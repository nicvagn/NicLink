#! /bin/python
#  lcd_display as a part of Niclink
#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

import serial
from time import time
from datetime import timedelta
import logging

from lichess.__main__ import Game


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

TIMEOUT = 100.0
BAUDRATE = 115200
PORT = "/dev/ttyACM0"


class ChessClock:
    """a controlling class to encapsulate and facilitate interaction's
    with Arduino chess clock. Starts the game time when this object is
    created
    """

    def __init__(
        self,
        game: Game,
        logger=logging.getLogger("clock"),
        port=PORT,
        baudrate=BAUDRATE,
        timeout=TIMEOUT,
    ) -> None:
        """initialize connection with ardino, and record start time"""
        self.logger = logger
        self.chess_clock = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        # the time in seconds from epoch that this ChessClock
        # is created. This will be at the start of a game
        self.game_start = time()

        # the game this timer is for
        self.game = game

    def update_chess_clock(self) -> None:
        """keep the external timer displaying correct time.
        The time stamp shuld be formated with both w and b timestamp set up to display
        correctly on a 16 x 2 LCD"""

        timestamp = self.create_timestamp()
        self.logger.info("\nTIMESTAMP: %s \n", timestamp)
        self.send_string(timestamp)

    def create_timestamp(self) -> str:

        timestamp = f"W: { str(self.game.game_state.get_wtime()) } \
                B:{ str(self.game.game_state.get_btime()) }"

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
