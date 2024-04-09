#! /bin/python
#  lcd_display as a part of Niclink
#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

import serial
from time import time, sleep
from datetime import timedelta
import logging


""" snippet from Ardino sketch
  switch (whatToDo) {
    case '1':
      // asking for time
      if (gameOver) {  // if the game is over, do not update ts
        break;
      }
      showTimestamp();
          break;
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
    """

    def __init__(
        self, serial_port: str, baudrate: int, timeout: float
    ):  # , port="/dev/ttyACM1", baudrate=115200, timeout=100.0) -> None:
        """initialize connection with ardino, and record start time"""
        self.logger = logging.getLogger("nl_lichess")
        self.chess_clock = serial.Serial(
            port=serial_port, baudrate=baudrate, timeout=timeout
        )
        self.game_start = None
        self.new_game()
        self.lcd_length = 16

    def update_chess_clock(self, wtime: timedelta, btime: timedelta) -> None:
        """keep the external timer displaying correct time.
        The time stamp shuld be formated with both w and b timestamp set up to display
        correctly on a 16 x 2 LCD"""

        timestamp = self.create_timestamp(wtime, btime)
        self.logger.info("\n\nTIMESTAMP: %s /n", timestamp)
        self.send_string(timestamp)

    def create_timestamp(self, wtime: timedelta, btime: timedelta) -> str:
        """create timestamp with white and black time for display on lcd"""
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

    def game_over(self) -> None:
        """Case 2: signal game over, w ASCII 2"""
        self.chess_clock.write("2".encode("ascii"))

    def send_string(self, message: str) -> None:
        """Case 3: send a String to the external chess clock"""
        self.chess_clock.write("3".encode("ascii"))

        # tell the clock we want to display a msg
        self.chess_clock.write(message.encode("ascii"))

    def new_game(self) -> None:
        """Case 4: signal clock to start a new game"""
        self.chess_clock.write("4".encode("ascii"))
        self.game_start = time()

    def show_splash(self) -> None:
        """Case 5: show the nl splash"""

        self.chess_clock.write("5".encode("ascii"))

    def white_won(self) -> None:
        """Case 6: show that white won"""
        self.chess_clock.write("6".encode("ascii"))

    def black_won(self) -> None:
        """Case 7: show that black won"""
        self.chess_clock.write("7".encode("ascii"))

    def drawn_game(self) -> None:
        """Case 8: show game is drawn"""
        self.chess_clock.write("8".encode("ascii"))


if __name__ == "__main__":
    print("this is not designed to be run as __main__")
    chess_clock = ChessClock("/dev/ttyACM1", 115200, 100.0)
    sleep(3)
    chess_clock.update_chess_clock(timedelta(minutes=1), timedelta(minutes=1))
    sleep(3)
    chess_clock.game_over()
    sleep(3)
    chess_clock.update_chess_clock(
        timedelta(hours=4, minutes=1), timedelta(hours=3, minutes=33)
    )
    sleep(3)
    chess_clock.game_over()
    sleep(3)
    chess_clock.update_chess_clock(timedelta(minutes=4), timedelta(minutes=8))
