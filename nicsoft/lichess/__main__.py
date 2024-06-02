# NicLink-lichess is a part of NicLink
#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

import argparse
import importlib.util
import logging
import logging.handlers
import os

# sys stuff
import sys
import threading
import traceback
from time import sleep

import berserk

# chess stuff
import chess
import chess.pgn
from berserk.exceptions import ResponseError

# external chess clock functionality
from chess_clock import ChessClock
from game import Game as LichessGame  # game is already a class
from game_start import GameStart

# other Nic modules
from game_state import GameState, timedelta

# exceptions
from serial import SerialException

# NicLink shit
from niclink import NicLinkManager
from niclink.nl_exceptions import *

### command line ###
# parsing command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--tokenfile")
parser.add_argument("--correspondence", action="store_true")
parser.add_argument("--clock", action="store_true")  # TODO: MAKE WORK
parser.add_argument("--quiet", action="store_true")
parser.add_argument("--debug", action="store_true")
args = parser.parse_args()

### globals ###
global game
global logger
game = None

correspondence = False
if args.correspondence:
    correspondence = True

# the script dir, used to import the lila token file
script_dir = os.path.dirname(__file__)

DEBUG = False
# DEBUG = True
if args.debug:
    DEBUG = True

if args.clock:
    CHESS_CLOCK = True
else:
    CHESS_CLOCK = False

# TODO: RM
CHESS_CLOCK = True
### constants ###
# refresh refresh delay for NicLink and Lichess
REFRESH_DELAY = 0.1
# POLL_DELAY for checking for new games
POLL_DELAY = 10

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
    logger.info("DEBUG not set")
    # for dev
    logger.setLevel(logging.INFO)
    consoleHandler.setLevel(logging.INFO)
    # logger.setLevel(logging.ERROR) for production
    # consoleHandler.setLevel(logging.ERROR)

formatter = logging.Formatter("%(levelno)s %(funcName)s %(message)s @: %(pathname)s")

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


# for good mesure, also log handled exceptions
def log_handled_exception(exception) -> None:
    """log a handled exception"""
    global logger
    logger.error("Exception handled: %s", exception)


### pre-amble fin ###

print(
    "\n\n|=====================| NicLink on Lichess startup |=====================|\n\n"
)
logger.info("NicLink Lichess startup\n")


class Game(threading.Thread):
    """a game on lichess"""

    def __init__(
        self,
        berserk_client,
        game_id,
        playing_white,
        bluetooth=False,
        starting_fen=False,
        chess_clock=CHESS_CLOCK,
        **kwargs,
    ):
        """Game, the client.board, niclink instance, the game id on lila, idk fam"""
        global nl_inst, logger
        super().__init__(**kwargs)

        # for await move to signal a move has been made
        self.has_moved = threading.Event()
        # berserk board_client
        self.berserk_board_client = berserk_client.board
        # id of the game we are playing
        self.game_id = game_id
        # incoming board stream
        self.stream = self.berserk_board_client.stream_game_state(game_id)
        # current state from stream
        self.current_state = next(self.stream)

        self.response_error_on_last_attempt = False

        # the most reasontly parsed game_state, in a GameState class wrapper
        self.game_state = GameState(self.current_state["state"])
        ### niclink options
        self.bluetooth = bluetooth
        ### external clock constants ###
        SERIAL_PORT = "/dev/ttyACM0"
        BAUDRATE = 115200
        TIMEOUT = 100.0
        """if there is an external_clock try to connect to the clock, 
        but do not fail if you dont
        """
        if chess_clock:
            try:
                self.chess_clock = ChessClock(
                    SERIAL_PORT,
                    BAUDRATE,
                    TIMEOUT,
                    logger=logger,
                )
            except SerialException as ex:
                logger.error("Chess clock could not be connected %s" % ex)
                self.chess_clock = False
        else:
            self.chess_clock = False

        self.playing_white = playing_white
        if starting_fen and False:  # HACK: make 960 work
            nl_inst.reset()
            self.game_board = chess.Board(starting_fen)
            nl_inst.set_game_board(self.game_board)
            self.starting_fen = starting_fen
        else:
            nl_inst.reset()  # reset niclink for a new game
            self.game_board = chess.Board()
            nl_inst.set_game_board(self.game_board)
            self.starting_fen = None

        logger.info("game init w id: %s", game_id)

        # if white, make the first move
        if self.playing_white and self.current_state["state"]["moves"] == "":
            self.make_first_move()
        # if we are joining a game in progress or move second
        else:
            self.handle_state_change(GameState(self.current_state["state"]))

    def run(self) -> None:
        """run the thread until game is through, ie: while the game stream is open
        then kill it w self.game_done()
        """
        global nl_inst, logger
        state_change_thread = None

        for event in self.stream:
            logger.debug("event in self.stream: %s", event)
            if event["type"] == "gameState":

                # update the game state in this class with a stream game_state
                # incapsulated in a conviniance class
                self.game_state = GameState(event)

                logger.debug("state_change_thread is: %s", state_change_thread)
                # if there is a state_change_thread
                if state_change_thread is not None:

                    # if there is another state change thread still
                    # running running, join it
                    # while checking for game over
                    while state_change_thread.is_alive():
                        if state_change_thread.is_alive():
                            # check that the game is not over.
                            # Will call game_done if so.
                            self.check_for_game_over(self.game_state)
                            # try to join state_change_thread with a one second time_out
                            state_change_thread.join(timeout=REFRESH_DELAY)

                # start new state change thread
                state_change_thread = threading.Thread(
                    target=self.handle_state_change, args=(self.game_state,)
                )
                state_change_thread.start()

            elif event["type"] == "chatLine":
                self.handle_chat_line(event)

            elif event["type"] == "gameFull":
                logger.info("\n\n +++ Game Full got +++\n\n")
                self.game_done()
            elif event["type"] == "opponentGone":
                logger.info(">>> opponentGone <<< recived event: %s \n", event)
                print(">>> opponentGone <<<")
                for x in range(0, 2):
                    nl_inst.signal_lights(3)
                    for x in range(0, 2):
                        nl_inst.beep()
                        sleep(0.2)
                    nl_inst.signal_lights(2)
                    sleep(1)
            else:  # If it is not one of these options, kill the stream
                logger.warning("\n\nNew Event: %s", event)
                for x in range(0, 3):
                    nl_inst.beep()
                    sleep(0.5)

                break

        self.game_done()

    def get_game_state(self) -> GameState:
        """get the current game_state"""
        return self.game_state

    def game_done(self, game_state: GameState = None) -> None:
        """stop the thread, game should be over, or maybe a rage quit
        @param - (GameState) a gamestate telling us how the game ended
        @side-effect - changes the external board led's

        info on signals:
         1 - ring of lights
         2 - left half lit up
         3 - right half lit up
         4 - central line
         5 - cross in center
        """
        global logger, nl_inst
        logger.info("\nGame.game_done(GameState) entered.\n GameState %s", game_state)
        # signal the side that won on the board by lighting up that side
        # if there is an external clock, display gameover message
        if game_state is not None:
            if game_state.winner:
                if game_state.winner == "white":
                    if self.chess_clock:
                        self.chess_clock.white_won()
                    nl_inst.signal_lights(2)
                elif game_state.winner == "black":
                    if self.chess_clock:
                        self.chess_clock.black_won()
                    nl_inst.signal_lights(3)
                else:
                    # if no winner
                    self.chess_clock.game_over()
                    nl_inst.signal_lights(4)
        else:
            # if no game state was given
            if self.chess_clock:
                self.chess_clock.game_over()
            # signal we dont know wtf with a cross
            self.signal_lights(5)

        print("\n[--- %%%%% GAME DONE %%%%% ---]\n")
        # tell the user and NicLink the game is through
        nl_inst.game_over.set()
        nl_inst.beep()
        nl_inst.gameover_lights()
        sleep(3)
        nl_inst.turn_off_all_LEDs()
        # stop the thread
        raise NicLinkGameOver("Game over")

    def await_move_thread(self, fetch_list: list) -> None:
        """await move in a way that does not stop the user from exiting. and when move is found,
        set it to index 0 on fetch_list in UCI. This function should be ran in it's own Thread.
        """
        global logger, nl_inst
        logger.debug("\nGame.await_move_thread(...) entered\n")
        try:
            move = nl_inst.await_move()  # await move from e-board the move from niclink
            logger.debug(
                "await_move_thread(...): move from chessboard %s. setting it to index 0 of the passed list, \
and setting moved event",
                move,
            )

            fetch_list.insert(0, move)
            self.has_moved.set()  # set the Event

        except KeyboardInterrupt as err:
            log_handled_exception(err)
            print("KeyboardInterrupt: bye")
            sys.exit(0)
        except ResponseError as err:
            logger.info(
                "\nResponseError on make_move(). This causes us to just return\n\n"
            )
            log_handled_exception(err)
            raise NoMove("ResponseError in Game.await_move_thread thread.")
        else:
            logger.info("Game.await_move_thread(...) Thread got move: %s", move)
            raise SystemExit(
                "exiting Game.await_move_thread thread, everything is good."
            )

    def make_move(self, move: str) -> None:
        """make a move in a lichess game with self.gameId
        @param - move: UCI move string ie: e4e5
        @side_effect: talkes to lichess, sending the move
        """
        global logger, nl_inst
        logger.info("move made: %s", move)

        while not nl_inst.game_over.is_set():
            logger.debug(
                "make_move() attempt w move: %s nl_inst.game_over.is_set(): %s",
                move,
                str(nl_inst.game_over.is_set()),
            )
            try:
                if move is None:
                    raise IllegalMove("Move is None")
                self.berserk_board_client.make_move(self.game_id, move)
                nl_inst.make_move_game_board(move)
                logger.debug("move sent to liches: %s", move)

                # once move has been made set self.response_error_on_last_attempt to false and return
                self.response_error_on_last_attempt = False

                # exit function on success
                return
            except ResponseError as err:
                log_handled_exception(err)

                # check for game over or it is not your turn, If so, return
                if "Not your turn, or game already over" in str(err):
                    logger.error(
                        "Not your turn, or game is already over. Exiting make_move(...)"
                    )
                    break

                # if not, try again
                print(
                    f"ResponseError: { err }trying again after three seconds.  \
Will only try twice before calling game_done"
                )
                sleep(3)

                if self.response_error_on_last_attempt == True:
                    self.response_error_on_last_attempt = False
                    self.game_done()
                else:
                    self.response_error_on_last_attempt = True
                continue
            except IllegalMove as err:
                log_handled_exception(err)
                print("Illegal move")
                break

    def make_first_move(self) -> None:
        """make the first move in a lichess game, before stream starts"""
        global nl_inst, logger, REFRESH_DELAY
        logger.info("making the first move in the game")
        move = nl_inst.await_move()
        # HACK:
        while move is None:
            move = nl_inst.await_move()
            sleep(REFRESH_DELAY)
        # make the move
        self.make_move(move)

    def get_move_from_chessboard(self, tmp_chessboard: chess.Board) -> str:
        """get a move from the chessboard, and return it in UCI"""
        global nl_inst, logger, REFRESH_DELAY
        logger.debug(
            "get_move_from_chessboard() entered. Geting move from ext board.\n"
        )

        # set this board as NicLink game board
        nl_inst.set_game_board(tmp_chessboard)

        logger.debug(
            "NicLink set_game_board(tmp_chessboard) set. board prior to move FEN %s\n FEN I see external: %s\n",
            tmp_chessboard.fen(),
            nl_inst.get_FEN(),
        )
        # the move_fetch_list is for getting the move and await_move_thread in a thread is it does not block
        move_fetch_list = []
        get_move_thread = threading.Thread(
            target=self.await_move_thread, args=(move_fetch_list,), daemon=True
        )

        get_move_thread.start()
        # wait for a move on chessboard
        while not nl_inst.game_over.is_set() or self.check_for_game_over(
            GameState(self.current_state["state"])  # TODO: FIND MORE EFFICIENT WAY
        ):
            if self.has_moved.is_set():
                move = move_fetch_list[0]
                self.has_moved.clear()
                return move
            sleep(REFRESH_DELAY)
        raise NoMove("No move in get_move_from_chessboard(...)")

    def update_tmp_chessboard(self, move_list: list[str]) -> chess.Board:
        """create a tmp chessboard with the given move list played on it."""
        global nl_inst, logger
        # if there is a starting FEN, use it
        if self.starting_fen is not None:
            tmp_chessboard = chess.Board(self.starting_fen)
        else:
            tmp_chessboard = chess.Board()

        # if the move list is not empty
        if move_list != [""]:
            for move in move_list:
                # make the moves on a board
                tmp_chessboard.push_uci(move)

        return tmp_chessboard

    def opponent_moved(self, game_state: GameState) -> None:
        """signal that the opponent moved, signal the external clock and NicLink"""
        logger.info(
            "\nopponent_moved(self, game_state) entered with GameState: %s",
            game_state,
        )

        # check to make sure the game state has moves befor trying to access them
        if game_state.has_moves():
            move = game_state.get_last_move()
            # tell nl about the move
            nl_inst.opponent_moved(move)
            # tell the user about the move
            nl_inst.beep()
            logger.info("opponent moved: %s", move)

        # if chess_clock send new timestamp to clock
        if self.chess_clock:
            if not game_state.first_move():
                logger.info("\n\nGameState sent to ChessClock: %s \n", game_state)
                self.chess_clock.move_made(game_state)

    def handle_state_change(self, game_state: GameState) -> None:
        """Handle a state change in the lichess game."""
        global nl_inst, logger

        logger.debug("\ngame_state: %s\n", game_state)

        # get all the moves of the game
        moves = game_state.get_moves()
        # update a tmp chessboard with the current state
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
            logger.info(
                "game done detected, calling game_done(). | result: %s | winner: %s\n",
                result,
                winner,
            )
            # stop the tread (this does some cleanup and throws an exception)
            self.game_done(game_state=game_state)

        # a move was made by the opponent
        self.opponent_moved(game_state)
        # if there is a chess clock
        if self.chess_clock:
            # signal move
            self.chess_clock.move_made(game_state)

        # tmp_chessboard.turn == True when white, false when black playing_white is same
        if tmp_chessboard.turn == self.playing_white:
            # get our move from chessboard
            move = self.get_move_from_chessboard(tmp_chessboard)

            # make the move
            logger.debug(
                "calling make_move(%s) to make the move from the chessboard in lila game",
                move,
            )
            self.make_move(move)

    def check_for_game_over(self, game_state: GameState) -> None:
        """check a game state to see if the game is through if so raise an exception."""
        global logger, nl_inst
        logger.debug(
            "check_for_game_over(self, game_state) entered w/ gamestate: %s", game_state
        )
        if game_state.winner:
            self.game_done(game_state=game_state)
        elif nl_inst.game_over.is_set():
            self.game_done()
        else:
            logger.debug("game not found to be over.")

    def handle_chat_line(self, chat_line: str) -> None:
        """handle when the other person types something in gamechat
        @param: chat_line - the chat line got from lila
        @side_effect: changes lights and beep's chess board
        """
        global nl_inst
        nl_inst.signal_lights(sig_num=1)
        print(chat_line)
        # signal_lights set's lights on the chess board
        nl_inst.signal_lights(1)
        nl_inst.beep()
        sleep(0.6)
        nl_inst.beep()


### helper functions ###
def show_FEN_on_board(FEN) -> None:
    """show board FEN on an ascii chessboard
    @param FEN - the fed to display on a board"""
    tmp_chessboard = chess.Board()
    tmp_chessboard.set_fen(FEN)
    print(tmp_chessboard)


def handle_game_start(
    game_start: GameStart, chess_clock: bool | ChessClock = False
) -> None:
    """handle game start event
    @param game_start: Typed Dict containing the game start info
    @param chess_clock: ase we using an external chess clock?
    @global berserk_client: client made for ous session with lila
    @global game: the Game class object, global bc has to be accessed everywhere
    """
    global berserk_client, logger, game

    # check if game speed is correspondence, skip those if --correspondence argument is not set
    if not correspondence:
        if game_start["game"]["speed"] == "correspondence":
            logger.info(
                "skipping correspondence game w/ id: %s\n", game_start["game"]["id"]
            )
            return

    # signal game start
    nl_inst.signal_lights(3)

    logger.info(
        "\nhandle_game_start(GameStart) enterd w game_start: \n %s\n", str(game_start)
    )
    game_data = LichessGame(game_start["game"])
    game_fen = game_data.fen

    msg = f"\ngame start received: { str(game_start) }\nyou play: %s" % game_data.colour
    print(msg)
    logger.debug(msg)

    if game_data.hasMoved:
        """handle ongoing game"""
        handle_ongoing_game(game_data)

    playing_white = game_data.playing_white()
    try:
        if game and game.is_alive():
            logger.error(
                "\nERROR: tried to start a new game while game thread is still alive"
            )
            raise NicLinkHandlingGame(
                "the game thread is still alive, a new game can not be started"
            )

        game = Game(
            berserk_client,
            game_data.id,
            playing_white,
            starting_fen=game_fen,
            chess_clock=chess_clock,
        )
        game.daemon = True

        logger.info("|| starting Game thread for game with id: %s\n", game_data.id)
        game.start()  # start the game thread

    except ResponseError as e:
        if "This game cannot be played with the Board API" in str(e):
            print("cannot play this game via board api")
        log_handled_exception(e)
    except KeyboardInterrupt:
        # mak exig good? IDK
        sys.exit(0)


def handle_ongoing_game(game: LichessGame) -> None:
    """handle joining a game that is alredy underway"""

    print("\n$$$ joining game in progress $$$\n")
    logger.info("joining game in proggress, game: \n %s", game)
    if game.isMyTurn:
        print("it is your turn. make a move.")
    else:
        print("it is your opponents turn.")


def handle_resign(event=None) -> None:
    """handle ending the game in the case where you resign."""
    global logger, game
    # end the game
    if event is not None:
        logger.info("handle_resign entered: event: %s", event)
        game.game_done(event=event)
    else:
        logger.info("handle_resign entered with no event")
        game.game_done()


# entry point
def main():
    """handle startup, and initiation of stuff"""
    global berserk_client, nl_inst, REFRESH_DELAY, logger

    print("=== NicLink lichess main entered ===")
    simplejson_spec = importlib.util.find_spec("simplejson")
    if simplejson_spec is not None:
        print(
            "ERROR: simplejson is installed. The berserk lichess client will not work with simplejson. Please remove the module. Aborting."
        )
        sys.exit(-1)

    # init NicLink
    try:
        nl_inst = NicLinkManager(refresh_delay=REFRESH_DELAY, logger=logger)
        nl_inst.start()

    except ExitNicLink:
        logger.error("ExitNicLink exception caught in main()")
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
        logger.error(
            "ERROR: cannot find token file @ ",
        )
        sys.exit(-1)
    except PermissionError:
        logger.error(f"ERROR: permission denied on token file")
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
            berserk_client = berserk.Client(session, base_url="https://lichess.dev")
        else:
            berserk_client = berserk.Client(session)
    except KeyboardInterrupt as err:
        log_handled_exception(err)
        print("KeyboardInterrupt: bye")
        sys.exit(0)
    except:
        e = sys.exc_info()[0]
        error_txt = f"cannot create lichess client: {e}"
        logger.error(error_txt)
        print(error_txt)
        sys.exit(-1)

    # get username
    try:
        account_info = berserk_client.account.get()
        username = account_info["username"]
        print(f"\nUSERNAME: { username }\n")
    except KeyboardInterrupt:
        print("KeyboardInterrupt: bye")
        sys.exit(0)
    except:
        e = sys.exc_info()[0]
        logger.error("cannot get lichess acount info: %s", e)
        print(f"cannot get lichess acount info: {e}")
        sys.exit(-1)
    try:
        # main program loop
        while True:
            try:
                logger.debug("==== lichess event loop start ====\n")
                print("=== Waiting for lichess event ===")
                for event in berserk_client.board.stream_incoming_events():
                    if event["type"] == "challenge":
                        logger.info("challenge received: %s", event)
                        print("\n==== Challenge received ====\n")
                        print(event)
                    elif event["type"] == "gameStart":
                        # wrap the gameStart in a Typed Dict class
                        gameStart = GameStart(event)
                        # and handle getting it started
                        handle_game_start(gameStart)
                    elif event["type"] == "gameFull":
                        logger.info("\ngameFull received\n")
                        handle_resign(event)
                        print("GAME FULL received")

                    # check for kill switch
                    if nl_inst.kill_switch.is_set():
                        sys.exit(0)

                logger.info("berserk stream exited")
                sleep(POLL_DELAY)

            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt: bye")
                try:
                    nl_inst.kill_switch.set()
                except Exception as err:
                    log_handled_exception(err)
                finally:
                    raise ExitNicLink("KeyboardInterrupt in __main__")
            except ResponseError as e:
                logger.error("Invalid server response: %s", e)
                if "Too Many Requests for url" in str(e):
                    sleep(10)

            except NicLinkGameOver:
                logger.info("NicLinkGameOver excepted, good game?")
                print("game over, you can play another. Waiting for lichess event...")
                handle_resign()

    except ExitNicLink:
        print("Have a nice life")
        sys.exit(0)


if __name__ == "__main__":
    main()
