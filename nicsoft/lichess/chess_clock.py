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
from game import Game
from game_state import GameState

from niclink.nl_exceptions import *

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
    ):
        """initialize connection with ardino, and record start time"""
        # the refresh rate of the lcd
        self.TIME_REFRESH = 0.3
        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger("chess_clock")
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
        # has the countdown been started?
        self.countdown_started = Event()
        # is the lcd handling a game?
        self.handling_game = Event()
        # event to signal white to move
        self.white_to_move: threading.Event = Event()
        # event to signal game over
        self.countdown_kill: threading.Event = Event()
        # a lock for accessing the time vars
        self.time_lock = Lock()
        # lcd use lock
        self.lcd_lock = Lock()
        # time left for the player that moved, at move time
        self.time_left_at_move: timedelta = None

        # clear lcd and lcd serial
        self.clear()
        # countdown thread
        self.countdown = Thread(target=self.time_keeper, args=(self,), daemon=True)
        self.logger.info("ChessClock initialized")

    def clear(self) -> None:
        """case 1: clear the lcd w ASCII 1"""

        self.chess_clock.write("1".encode("ascii"))

    def game_over(self, display_message=True) -> None:
        """Case 2: signal game over, w ASCII 2 and stop counting down"""
        self.logger.info("game_over(...) entered")
        self.countdown_kill.set()
        self.handling_game.clear()

        if display_message:
            """if a message of gameover should be shown. We do not
            want this if we are displaying a custom message"""
            self.chess_clock.write("2".encode("ascii"))

        if self.displayed_btime is not None and self.displayed_wtime is not None:
            self.logger.info(
                "\nChessClock.game_over() entered w current ts: %s\n"
                % (self.create_timestamp(self.displayed_wtime, self.displayed_btime))
            )
        else:
            self.logger.warning(
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

        # from doc: Flush of file like objects. In this case, wait until all data is written.
        self.chess_clock.flush()

    def start_new_game(
        self,
        game: Game,
    ) -> None:
        """Case 4: handle game start event. reset all the game time data.
        @param game - berserk event incased in conviniance class
        @raises: RuntimeError if the chess clock is still handling a game
        """
        self.logger.info("\nchess_clock: start_new_game entered with Game %s \n", game)
        # no clock for correspondence
        if game.speed == "correspondence":
            logger.info("SKIPPING correspondence game w/ id %s \n", game.gameId)
            return
        # make sure countdown thread is dead
        while self.countdown.is_alive():
            self.countdown_kill.set()
            sleep(self.TIME_REFRESH)

        self.countdown_kill.clear()
        # create a new coutdown thread
        self.countdown = Thread(target=self.time_keeper, args=(self,), daemon=True)
        # create starting timestamp
        self.update_lcd(game.get_wtime(), game.get_btime())

        # check for correspondance
        self.logger.info(
            "\nhandle_game_start(...) called with game_start['game'].gameId: %s",
            game.gameId,
        )

        # start the chess clock for this game

        if not self.handling_game.is_set():
            # creat new coundown thread if not handling game
            self.countdown.start()
        else:
            raise RuntimeError("ChessClock.handling_game is set.")

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
        """a move was made in the game this chess clock is for, self.move_time is set.
        @param: game_state the game state at the time of move, or None if there is None
        """
        with self.time_lock:
            # record the move_time
            self.move_time = datetime.now()
            self.logger.info("\nrecorded move time: %s\n", self.move_time)

            if game_state is not None:
                self.displayed_wtime: timedelta = game_state.wtime
                self.displayed_btime: timedelta = game_state.btime
            else:
                # TODO: add incriment
                pass

            # record the time player has left at move time
            if self.white_to_move.is_set():
                self.time_left_at_move = self.displayed_wtime
                # clear event
                self.white_to_move.clear()
            else:
                self.time_left_at_move = self.displayed_btime
                # set white_to move
                self.white_to_move.set()

            # HACK: NO COUNTOWN MODE
            self.update_lcd(self.displayed_wtime, self.displayed_btime)

    def update_lcd(self, wtime: timedelta, btime: timedelta) -> None:
        """display wtime and btime on lcd. creates a timestamp from given times
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

    def did_flag(self, player_time: timedelta) -> bool:
        """check if a timedelta is 0 total_seconds or less. ie: they flaged
        @param: player_time (timedelta) - timedelta of how much time a player has
        @returns: (bool) if they flaged
        """
        self.logger.info("did_flag(player_time) with player time %s", player_time)
        if type(player_time) is timedelta:
            if player_time.total_seconds() <= 0:
                return True
        else:
            self.logger.warning(
                "ChessClock.did_flag(player_time): player_time is not a timedelta"
            )

        return False

    @staticmethod
    def time_keeper(chess_clock) -> None:
        """keep the time on the lcd correct. using the last time a move was made
        @param: chess_clock (ChessClock) - a ChessClock
        @raises:
            NicLinkGameOver:
                - if countdown_kill is set
                - if white or black flags
        """
        # loop inifinatly
        while True:
            # if the game is over, kill the time_keeper
            if chess_clock.countdown_kill.is_set():
                chess_clock.logger.warning("countdown_kill is set")
                raise NicLinkGameOver(
                    """time_keeper(...) exiting. 
chess_clock.countdown_kill.is_set()"""
                )

            if chess_clock.move_time is None:
                chess_clock.logger.warning("chess_clock.move_time is None")
                sleep(chess_clock.TIME_REFRESH)
                continue
            if chess_clock.time_left_at_move is None:
                chess_clock.logger.warning("chess_clock.time_left_at_move is None")
                sleep(chess_clock.TIME_REFRESH)
                continue
            if chess_clock.displayed_btime is None:
                chess_clock.logger.warning("chess_clock.displayed_btime is None")
                sleep(chess_clock.TIME_REFRESH)
                continue
            if chess_clock.displayed_wtime is None:
                chess_clock.logger.warning("chess_clock.displayed_wtime is None")
                sleep(chess_clock.TIME_REFRESH)
                continue

            # if it is white to move
            if chess_clock.white_to_move.is_set():
                # because sometimes time_left_at_move is an int of secondsLeft
                if type(chess_clock.time_left_at_move) is not timedelta:
                    chess_clock.time_left_at_move = timedelta(
                        seconds=chess_clock.time_left_at_move
                    )

                # create a new timedelta with the updated wtime
                new_wtime = chess_clock.time_left_at_move - (
                    datetime.now() - chess_clock.move_time
                )
                # check for flag for white
                if chess_clock.did_flag(new_wtime):
                    chess_clock.black_won()
                    # kill the thread
                    raise NicLinkGameOver("white flaged")
                # update the clock
                chess_clock.update_lcd(new_wtime, chess_clock.displayed_btime)
            # else black to move
            else:
                # because sometimes time_left_at_move is an int of secondsLeft
                if type(chess_clock.time_left_at_move) is not timedelta:
                    chess_clock.time_left_at_move = timedelta(
                        seconds=chess_clock.time_left_at_move
                    )

                # create a new timedelta object w updated b time
                new_btime = chess_clock.time_left_at_move - (
                    datetime.now() - chess_clock.move_time
                )

                # check if black has flaged
                if chess_clock.did_flag(chess_clock.displayed_btime):
                    chess_clock.white_won()
                    # kill the thread
                    raise NicLinkGameOver("black flaged")
                # update the clock, updates displayed time
                chess_clock.update_lcd(chess_clock.displayed_wtime, new_btime)

            sleep(chess_clock.TIME_REFRESH)


### testing ###
def test_timekeeper(cc: ChessClock, game: Game) -> None:
    """test the chess clock's countdown"""
    print("TEST: countdown")
    GS = GameState(
        {
            "type": "gameState",
            "moves": "e2e4 e6e5 d2d4",
            "wtime": timedelta(seconds=24),
            "btime": timedelta(seconds=13),
            "winc": timedelta(seconds=3),
            "binc": timedelta(seconds=3),
            "status": "started",
        }
    )
    cc.start_new_game(game)
    x = "n"
    while x == "n":
        cc.move_made(GS)
        print("press 'n' to move in game, not 'n' to quit")
        x = readchar.readchar()

    cc.game_over()


def test_display_options(cc: ChessClock) -> None:
    """test all the display options"""
    print("TEST: testing display options. press a key to display next")

    print("game_over w message.")
    cc.game_over()
    readchar.readchar()

    print("white won")
    cc.white_won()
    readchar.readchar()

    print("black_won")
    cc.black_won()
    readchar.readchar()

    print("drawn game")
    cc.drawn_game()
    readchar.readchar()

    print("show splash")
    cc.show_splash()
    readchar.readchar()

    print("Send String: Sending reeeee")
    cc.send_string("reeeeeeeeeeeeeeeeeee")
    readchar.readchar()

    print("display test out")


def main() -> None:
    """test ChessClock"""
    global logger
    PORT = "/dev/ttyACM0"
    BR = 115200  # baudrate for Serial connection
    REFRESH_DELAY = 100.0  # refresh delay for chess_clock
    SCRIPT_DIR = os.path.dirname(__file__)
    TOKEN_FILE = os.path.join(SCRIPT_DIR, "lichess_token/token")

    test_display_opts = True
    test_countdown = False

    RAW_GAME = {
        "fullId": "4lmop23qqa8S",
        "gameId": "4lmop23q",
        "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "color": "white",
        "lastMove": "",
        "source": "lobby",
        "status": {"id": 20, "name": "started"},
        "variant": {"key": "standard", "name": "Standard"},
        "speed": "rapid",
        "perf": "rapid",
        "rated": False,
        "hasMoved": False,
        "opponent": {"id": "david002", "username": "David002", "rating": 1376},
        "isMyTurn": True,
        "secondsLeft": 1200,
    }
    GAME_START = Game(RAW_GAME)
    SAMPLE_GAMESTATE0 = GameState(
        {
            "type": "gameState",
            "moves": "",
            "wtime": timedelta(minutes=3),
            "btime": timedelta(minutes=3),
            "winc": timedelta(seconds=3),
            "binc": timedelta(seconds=3),
            "status": "started",
        }
    )
    SAMPLE_GAMESTATE1 = GameState(
        {
            "type": "gameState",
            "moves": "e2e4",
            "wtime": timedelta(minutes=3),
            "btime": timedelta(minutes=3),
            "winc": timedelta(seconds=3),
            "binc": timedelta(seconds=3),
            "status": "started",
        }
    )
    SAMPLE_GAMESTATE2 = GameState(
        {
            "type": "gameState",
            "moves": "e2e4 e6e5",
            "wtime": timedelta(minutes=3),
            "btime": timedelta(minutes=2, seconds=44),
            "winc": timedelta(seconds=3),
            "binc": timedelta(seconds=3),
            "status": "started",
        }
    )
    SAMPLE_GAMESTATE3 = GameState(
        {
            "type": "gameState",
            "moves": "e2e4 e6e5 d2d4",
            "wtime": timedelta(seconds=24),
            "btime": timedelta(seconds=13),
            "winc": timedelta(seconds=3),
            "binc": timedelta(seconds=3),
            "status": "started",
        }
    )

    chess_clock = ChessClock(
        PORT,
        BR,
        REFRESH_DELAY,
        logger=logger,
    )

    if test_countdown:
        test_timekeeper(chess_clock, GAME_START)
    if test_display_opts:
        print("look at lcd")
        test_display_options(chess_clock)

    logger.debug("\n==== test loop ====\n")
    print("clock initialized. Ready for move made.")
    chess_clock.start_new_game(GAME_START)
    readchar.readchar()
    chess_clock.move_made(SAMPLE_GAMESTATE1)
    readchar.readchar()
    chess_clock.move_made(SAMPLE_GAMESTATE2)
    readchar.readchar()
    chess_clock.move_made(SAMPLE_GAMESTATE3)
    readchar.readchar()


if __name__ == "__main__":
    global logger
    # if run as __main__ set up logging
    logger = logging.getLogger("chess_clock")
    consoleHandler = logging.StreamHandler(sys.stdout)

    logger.info("DEBUG is set.")
    logger.setLevel(logging.DEBUG)
    consoleHandler.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(module)s %(message)s")

    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)

    main()
