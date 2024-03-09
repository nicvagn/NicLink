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
import traceback

# import shinanigans. I don't fully comprehend how python importing works, but this works
script_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(script_dir)

sys.path.append(parent_dir)

# chess stuff
import chess.pgn
import chess
import berserk

# for the clock
import datetime

# NicLink shit
from niclink import NicLinkManager
from niclink.nl_exceptions import *

parser = argparse.ArgumentParser()
parser.add_argument("--tokenfile")
parser.add_argument("--correspondence", action="store_true")
parser.add_argument("--quiet", action="store_true")
parser.add_argument("--debug", action="store_true")
args = parser.parse_args()

# refresh refresh delay for NicLink and Lichess
REFRESH_DELAY = 0.4

correspondence = False
if args.correspondence:
    correspondence = True

DEBUG = False
#DEBUG = True
if args.debug:
    DEBUG = True

TOKEN_FILE = os.path.join(script_dir, "lichess_token/token")
if args.tokenfile is not None:
    TOKEN_FILE = args.tokenfile

if DEBUG:
    TOKEN_FILE = os.path.join(script_dir, "lichess_token/dev_token")

logger = logging.getLogger("nl_lichess")

consoleHandler = logging.StreamHandler(sys.stdout)

if DEBUG:
    logger.info("DEBUG is set.")
    logger.setLevel(logging.DEBUG)
    consoleHandler.setLevel(logging.DEBUG)
else:
    logger.info("not DEBUG. DEBUG not set")
    # for dev
    logger.setLevel(logging.DEBUG)
    consoleHandler.setLevel(logging.DEBUG)
    # logger.setLevel(logging.ERROR) for production
    # consoleHandler.setLevel(logging.ERROR)

formatter = logging.Formatter("%(asctime)s %(levelname)s %(module)s %(message)s")

consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)

fileHandler = logging.FileHandler("NicLink.log")
fileHandler.setLevel(logging.DEBUG)

logger.addHandler(fileHandler)

# log unhandled exceptions to the log file
def log_excepthook(excType, excValue, traceback):
    global logger
    logger.error("Uncaught exception", exc_info=(excType, excValue, traceback))

sys.excepthook = log_excepthook

def log_handled_exception(exception: Exception) -> None:
    """log a handled exception"""
    logger.error("Exception handled: %s", exception)


print(
    "\n\n==========================\nNicLink on Lichess startup\n==========================\n\n"
)
logger.info("=== NicLink Lichess startup ===\n")

class Game(threading.Thread):
    """a game on lichess"""

    def __init__(self, game_id, playing_white, starting_fen=False, **kwargs):
        """Game, the client.board, niclink instance, the game id on lila, idk fam"""
        global client, nl_inst, logger
        super().__init__(**kwargs)
        # berserk board_client
        self.berserk_board_client = client.board
        # id of the game we are playing
        self.game_id = game_id
        # incoming board stream
        self.stream = self.berserk_board_client.stream_game_state(game_id)

        # current state from stream
        self.current_state = next(self.stream)

        self.playing_white = playing_white
        if starting_fen and False:  # TODO fix starting fen (for use w chess960)
            self.game_board = chess.Board(starting_fen)
            nl_inst.set_game_board(self.game_board)
            self.starting_fen = starting_fen
        else:
            self.game_board = chess.Board()
            nl_inst.set_game_board(self.game_board)
            self.starting_fen = None

        logger.info("game init w id: %s", game_id)
        logger.info(client.games.get_ongoing())

        # if white, make the first move
        if self.playing_white and self.current_state["state"]["moves"] == "":
            self.make_first_move()
        # if we are joining a game in progress or move second
        else:
            self.handle_state_change(self.current_state["state"])

    def run(self) -> None:
        """run the thread until game is through, ie: while the game stream is open then kill it w self.game_done()"""
        global nl_inst, logger

        for event in self.stream:
            logger.debug("event: %s", event)
            if event["type"] == "gameState":
                self.white_time = self.current_state["state"]["wtime"]
                self.black_time = self.current_state["state"]["btime"]
                logger.info("\n*** time remaining(in seconds): [B] - %s [W] - %s***\n", self.white_time, self.black_time)
                self.handle_state_change(event)
            elif event["type"] == "chatLine":
                self.handle_chat_line(event)
            elif event["type"] == "gameFull":
                logger.info("\n\n +++ Game Full got +++\n\n")
                self.game_done()
            else:
                break

        # when the stream ends, the game is over
        self.game_done() 

    def game_done(self):
        """stop the thread, game should be over, or maybe a rage quit"""
        global logger, nl_inst
        print("good game")
        logger.info("Game.game_done() entered")
        # tell the user and NicLink the game is through
        nl_inst.beep()
        nl_inst.gameover_lights()
        nl_inst.game_over.set()
        time.sleep(3)
        nl_inst.turn_off_all_leds()
        # stop the thread
        raise NicLinkGameOver("Game over")

    def make_move(self, move) -> None:
        """make a move in a lichess game"""
        global logger, nl_inst
        logger.info("move made: %s", move)

        while not nl_inst.game_over.is_set():
            logger.info("make_move() attempt w move: %s nl_inst.game_over.is_set(): %s", move, str(nl_inst.game_over.is_set()))
            try:
                if move is None:
                    raise IllegalMove("Move is None")
                self.berserk_board_client.make_move(self.game_id, move)
            except berserk.exceptions.ResponseError as err:
                log_handled_exception(err)
                print(f"ResponseError: { err }trying again after three seconds")
                time.sleep(3)
                continue
            except IllegalMove as err:
                log_handled_exception(err)
                print("Illegal move")
                break
            else:
                break
    def make_first_move(self):
        """make the first move in a lichess game, before stream starts"""
        global nl_inst, logger
        logger.info("making the first move in the game")
        move = nl_inst.await_move()
        # hack
        while move is None:
            move = nl_inst.await_move()
        # make the move
        self.make_move(move)

    def handle_state_change(self, game_state) -> None:
        """Handle a state change in the lichess game."""
        global nl_inst, logger
        # {'type': 'gameState', 'moves': 'd2d3 e7e6 b1c3', 'wtime': datetime.datetime( 1970, 1, 25, 20, 31, 23, 647000, tzinfo=datetime.timezone.utc ), 'btime': datetime.datetime( 1970, 1, 25, 20, 31, 23, 647000, tzinfo=datetime.timezone.utc ), 'winc': datetime.datetime( 1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc ), 'binc': datetime.datetime( 1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc ), 'bdraw': False, 'wdraw': False}

        logger.info("game_state: %s", game_state)

        if self.check_for_game_over(self.current_state["state"]):
            self.game_over()

        # tmp_chessboard is used to get the current game state from API and parse it into something we can use
        if self.starting_fen:
            # allows for different starting position
            tmp_chessboard = chess.Board(self.starting_fen)
        else:
            tmp_chessboard = chess.Board()

        moves = game_state["moves"].split(" ")
        # last move is to highlight last move on board
        last_move = None
        if moves != [""]:
            for move in moves:
                # make the moves on a board
                tmp_chessboard.push_uci(move)
                last_move = move

            # highlight last made move
            nl_inst.set_move_LEDs( last_move )

        # check for game over
        result = tmp_chessboard.outcome()
        if result is not None:
            # set the winner var
            if result.winner is None:
                winner = "no winner"
            elif result.winner:
                winner = "White"
            else:
                winner = "Black"

            print(
                f"\n--- GAME OVER ---\nreason: {result.termination}\nwinner: {winner}"
            )
            logger.info("game done detected, calling game_done()")
            # stop the tread (this does some cleanup and throws an exception)
            self.game_done()

        # set this board as NicLink game board
        nl_inst.set_game_board(tmp_chessboard)

        # tmp_chessboard.turn == True when white, false when black playing_white is same
        if tmp_chessboard.turn == self.playing_white:
            logger.info("it is our turn")

            logger.info(
                "board prior to move FEN %s\n FEN I see external: %s\n",
                tmp_chessboard.fen(),
                nl_inst.get_FEN(),
            )
            try:
                for attempt in range(3):
                    move = (
                        nl_inst.await_move()
                    )  # await move from e-board the move from niclink
                    logger.info("move from chessboard %s", move)

                    # make the move
                    self.make_move(move)
                    break

            except KeyboardInterrupt as err:
                log_handled_exception(err)
                print("KeyboardInterrupt: bye")
                raise NicLinkGameOver("Game exited via a KeyboardInterrupt")
                sys.exit(0)

                #except:
                #    e = sys.exc_info()[0]
                #    logger.info("!!! exception on make_move: !!!\nRecord what it is, and try to replace the arbitrary except")
                #    traceback.print_exc()
            finally:
                if attempt > 1:
                    logger.debug("sleeping before retry")
                    time.sleep(3)

    def handle_chat_line(self, chat_line) -> None:
        """handle when the other person types something in gamechat"""
        nl_inst.beep()
        print(chat_line)
        pass

    def check_for_game_over(self, game_state) -> bool:
        """check a game state to see if the game is through if so raise an exception. If not return True"""
        global logger

        logger.info(game_state)
        print(game_state)

        if game_state["status"] == "gameFull":
            breakpoint()
            self.game_done()
        if "winner" in game_state:
            breakpoint()
            self.game_done()
        return False


def show_FEN_on_board(FEN) -> None:
    """show board FEN on an ascii chessboard"""
    tmp_chessboard = chess.Board()
    tmp_chessboard.set_fen(FEN)
    print(tmp_chessboard)


def handle_game_start(event) -> None:
    """handle game start event"""
    global client, logger, game
    game_data = event["game"]

    # check if game speed is correspondence, skip those if --correspondence argument is not set
    if not correspondence:
        if is_correspondence(game_data["id"]):
            logger.info("skipping correspondence game w/ id: %s", game_data["id"])
            return

    playing_white = game_data["color"] == "white"

    logger.info("\ngame start received: \nyou play: %s", game_data["color"])

    game_fen = game_data["fen"]
    print(
        f"game start:\ngame board: \n{ chess.Board(game_fen) }\nyour turn?: { game_data['isMyTurn'] }\n"
    )

    if game_data["hasMoved"]:
        """handle ongoing game"""
        handle_ongoing_game(game_data)

    try:
        game = Game(
            game_data["id"], playing_white, starting_fen=game_fen
        )  # ( game_data['color'] == "white" ) is used to set is_white bool
        game.start()  # start the game thread

    except berserk.exceptions.ResponseError as e:
        if "This game cannot be played with the Board API" in str(e):
            print("cannot play this game via board api")
        log_handled_exception(e)
    except KeyboardInterrupt:
        print("bye")
        nl_inst.game_over()
        logger.info("KeyboardInterrupt. halting")
        sys.exit(0)


def handle_ongoing_game(game_data):
    """handle joining a game that is alredy underway"""

    print("\n+++ joining game in progress +++\n")
    print(f"Playing: { game_data['color'] }")

    if game_data["isMyTurn"]:
        print("it is your turn. make a move.")
    else:
        print("it is your opponents turn.")


def handle_resign(event) -> None:
    """handle ending the game in the case where you resign"""
    global nl_inst, logger, game
    logger.info("handle_resign entered: event: %", event)
    # end the game
    game.game_done()


def is_correspondence(gameId) -> bool:
    """is the game a correspondence game?"""
    global client, logger
    try:
        for game in client.games.get_ongoing():
            if game["gameId"] == gameId:
                if game["speed"] == "correspondence":
                    return True
    except KeyboardInterrupt as err:
        log_handled_exception(err)
        print("KeyboardInterrupt: bye")
        sys.exit(0)
    except:
        e = sys.exc_info()[0]
        print(f"cannot determine game speed: {e}")
        logger.info("cannot determine if game is correspondence: ", e)
        log_handled_exception(e)
        return False
    return False


# globals, because why not
client = None
nl_inst = None
game = None


def main():
    global client, nl_inst, REFRESH_DELAY, logger

    print("=== NicLink lichess main entered ===")
    simplejson_spec = importlib.util.find_spec("simplejson")
    if simplejson_spec is not None:
        print(
            f"ERROR: simplejson is installed. The berserk lichess client will not work with simplejson. Please remove the module. Aborting."
        )
        sys.exit(-1)

    # init NicLink
    try:
        nl_inst = NicLinkManager(refresh_delay=REFRESH_DELAY, logger=logger)
        nl_inst.start()

    except ExitNicLink:
        logger.info("ExitNicLink exception caught in main()")
        print("Thank's for using NicLink")
        sys.exit(0)

    except Exception as err:
        log_handled_exception(err)
        print(f"error: { traceback.format_exc() } on NicLink connection.")
        sys.exit(-1)

    try:
        logger.info("reading token from %s", TOKEN_FILE)
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
        log_handled_exception(e)
        print(f"cannot create session: {e}")
        logger.info("cannot create session", e)
        sys.exit(-1)
 
    try:
        if DEBUG:
            client = berserk.Client(session, base_url="https://lichess.dev")
        else:
            client = berserk.Client(session)
    except KeyboardInterrupt as err:
        log_handled_exception(err)
        print("KeyboardInterrupt: bye")
        sys.exit(0)
    except:
        e = sys.exc_info()[0]
        logger.info("cannot create lichess client: %s", e)
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
        logger.info("cannot get lichess acount info: %s", e)
        print(f"cannot get lichess acount info: {e}")
        sys.exit(-1)

    # main program loop
    while True:
        try:
            logger.debug("\n==== event loop ====\n")
            print("=== Waiting for lichess event ===")
            for event in client.board.stream_incoming_events():
                if event["type"] == "challenge":
                    logger.info("challenge received: %s", event)
                    print("\n==== Challenge received ====\n")
                    print(event)
                elif event["type"] == "gameStart":
                    # a game is starting, it is handled by a function
                    handle_game_start(event)
                elif event["type"] == "gameFull":
                    nl_inst.game_over.set()
                    handle_resign(event)
                    print("GAME FULL received")
                    logger.info("\ngameFull received\n")
                time.sleep(REFRESH_DELAY)

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt: bye")
            try:
                nl_inst.kill_switch.set()
            except:
                # quit down quiett
                pass
            raise ExitNicLink("editing b/c of keyboard intrupt") 
        except berserk.exceptions.ResponseError as e:
            print(f"ERROR: Invalid server response: {e}")
            logger.info("Invalid server response: %s", e)
            if "Too Many Requests for url" in str(e):
                time.sleep(10)
        except NicLinkGameOver:
            logger.info("NicLinkGameOver excepted, good game?")
            print("game over, you can play another. Waiting for lichess event...")

        finally:
            time.sleep(REFRESH_DELAY)
            logger.info("main loop: sleeping REFRESH_DELAY")

            continue


if __name__ == "__main__":
    main()
