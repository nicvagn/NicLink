#! /bin/python
#  lcd_display as a part of Niclink
#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

import serial
from time import sleep
from datetime import timedelta, datetime
import logging
import readchar

# from niclink.nl_exceptions import NicLinkGameOver

"""
snip from chess_clock.ino
 
switch (what_to_do[0]) {
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
}
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
        self, serial_port: str, baudrate: int, timeout: float
    ):  # , port="/dev/ttyACM0", baudrate=115200, timeout=100.0) -> None:
        """initialize connection with ardino, and record start time"""
        self.logger = logging.getLogger("nl_lichess")
        self.chess_clock = serial.Serial(
            port=serial_port, baudrate=baudrate, timeout=timeout
        )
        self.lcd_length = 16
        self.game_start = None
        self.displayed_btime = None
        self.displayed_wtime = None

        self.start_new_game()

    # TODO: make update
    def time_keeper(self) -> None:
        """keep the time on the lcd correct. using the last time a move was made"""
        if self.move_time is None:
            raise ValueError(
                "move_time is none, it should be the time of the last move"
            )
        if self.displayed_btime is None:
            raise ValueError(
                "self.displayed_btime is none, it should be blacks time. \
                             Maybe you called this before making a move?"
            )
        if self.displayed_wtime is None:
            raise ValueError(
                "self.displayed_wtime is none, it should be whites time. \
                             Maybe you called this before making a move?"
            )
        # if it is white to move
        if self.white_to_move:
            # create a new timedelta with the updated wtime
            self.displayed_wtime = self.displayed_wtime - (
                datetime.now() - self.move_time
            )
            # check for flag for white
            if ChessClock.did_flag(self.displayed_wtime):
                self.game_over()
            # update the clock
            self.updateLCD(self.displayed_wtime, self.displayed_btime)
        # else black to move
        else:
            # create a new timedelta object w updated b time
            self.displayed_btime = self.displayed_btime - (
                datetime.now() - self.move_time
            )

            # check if black has flaged
            if ChessClock.did_flag(self.displayed_btime):
                self.game_over()
            # update the clock
            self.updateLCD(self.displayed_wtime, self.displayed_btime)

    def move_made(self) -> None:
        """a move was made in the game this chess clock is for. HACK: Must be called
        before first move on game start before time_keeper is called
        """
        # switch who's turn it is
        self.white_to_move = not self.white_to_move
        # record the move_time
        self.move_time = datetime.now()

    def updateLCD(self, wtime: timedelta, btime: timedelta) -> None:
        """keep the external timer displaying correct time.
        The time stamp shuld be formated with both w and b timestamp set up to display
        correctly on a 16 x 2 LCD
        """
        timestamp = self.create_timestamp(wtime, btime)
        self.logger.info("\n\nTIMESTAMP: %s \n", timestamp)
        self.send_string(timestamp)

    def create_timestamp(self, wtime: timedelta, btime: timedelta) -> str:
        """create timestamp with white and black time for display on lcd"""
        # update the last received btime and wtime
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
        self.logger.info("ChessClock.chess_clock() created: %s" % (timestamp))
        print(timestamp)
        return timestamp

    def game_over(self, display_message=True) -> None:
        """Case 2: signal game over, w ASCII 2 and exception
        Raises:
            NicLinkGameOver
        """
        if display_message:
            self.chess_clock.write("2".encode("ascii"))

        if self.displayed_btime is not None and self.displayed_wtime is not None:
            self.logger.info(
                "ChessClock.game_over() entered w current ts: %s"
                % (self.create_timestamp(self.displayed_wtime, self.displayed_btime))
            )
        else:
            self.logger.warn(
                "ChessClock.game_over(): self.displayed_btime or self.displayed_wtime is None"
            )
        self.logger.info("ChessClock.game_over(...) called")

    def send_string(self, message: str) -> None:
        """Case 3: send a String to the external chess clock"""
        self.chess_clock.write("3".encode("ascii"))

        # tell the clock we want to display a msg
        self.chess_clock.write(message.encode("ascii"))

    def start_new_game(self) -> None:
        """Case 4: signal clock to start a new game
        reset all the game time data
        """
        self.chess_clock.write("4".encode("ascii"))

        self.move_time: datetime | None = None
        self.white_to_move: bool = True

        # last recived w and b time
        self.displayed_wtime = None
        self.displayed_btime = None

        self.game_start = datetime.now()
        # HACK: tell the clock that that the game started
        self.move_made()

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

    @staticmethod
    def did_flag(player_time: timedelta) -> bool:
        """check if a timedelta is 0 total_seconds or less. ie: they flaged"""
        if player_time.total_seconds() <= 0:
            return True

        return False


if __name__ == "__main__":

    chess_clock = ChessClock("/dev/ttyACM0", 115200, 100.0)

    chess_clock.displayed_wtime = timedelta(seconds=9)
    chess_clock.displayed_btime = timedelta(seconds=9)
    # init game
    chess_clock.move_made()
    while True:
        chess_clock.time_keeper()
        chess_clock.move_made()

        readchar.readkey()

    print("this is not designed to be run as __main__")
    chess_clock = ChessClock("/dev/ttyACM0", 115200, 100.0)
    sleep(3)
    chess_clock.updateLCD(timedelta(minutes=1), timedelta(minutes=1))
    sleep(3)
    chess_clock.game_over()
    sleep(3)
    chess_clock.updateLCD(timedelta(hours=4, minutes=1), timedelta(hours=3, minutes=33))
    sleep(3)
    chess_clock.game_over()
    sleep(3)
    chess_clock.updateLCD(timedelta(minutes=4), timedelta(minutes=8))
