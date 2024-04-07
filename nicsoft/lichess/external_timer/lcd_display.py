#  lcd_display as a part of Niclink
#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

import serial
from time import sleep


TIMEOUT = 50.0
BAUDRATE = 115200
PORT = "/dev/ttyACM0"
chess_clock = serial.Serial(port=PORT, baudrate=BAUDRATE, timeout=TIMEOUT)

# TODO: update this to work with updated chess_clock.ino script, and document


def send_string(message: str):
    """send a String to the external chess clock"""
    chess_clock.write(message.encode())


def send_timestamp(message: str):
    """send timestamp. First write a '1' to signal the chess_clock we are sending a ts
    The * character is the delimeter for the ardino. | is the delimeter for seperating
    the timestamp. The cc will send a '1' to signal it is ready for black's time"""
    if isinstance(message, str):

        chess_clock.write(b"1")  # to tell the clock we are sending a ts

        display_lines = message.split("|")
        print(display_lines)

        white_ts = display_lines[0]
        print(f"whites time stamp: {white_ts}")
        chess_clock.write(bytes(white_ts, "utf-8"))
        sleep(TIMEOUT / 1000)  # TIMEOUT in miliseconds

        chess_clock.read(1)

        black_ts = display_lines[1]
        print(black_ts)
        chess_clock.write(bytes(black_ts, "utf-8"))
        sleep(TIMEOUT / 1000)  # TIMEOUT in miliseconds

    else:
        raise ValueError("send_timestamp's message should be a str")


if __name__ == "__main__":
    send_timestamp("W: 4.44.44 *|B: 3.33.33*")
    while True:
        pass
