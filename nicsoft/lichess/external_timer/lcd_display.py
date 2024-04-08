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

chess_clock = serial.Serial(port=PORT, baudrate=BAUDRATE, timeout=TIMEOUT)

# TODO: update this to work with updated chess_clock.ino script, and document


# FIX: THIS
def send_timestamp(time_stamp: str):
    """Case 1:send timestamp. First write a '1' to signal the chess_clock we are sending a ts
    The * character is the delimeter for the ardino. | is the delimeter for seperating
    the timestamp. The cc will send a '1' to signal it is ready for black's time"""
    if isinstance(time_stamp, str):
        # to tell the clock we are sending a ts
        chess_clock.write("1".encode("ascii"))

        display_lines = time_stamp.split("|")
        print(display_lines)

        white_ts = display_lines[0]
        print(f"whites time stamp: {white_ts}")
        chess_clock.write(white_ts.encode("ascii"))
        sleep(TIMEOUT / 1000)  # TIMEOUT in miliseconds

        wt = chess_clock.readline()  # confirm clock is ready for black ts
        print(wt)

        black_ts = display_lines[1]
        print(black_ts)
        chess_clock.write(black_ts.encode("ascii"))
        sleep(TIMEOUT / 1000)  # TIMEOUT in miliseconds

    else:
        raise ValueError("send_timestamp should be a str")


def game_over() -> None:
    """Case 2: signal game over, w ASCII 2"""
    chess_clock.write("2".encode("ascii"))


def send_string(message: str):
    """Case 3: send a String to the external chess clock"""
    chess_clock.write("3".encode("ascii"))

    # tell the clock we want to display a msg
    chess_clock.write(message.encode("ascii"))


def new_game() -> None:
    """Case 4: signal clock to start a new game"""
    chess_clock.write("4".encode("ascii"))


def show_splash() -> None:
    """Case 5: show the nl splash"""

    chess_clock.write("5".encode("ascii"))


def white_won() -> None:
    """Case 6: show that white won"""
    chess_clock.write("6".encode("ascii"))


def black_won() -> None:
    """Case 7: show that black won"""
    chess_clock.write("7".encode("ascii"))


def drawn_game() -> None:
    """Case 8: show game is drawn"""
    chess_clock.write("8".encode("ascii"))


if __name__ == "__main__":
    # TODO: 1
    # send_timestamp("W: dt:he:dt*|B: dt:he:ml*")
    # 2
    print("game_over()")
    game_over()
    sleep(5)
    # 3
    print("send_string()")
    send_string("hello lcd")
    sleep(5)
    # 4
    print("new_game()")
    new_game()
    sleep(5)
    # 5
    print("white_won()")
    white_won()
    sleep(5)
    # 6
    print("show_splash()")
    show_splash()
    sleep(5)
    # 7
    print("black_won()")
    black_won()
    sleep(5)

    # over
    print("fin")
    send_string("===== fin =====")
