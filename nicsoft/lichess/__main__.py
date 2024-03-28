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

# chess stuff
import chess.pgn
import chess
import berserk
from berserk.exceptions import *

# for the clock
import datetime

# NicLink shit
from niclink import NicLinkManager
from niclink.nl_exceptions import *

# parsing command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--tokenfile")
parser.add_argument("--correspondence", action="store_true")
parser.add_argument("--quiet", action="store_true")
parser.add_argument("--debug", action="store_true")
args = parser.parse_args()

### constants ###
# refresh refresh delay for NicLink and Lichess
REFRESH_DELAY = 0.5
# POLL_DELAY for checking for new games
POLL_DELAY = 20

correspondence = False
if args.correspondence:
    correspondence = True

DEBUG = False
#DEBUG = True
if args.debug:
    DEBUG = True

# the script dir, used to import the lila token file
script_dir = os.path.dirname(__file__)

### lichess token parsing ###
TOKEN_FILE = os.path.join(script_dir, "lichess_token/token")
if args.tokenfile is not None:
    TOKEN_FILE = args.tokenfile

if DEBUG:
    TOKEN_FILE = os.path.join(script_dir, "lichess_token/dev_token")

### logger stuff ###
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

# logging to a file
fileHandler = logging.FileHandler("NicLink.log")
fileHandler.setLevel(logging.DEBUG)

logger.addHandler(fileHandler)

### exception logging and except hook ###

# log unhandled exceptions to the log file
def log_except_hook(excType, excValue, traceback):
    global logger
    logger.error("Uncaught exception", exc_info=(excType, excValue, traceback))
# set exception hook
sys.excepthook = log_except_hook

def log_handled_exception(exception: Exception) -> None:
    """log a handled exception"""
    global logger
    logger.error("Exception handled: %s", exception)

### pre-amble fin ###


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
        
        # make sure the nl_inst is reset
        nl_inst.reset()

        # for await move to signal a move has been made
        self.has_moved = threading.Event()
        # berserk board_client
        self.berserk_board_client = client.board
        # id of the game we are playing
        self.game_id = game_id
        # incoming board stream
        self.stream = self.berserk_board_client.stream_game_state(game_id)

        # current state from stream
        self.current_state = next(self.stream)

        # cur_game_state is None, updated in run
        self.cur_game_state = None

        self.playing_white = playing_white
        if starting_fen and False: # TODO: make 960 work
            nl_inst.reset()
            self.game_board = chess.Board(starting_fen)
            nl_inst.set_game_board(self.game_board)
            self.starting_fen = starting_fen
        else:
            nl_inst.reset() # reset niclink for a new game
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
        state_change_thread = False

        for event in self.stream:
            # update current state
            logger.debug("event: %s", event)
            if event["type"] == "gameState":

                self.cur_game_state = event
                self.white_time = event["wtime"]
                self.black_time = event["btime"]
                logger.info("white time (seconds): %s\n", self.white_time.seconds)
                logger.info("black time (seconds): %s\n", self.black_time.seconds)
                # if there is another state change thread for some reason, join it
                if(state_change_thread and state_change_thread.is_alive()):
                    state_change_thread.join()
                state_change_thread = threading.Thread(target=self.handle_state_change, args=(event,))
                state_change_thread.start()

            elif event["type"] == "chatLine":
                self.handle_chat_line(event)
            elif event["type"] == "gameFull":
                logger.info("\n\n +++ Game Full got +++\n\n")
                self.game_done()
            else: # If it is not one of these options, kill the stream
                break

        self.game_done()

    def game_done(self) -> None:
        """stop the thread, game should be over, or maybe a rage quit"""
        global logger, nl_inst
        print("good game")
        logger.info("Game.game_done() entered")
        # tell the user and NicLink the game is through
        nl_inst.game_over.set()
        nl_inst.beep()
        nl_inst.gameover_lights()
        time.sleep(3)
        nl_inst.turn_off_all_leds()
        # stop the thread
        raise NicLinkGameOver("Game over")

    def await_move_thread(self, fetch_list: list) -> None:
        """await move in a way that does not stop the user from exiting and when move is found, 
        set it to index 0 on fetch_list in UCI. This function should be ran in in i it's own Thread."""
        global logger, nl_inst
        logger.info("\nGame.await_move_thread(...) entered\n")
        try:
            move = (
                nl_inst.await_move()
            )  # await move from e-board the move from niclink
            logger.info("await_move_thread(...): move from chessboard %s. setting it to index 0 of the passed list, and setting moved event", move)
            
            fetch_list.insert(0, move)
            self.has_moved.set() # set the Event

        except KeyboardInterrupt as err:
            log_handled_exception(err)
            print("KeyboardInterrupt: bye")
            sys.exit(0)
        except ResponseError as err:
            logger.info("\nResponseError on make_move(). This causes us to just return\n\n")
            log_handled_exception(err)
            raise NoMove("ResponseError in Game.await_move_thread thread.")
        else:
            logger.info("Game.await_move_thread(...) Thread got move: %s", move)
            raise SystemExit("exiting Game.await_move_thread thread, everything is good.")


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
                
                # check for game over or it is not your turn, If so, return
                if "Not your turn, or game already over" in str(err):
                    logger.error("Not your turn, or game is already over. Exiting make_move(...)")
                    return

                # if not, try again
                print(f"ResponseError: { err }trying again after three seconds")
                time.sleep(3)
                continue
            except IllegalMove as err:
                log_handled_exception(err)
                print("Illegal move")
                break
            else:
                break

    def make_first_move(self) -> None:
        """make the first move in a lichess game, before stream starts"""
        global nl_inst, logger
        logger.info("making the first move in the game")
        move = nl_inst.await_move()
        # hack
        while move is None:
            move = nl_inst.await_move()
        # make the move
        self.make_move(move)

    def get_move_from_chessboard(self, tmp_chessboard: chess.Board) -> str:
        """get a move from the chessboard, and return it in UCI"""
        global nl_inst, logger
        logger.info("get_move_from_chessboard() entered. Our turn to move.\n")
        
        # set this board as NicLink game board
        nl_inst.set_game_board(tmp_chessboard)

        logger.info(
            "NicLink set_game_board(tmp_chessboard) set. board prior to move FEN %s\n FEN I see external: %s\n",
            tmp_chessboard.fen(),
            nl_inst.get_FEN(),
        )
        # the move_fetch_list is for getting the move and await_move_thread in a thread is it does not block
        move_fetch_list = []
        get_move_thread = threading.Thread(target = self.await_move_thread, args=(move_fetch_list,), daemon=True)
        
        get_move_thread.start()
        # wait for a move on chessboard
        while not nl_inst.game_over.is_set():
            if self.has_moved.is_set():
                move = move_fetch_list[0]
                self.has_moved.clear()
                break

        return move

    def update_tmp_chessboard(self, move_list: list[str]) -> chess.Board:
        """create a tmp chessboard with the given move list played on it."""
        global nl_inst, logger
        # if there is a starting FEN, use it
        if self.starting_fen is not None: 
            tmp_chessboard = chess.Board(self.starting_fen)
        else:
            tmp_chessboard = chess.Board()
        
        if move_list != [""]:
            last_move = None
            for move in move_list:
                # make the moves on a board
                tmp_chessboard.push_uci(move)
                last_move = move

            # highlight last made move
            nl_inst.set_move_LEDs( last_move )
            logger.info("The last move was found to be: %s", last_move)

            # set the nl_inst.last move
            nl_inst.last_move = last_move


        return tmp_chessboard

    def handle_state_change(self, game_state) -> None:
        """Handle a state change in the lichess game."""
        global nl_inst, logger
        # {'type': 'gameState', 'moves': 'd2d3 e7e6 b1c3', 'wtime': datetime.datetime( 1970, 1, 25, 20, 31, 23, 647000, tzinfo=datetime.timezone.utc ), 'btime': datetime.datetime( 1970, 1, 25, 20, 31, 23, 647000, tzinfo=datetime.timezone.utc ), 'winc': datetime.datetime( 1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc ), 'binc': datetime.datetime( 1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc ), 'bdraw': False, 'wdraw': False}

        logger.info("\ngame_state: %s\n", game_state)
        
        logger.info("cur_game_state updated")
        self.cur_game_state = game_state
        # check if game has ended
        self.check_for_game_over(game_state)
        # update a tmp chessboard with the current state
        moves = game_state["moves"].split(" ")
        # update tmp chessboard
        tmp_chessboard = self.update_tmp_chessboard(moves)

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
            logger.info("game done detected, calling game_done(). winner: %s\n", winner)
            # stop the tread (this does some cleanup and throws an exception)
            self.game_done()

        # tmp_chessboard.turn == True when white, false when black playing_white is same
        if tmp_chessboard.turn == self.playing_white:
            # get our move from chessboard
            move = self.get_move_from_chessboard(tmp_chessboard)

            # make the move
            logger.info("calling self.make_move(%s)", move) 
            self.make_move(move)



    def handle_chat_line(self, chat_line) -> None:
        """handle when the other person types something in gamechat"""
        global nl_inst
        nl_inst.beep()
        print(chat_line)
        pass

    def check_for_game_over(self, game_state) -> None:
        """check a game state to see if the game is through if so raise an exception."""
        global logger, nl_inst

        logger.debug("check_for_game_over(self, game_state) entered w/ gamestate: %s", game_state)
        if game_state["status"] == "gameFull":
            logger.error("\n\ngameFull received !!!")
            while True: # be obnozios so I know
                nl_inst.beep()
                time.sleep(1)
            self.game_done()
        elif "winner" in game_state:   # confirmed worked once on their resign
            self.game_done()
        elif nl_inst.game_over.is_set():
            self.game_done()
        else:
            logger.info("game not found to be over.")

### helper functions ###
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
        game.daemon = True
        game.start()  # start the game thread

    except berserk.exceptions.ResponseError as e:
        if "This game cannot be played with the Board API" in str(e):
            print("cannot play this game via board api")
        log_handled_exception(e)

def handle_ongoing_game(game_data):
    """handle joining a game that is alredy underway"""

    print("\n+++ joining game in progress +++\n")
    print(f"Playing: { game_data['color'] }")

    if game_data["isMyTurn"]:
        print("it is your turn. make a move.")
    else:
        print("it is your opponents turn.")

def handle_resign(event = None) -> None:
    """handle ending the game in the case where you resign"""
    global nl_inst, logger, game
    if event is not None:
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
client = None  # the berserk client
nl_inst = None  # the NicLinkManager object
game = None # the active game, there can only be on, because on board

# entry point
def main():
    """handle startup, and initiation of stuff"""
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
    try:
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

                    # check for kill switch
                    if nl_inst.kill_switch.is_set():
                        sys.exit(0)


            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt: bye")
                try:
                    nl_inst.kill_switch.set()
                except Exception as err:
                    log_handled_exception(err)
                    # quit down quiett
                    # pass
                finally:
                    raise ExitNicLink("KeyboardInterrupt in __main__")
            except berserk.exceptions.ResponseError as e:
                print(f"ERROR: Invalid server response: {e}")
                logger.info("Invalid server response: %s", e)
                if "Too Many Requests for url" in str(e):
                    time.sleep(10)
                
            except NicLinkGameOver:
                logger.info("NicLinkGameOver excepted, good game?")
                print("game over, you can play another. Waiting for lichess event...")
                handle_resign()

            else:
                time.sleep(POLL_DELAY)
                logger.info("main loop: sleeping POLL_DELAY")

    except ExitNicLink:
        print("Have a nice life")
        sys.exit(0)

if __name__ == "__main__":
    main()
