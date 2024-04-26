#! /bin/python
#  chess_clock is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  chess_clock is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with chess_clock. If not, see <https://www.gnu.org/licenses/>.

import logging
import os
import sys
from datetime import datetime, timedelta
from threading import Event, Lock, Thread
from time import sleep

import berserk
import readchar
import serial
from berserk import Client
from berserk.exceptions import ResponseError
from game_start import GameStart  # TODO: IMPLIMENT WRAPPER
from game_state import GameState

import niclink.nl_exceptions
from niclink.nl_exceptions import *

### events ###
# is the lcd being used for a game
lcd_displaying_game = Event()


"""
snip from chess_clock.ino
  case '2':
    signalGameOver();
    break;
  case '3':
    // show a str on LED read from Serial
    printSerialMessage();
    break;
  case '4':
    // start a new game
    newGame();
    break;
  case '5':
    // show the splay
    niclink_splash();
    break;
  case '6':
    // white one, and the game is over
    white_won();
    break;
  case '7':
    // black won the game
    black_won();
    break;
  case '8':
    // game is a draw
    drawn_game();
    break;
  case '@':
    //say hello
    lcd.clear();
    lcd.setCursor(1, 0);
    lcd.print("Hi there");
    break;
"""


class ChessClock:
    """a controlling class to encapsulate and facilitate interaction's
    with Arduino chess clock. Starts the game time when this object is
    created

    Attributes
    ----------
        logger : logger
            self explanitory I think
        chess_clock : Serial
            the serial port that the niclink(tm) ardino
            chess clock is connected to
        lcd_length : int
            the char lingth of the lcd in chess clock
        displayed_wtime : timedelta
            the last recived white time delta from lila
        displayed_btime : timedelta
            the last recived black time delta from lila
        move_time : datetime | None
            time of the last move
        white_to_move : bool
            is it whites move?

    """

    def __init__(
        self,
        serial_port: str,
        baudrate: int,
        timeout: float,
        logger=None,
    ):  # , port="/dev/ttyACM0", baudrate=115200, timeout=100.0) -> None:
        """initialize connection with ardino, and record start time"""
        # the refresh rate of the lcd
        self.TIME_REFRESH = 0.5
        if logger is not None:
            self.logger = logger
        else:
            raise Exception("no logger")
        self.chess_clock = serial.Serial(
            port=serial_port, baudrate=baudrate, timeout=timeout
        )

        self.lcd_length = 16
        # times to be displayed on lcd
        self.displayed_btime: timedelta = None
        self.displayed_wtime: timedelta = None
        # the countdown thread var
        self.countdown: None | Thread = None
        self.move_time: None | datetime = None
        # event to signal white to move
        self.white_to_move: threading.Event = Event()
        # event to signal game over
        self.game_over_event: threading.Event = Event()
        # event telling if clock is initialized
        self.clock_initialized: threading.Event = Event()
        # a lock for accessing the time vars
        self.time_lock = Lock()
        # lcd use lock
        self.lcd_lock = Lock()

        # time left for the player that moved, at move time
        self.time_left_at_move: timedelta = None

        self.logger.info("ChessClock initialized")

    def game_over(self, display_message=True) -> None:
        """Case 2: signal game over, w ASCII 2 and stop counting down"""
        global lcd_displaying_game
        self.logger.info("game_over(...) entered")
        self.game_over_event.set()
        lcd_displaying_game.clear()
        if display_message:
            self.chess_clock.write("2".encode("ascii"))

        if self.displayed_btime is not None and self.displayed_wtime is not None:
            self.logger.info(
                "\nChessClock.game_over() entered w current ts: %s\n"
                % (self.create_timestamp(self.displayed_wtime, self.displayed_btime))
            )
        else:
            self.logger.warn(
                "ChessClock.game_over(): self.displayed_btime or self.displayed_wtime is None"
            )
        self.logger.info("ChessClock.game_over(...) called")

    def send_string(self, message: str) -> None:
        """Case 3: send a String to the external chess clock"""
        # because there are multiple threads that call this function
        with self.lcd_lock:
            # tell the clock we want to display a msg
            self.chess_clock.write("3".encode("ascii"))
            # send the message
            self.chess_clock.write(message.encode("ascii"))

    def start_new_game(
        self,
        game_stream,
    ) -> None:
        """Case 4: signal clock to start a new game
        reset all the game time data.
        """
        self.logger.info("\nchess_clock: start_new_game entered \n")

        # clear game_over_event
        self.game_over_event.clear()

        """Do not display that a new game has been started,
        keep the time of the new game up
        old: self.chess_clock.write("4".encode("ascii"))
        """

        # reinit clock
        self.initialize_clock()

    def show_splash(self) -> None:
        """Case 5: show the nl splash"""
        self.chess_clock.write("5".encode("ascii"))

    def white_won(self) -> None:
        """Case 6: show that white won"""
        self.chess_clock.write("6".encode("ascii"))
        self.game_over(display_message=False)

    def black_won(self) -> None:
        """Case 7: show that black won"""
        self.chess_clock.write("7".encode("ascii"))
        self.game_over(display_message=False)

    def drawn_game(self) -> None:
        """Case 8: show game is drawn"""
        self.chess_clock.write("8".encode("ascii"))
        self.game_over(display_message=False)

    def show_splash(self) -> None:
        """Case 5: show the nl splash"""
        self.chess_clock.write("5".encode("ascii"))

    def white_won(self) -> None:
        """Case 6: show that white won"""
        self.chess_clock.write("6".encode("ascii"))
        self.game_over(display_message=False)

    def black_won(self) -> None:
        """Case 7: show that black won"""
        self.chess_clock.write("7".encode("ascii"))
        self.game_over(display_message=False)

    def drawn_game(self) -> None:
        """Case 8: show game is drawn"""
        self.chess_clock.write("8".encode("ascii"))
        self.game_over(display_message=False)

    def move_made(self, game_state: GameState) -> None:
        """a move was made in the game this chess clock is for.
        self.move_time is set.
        """
        with self.time_lock:
            # record the move_time
            self.move_time = datetime.now()
            self.logger.info("\nrecorded move time: %s\n", self.move_time)
            self.displayed_wtime: timedelta = game_state.wtime
            self.displayed_btime: timedelta = game_state.btime

            # record the time player has left at move time
            if self.white_to_move.is_set():
                self.time_left_at_move = self.displayed_wtime
                # clear event
                self.white_to_move.clear()
            else:
                self.time_left_at_move = self.displayed_btime
                # set white_to move
                self.white_to_move.set()

    def update_lcd(self, wtime: timedelta, btime: timedelta) -> None:
        """keep the external timer displaying correct time.
        The time stamp shuld be formated with both w and b timestamp set up to display
        correctly on a 16 x 2 lcd
        """
        timestamp = self.create_timestamp(wtime, btime)
        self.logger.info(
            "\n\nTIMESTAMP: %s white_to_move: %s\n",
            timestamp,
            self.white_to_move.is_set(),
        )
        self.send_string(timestamp)

    def initialize_clock(self, gameState: GameState) -> None:
        """initilize the clock. This involves reading the time from lila event
        and displaying the game time on the ext clock
        @param initial gameState from berserk
        """
        self.logger.info(
            "\nfunction entered:\ninitialize_clock(...) entered w gameState %s",
            gameState,
        )

        # make sure countown is exited
        if self.countdown is not None:
            if self.countdown.is_alive():
                raise Exception("ChessClock.countdown() is still alive")
        self.logger.info(
            "\ngameState.is_white_to_move: %s\n",
            gameState.is_white_to_move(),
        )
        # allow for joining a game in progress. ie: if it's black's move
        if gameState.is_white_to_move(gameState):
            self.time_left_at_move = gameState.get_wtime()
            self.white_to_move.set()
        else:
            self.time_left_at_move = gameState.get_btime()
            self.white_to_move.clear()

        # init lcd by displaying the starting white and black times

        if gameState.has_moves():
            # start timekeeper thread
            self.countdown = Thread(target=self.time_keeper, args=(self,), daemon=True)
            self.countdown.start()
        else:
            self.logger.info(
                "ChessClock.initialize_clock(...): clock initialized, but not started.\
'hasMoved' not True"
            )
            self.update_lcd(game_state.get_wtime(), game_state.get_btime())
        # signal that clock is initalized
        self.clock_initialized.set()

    def display_initial_time(self, game_state: GameState) -> None:
        with self.time_lock:
            # record the move_time
            self.logger.info("\ndisplay inital time entered: %s\n")
            wtime = game_state.get_wtime()
            btime = game_state.get_btime()

            ts = self.create_timestamp(wtime, btime)

            self.update_lcd(gameState.get_wtime(), gameState.get_btime())

    def create_timestamp(self, wtime: timedelta, btime: timedelta) -> str:
        """create timestamp with white and black time for display on lcd
        @param: wtime timedelta contaning whites time
        @param: btime timedelta contaning blacks time
        @returns: a 2 X lcd_length string. It will overflow onto the seccond row
        """
        # update the last received btime and wtime
        with self.time_lock:
            self.displayed_wtime = wtime
            self.displayed_btime = btime

            # ensure ts uses all the space, needed for lcd side
            white_time = f"W: { str(wtime) }"
            if len(white_time) > self.lcd_length:
                white_time = white_time[: self.lcd_length]
            else:
                while len(white_time) < self.lcd_length:
                    white_time += " "

            black_time = f"B: { str(btime) }"
            if len(black_time) > self.lcd_length:
                black_time = black_time[: self.lcd_length]
            else:
                while len(black_time) < self.lcd_length:
                    black_time += " "

            timestamp = f"{white_time}{black_time}"
            self.logger.info(
                "timestamp created: %s, from timedeltas wtime: %s, and btime: %s",
                timestamp,
                wtime,
                btime,
            )
            return timestamp

    @staticmethod
    def did_flag(player_time: timedelta) -> bool:
        """check if a timedelta is 0 total_seconds or less. ie: they flaged
        @param: player_time (timedelta) - timedelta of how much time a player has
        @returns: (bool) if they flaged
        """
        global logger
        logger.info("did_flag(player_time) with player time %s", player_time)
        if type(player_time) is timedelta:
            if player_time.total_seconds() <= 0:
                return True
        else:
            logger.warning(
                "ChessClock.did_flag(player_time): player_time is not a timedelta"
            )

        return False

    @staticmethod
    def time_keeper(chess_clock) -> None:
        """keep the time on the lcd correct. using the last time a move was made
        @param: chess_clock (ChessClock) - a ChessClock
        @raises:
            NicLinkGameOver:
                - if game_over_event is set
                - if white or black flags
        """
        global logger

        while True:
            # if the game is over, kill the time_keeper
            if chess_clock.game_over_event.is_set():
                logger.warning("game_over_event is set")
                raise NicLinkGameOver(
                    """time_keeper(...) exiting. 
chess_clock.game_over_event.is_set()"""
                )
            if chess_clock.move_time is None:
                logger.warning("chess_clock.move_time is None")
                sleep(chess_clock.TIME_REFRESH)
                continue
            if chess_clock.time_left_at_move is None:
                logger.warning("chess_clock.time_left_at_move is None")
                sleep(chess_clock.TIME_REFRESH)
                continue
            if chess_clock.displayed_btime is None:
                logger.warning("chess_clock.displayed_btime is None")
                sleep(chess_clock.TIME_REFRESH)
                continue
            if chess_clock.displayed_wtime is None:
                logger.warning("chess_clock.displayed_wtime is None")
                sleep(chess_clock.TIME_REFRESH)
                continue

            # if it is white to move
            if chess_clock.white_to_move.is_set():
                # breakpoint()
                # create a new timedelta with the updated wtime
                new_wtime = chess_clock.time_left_at_move - (
                    datetime.now() - chess_clock.move_time
                )
                # check for flag for white
                if ChessClock.did_flag(new_wtime):
                    chess_clock.white_won()
                    # kill the thread
                    raise NicLinkGameOver("white flaged")
                # update the clock
                chess_clock.update_lcd(new_wtime, chess_clock.displayed_btime)
            # else black to move
            else:
                # breakpoint()
                # create a new timedelta object w updated b time
                new_btime = chess_clock.time_left_at_move - (
                    datetime.now() - chess_clock.move_time
                )

                # check if black has flaged
                if ChessClock.did_flag(chess_clock.displayed_btime):
                    chess_clock.black_won()
                    # kill the thread
                    raise NicLinkGameOver("black flaged")
                # update the clock
                chess_clock.update_lcd(chess_clock.displayed_wtime, new_btime)

            sleep(chess_clock.TIME_REFRESH)


def handle_game_start(
    game_start: GameStart, berserk_client: Client, chess_clock: ChessClock
) -> None:
    """handle game start event.
    @param game_start - berserk event
    @raises: RuntimeError if the chess clock is still handleing a game
    """
    global logger, lcd_handling_game

    game_data = game_start["game"]
    # no clock for correspondence
    if game_data["speed"] == "correspondence":
        logger.info("SKIPPING correspondence game w/ id %s \n", game_data["id"])
        return

    # clear game_over_event
    chess_clock.game_over_event.clear()
    # check for correspondance
    logger.info("\nhandle_game_start(...) called with game_start: %s", game_start)

    # start the chess clock for this game
    if not lcd_displaying_game.is_set():
        chess_clock.start_new_game(game_data["id"])
    else:
        raise RuntimeError("lcd displaying game currently")


def main() -> None:
    global logger
    PORT = "/dev/ttyACM0"
    BR = 115200  # baudrate for Serial connection
    REFRESH_DELAY = 100.0  # refresh delay for chess_clock
    SCRIPT_DIR = os.path.dirname(__file__)
    TOKEN_FILE = os.path.join(SCRIPT_DIR, "lichess_token/token")

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
        session: Session = berserk.TokenSession(token)
    except:
        e = sys.exc_info()[0]
        log_handled_exception(e)
        print(f"cannot create session: {e}")
        logger.info("cannot create session", e)
        sys.exit(-1)

    try:
        berserk_client: Client = berserk.Client(session)
    except KeyboardInterrupt as err:
        log_handled_exception(err)
        print("KeyboardInterrupt: bye")
        sys.exit(0)
    except:
        e = sys.exc_info()[0]
        error_txt = f"cannot create lichess client: {e}"
        logger.info(error_txt)
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
        logger.info("cannot get lichess acount info: %s", e)
        print(f"cannot get lichess acount info: {e}")
        sys.exit(-1)

    chess_clock = ChessClock(
        PORT,
        BR,
        REFRESH_DELAY,
        logger=logger,
    )

    # test_chessclock(chess_clock)
    # main program loop
    while True:
        try:
            logger.debug("\n==== event loop ====\n")
            print("=== Waiting for lichess event ===")
            for event in berserk_client.board.stream_incoming_events():
                if event["type"] == "challenge":
                    logger.info("challenge received: %s", event)
                    print("\n==== Challenge received ====\n")
                    print(event)
                elif event["type"] == "gameStart":
                    logger.info("\n'gameStart' received from stream in main()")
                    # a game is starting, it is handled by a function
                    handle_game_start(event, berserk_client.board, chess_clock)
                elif event["type"] == "gameFull":
                    logger.info("\ngameFull received\n")
                    if event["status"] == "started":
                        print("GAME FULL received")
                        raise NotImplementedError("gamefull event: %s", event)

        except ResponseError as e:
            print(f"ERROR: Invalid server response: {e}")
            logger.info("Invalid server response: %s", e)
            if "Too Many Requests for url" in str(e):
                sleep(150)
            else:
                # kill the program
                raise RuntimeError("UNKNOWN ResponseError %s", e)
        # sleep for some time b/f pulling endpoint again
        sleep(100)


if __name__ == "__main__":
    logger = logging.getLogger("chess_clock")
    main()
