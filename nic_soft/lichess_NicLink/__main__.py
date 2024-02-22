#  NicLink-lichess is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink-lichess is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

# sys stuff
import sys
import time
import logging
import logging.handlers
import os
import sys
import argparse
import threading
import importlib

# chess stuff
import chess.pgn
import chess
import berserk

# NicLink shit
from niclink import NicLinkManager

parser = argparse.ArgumentParser()
parser.add_argument("--tokenfile")
parser.add_argument("--correspondence", action="store_true")
parser.add_argument("--quiet", action="store_true")
parser.add_argument("--debug", action="store_true")
args = parser.parse_args()

# refresh refresh delay for NicLink and Lichess 
REFRESH_DELAY = 2

correspondence = False
if args.correspondence:
    correspondence = True

#DEBUG = True
DEBUG = False
if args.debug:
    DEBUG = True

TOKEN_FILE = os.path.join(os.path.dirname(__file__), "lichess_token/token")
if args.tokenfile is not None:
    TOKEN_FILE = args.tokenfile

if DEBUG:
    TOKEN_FILE = os.path.join(os.path.dirname(__file__), "lichess_token/dev_token")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(module)s %(message)s")

if not args.quiet:
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)


# log unhandled exceptions to the log file
def my_excepthook(excType, excValue, traceback, logger=logger):
    logger.error("Uncaught exception", exc_info=(excType, excValue, traceback))


sys.excepthook = my_excepthook

print(
    "\n\n========================== \n NicLink_lichess startup\n==========================\n\n"
)


class Game(threading.Thread):
    """a game on lichess"""

    def __init__(self, game_id, playing_white, **kwargs):
        """Game, the client.board, niclink instance, the game id on lila, idk fam"""
        global client, nl_inst
        super().__init__(**kwargs)
        # berserk board_client
        self.berserk_board_client = client.board
        # id of the game we are playing
        self.game_id = game_id
        # incoming board stream
        self.stream = self.berserk_board_client.stream_game_state(game_id)

        # current state from stream
        self.current_state = next(self.stream)

        self.stop_event = threading.Event()

        # stuff about cur game
        self.playing_white = playing_white
        self.game_board = chess.Board()

        logger.info(f"game init w id: { game_id }")
        logger.info(client.games.get_ongoing())

    def run(self) -> None:
        for event in self.stream:
            if not self.stop_event.is_set():
                if event["type"] == "gameState":
                    self.handle_state_change(event)
                elif event["type"] == "chatLine":
                    self.handle_chat_line(event)
            else:
                break
        
        print("good game")
        breakpoint()

    def make_move(self, move) -> None:
        """make a move in a lichess game"""
        logger.info(f"move made: { move }")
        self.berserk_board_client.make_move(self.game_id, move)

    def handle_state_change(self, game_state) -> None:
        """Handle a state change in the lichess game."""
        global nl_inst
        # {'type': 'gameState', 'moves': 'd2d3 e7e6 b1c3', 'wtime': datetime.datetime( 1970, 1, 25, 20, 31, 23, 647000, tzinfo=datetime.timezone.utc ), 'btime': datetime.datetime( 1970, 1, 25, 20, 31, 23, 647000, tzinfo=datetime.timezone.utc ), 'winc': datetime.datetime( 1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc ), 'binc': datetime.datetime( 1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc ), 'bdraw': False, 'wdraw': False}

        # logger.info(game_state)

        # tmp_chessboard is used to get the current game state from API and parse it into something we can use
        tmp_chessboard = chess.Board()
        moves = game_state["moves"].split(" ")
        last_move = None
        for move in moves:
            # make the moves on a board
            tmp_chessboard.push_uci(move)
            last_move = move

        # check for game over
        result = tmp_chessboard.outcome()
        if result is not None:
            nl_inst.beep()

            # set the winner var
            if result.winner is None:
                winner = "no winner"
            elif result.winner:
                winner = "White"
            else:
                winner = "Black"

            self.stop_event.set() # set event to stop thread
            print( f"\n--- GAME OVER ---\nreason: {result.termination}\nwinner: {winner}")
            # stop the tread
            raise Exception("Game over") 


        # set this board as NicLink game board
        nl_inst.set_game_board(tmp_chessboard)

        # tmp_chessboard.turn == True when white, false when black playing_white is same
        if tmp_chessboard.turn == self.playing_white:
            logger.info("it is our turn")

            nl_FEN = nl_inst.get_FEN()
            nl_board = tmp_chessboard.copy()
            nl_board.set_board_fen(nl_FEN)
            print( f"NicLinked board prior to move\n{nl_board}")

            try:
                for attempt in range(3):
                    move = nl_inst.await_move()  # await move from e-board the move from niclink
                    logger.info(f"move from chessboard { move }")

                    # make the move
                    self.make_move(move)
                    break

            except KeyboardInterrupt:
                print("KeyboardInterrupt: bye")
                sys.exit(0)
            except:
                e = sys.exc_info()[0]
                logger.info(f"exception on make_move: {e}")
            finally:
                if attempt > 1:
                    logger.debug(f"sleeping before retry")
                    time.sleep(3)

    def handle_chat_line(self, chat_line) -> None:
        nl_inst.beep()
        print(chat_line)
        pass


def show_FEN_on_board(FEN) -> None:
    """show board FEN on an ascii chessboard"""
    tmp_chessboard = chess.Board()
    tmp_chessboard.set_fen(FEN)
    print(tmp_chessboard)


def handle_game_start(event) -> None:
    """handle game start event"""
    global client
    game_data = event["game"]

    playing_white = game_data["color"] == "white"

    logger.info(
        f"\ngame start received: { game_data['id']}\nyou play: { game_data['color'] }"
    )

    print(
        f"\ngame board: { show_FEN_on_board(game_data['fen']) }\nyour turn?: { game_data['isMyTurn'] }\n"
    )

    # check if game speed is correspondence, skip those if --correspondence argument is not set
    if not correspondence:
        if is_correspondence(game_data["id"]):
            logger.info(f"skipping correspondence game: {game_data['id']}")
            return
    if game_data["hasMoved"]:
        """handle ongoing game"""
        handle_ongoing_game(game_data)

    try:
        game = Game(
            game_data["id"], playing_white
        )  # ( game_data['color'] == "white" ) is used to set is_white bool
        game.daemon = True
        game.start()  # start the game thread

    except berserk.exceptions.ResponseError as e:
        if "This game cannot be played with the Board API" in str(e):
            print("cannot play this game via board api")
        logger.info(f"ERROR: {e}")
        return
    except KeyboardInterrupt:
        print("KeyboardInterrupt: bye")
        sys.exit(0)


def handle_ongoing_game(game_data):
    """handle joining a game that is alredy underway"""

    print("\n+++ joining game in progress +++\n")
    print(f"Playing: { game_data['color'] }")

    if game_data["isMyTurn"]:
        print("it is your turn. make a move.")
    else:
        print("it is your opponents turn.")


def is_correspondence(gameId) -> bool:
    """is the game a correspondence game?"""
    global client
    try:
        for game in client.games.get_ongoing():
            if game["gameId"] == gameId:
                if game["speed"] == "correspondence":
                    return True
    except KeyboardInterrupt:
        print("KeyboardInterrupt: bye")
        sys.exit(0)
    except:
        e = sys.exc_info()[0]
        print(f"cannot determine game speed: {e}")
        logger.info(f"cannot determine if game is correspondence: {e}")
        return False
    return False


# globals, because why not
client = None
nl_inst = None


def main():
    global client, nl_inst, REFRESH_DELAY

    print("=== NicLink lichess main entered ===")
    simplejson_spec = importlib.util.find_spec("simplejson")
    if simplejson_spec is not None:
        print(
            f"ERROR: simplejson is installed. The berserk lichess client will not work with simplejson. Please remove the module. Aborting."
        )
        sys.exit(-1)

    # init NicLink
    try:
        nl_inst = NicLinkManager(refresh_delay=REFRESH_DELAY)
    except:
        e = sys.exc_info()[0]
        print( f"error: { e } on NicLink connection. Exiting")
        sys.exit(-1)

    try:
        logger.info(f"reading token from {TOKEN_FILE}")
        with open(TOKEN_FILE) as f:
            token = f.read().strip()
    
    except FileNotFoundError:
        print(f"ERROR: cannot find token file")
        sys.exit(-1)
    except PermissionError:
        print(f"ERROR: permission denied on token file")
        sys.exit(-1)
    try:
        session = berserk.TokenSession(token)
    except:
        e = sys.exc_info()[0]
        print(f"cannot create session: {e}")
        logger.info(f"cannot create session {e}")
        sys.exit(-1)

    try:
        if DEBUG:
            client = berserk.Client(session, base_url="https://lichess.dev")

        else:
            client = berserk.Client(session)
    except KeyboardInterrupt:
        print("KeyboardInterrupt: bye")
        sys.exit(0)
    except:
        e = sys.exc_info()[0]
        logger.info(f"cannot create lichess client: {e}")
        print(f"cannot create lichess client: {e}")
        sys.exit(-1)

    # get username
    try:
        account_info = client.account.get()
        username = account_info["username"]
        print(f"\nUSERNAME: { username }\n")
    except KeyboardInterrupt:
        print("KeyboardInterrupt: bye")
        sys.exit(0)
    except:
        e = sys.exc_info()[0]
        logger.info(f"cannot get lichess acount info: {e}")
        print(f"cannot get lichess acount info: {e}")
        sys.exit(-1)

    # main program loop
    while True:
        try:
            logger.debug(f"\n==== event loop ====\n")
            for event in client.board.stream_incoming_events():
                if event["type"] == "challenge":
                    print("\n==== Challenge received ====\n")
                    print(event)
                elif event["type"] == "gameStart":
                    # a game is starting, it is handled by a function
                    print("\n\n\n GAME START \n\n\n")
                    handle_game_start(event)

        except KeyboardInterrupt:
            print("KeyboardInterrupt: bye")
            sys.exit(0)
        except berserk.exceptions.ResponseError as e:
            print(f"ERROR: Invalid server response: {e}")
            logger.info("Invalid server response: {e}")
            if "Too Many Requests for url" in str(e):
                time.sleep(10)

        finally:
            time.sleep(REFRESH_DELAY)


if __name__ == "__main__":
    main()
