#  lcd display as a part of Niclink-lichess
#
#  NicLink-lichess is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink-lichess is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

import serial
from time import sleep


TIMEOUT = 500.0
arduino = serial.Serial(port="/dev/ttyACM0", baudrate=115200, timeout=TIMEOUT)


def send_string(message: str):
    """send a String to the external chess clock"""
    arduino.write(message.encode())


def send_timestamp(message: str):
    """send timestamp. The ardino know's how to hanndle it
    The * character is the delimeter for the ardino.
    | is the delimeter for seperating the timestamp"""
    if isinstance(message, str):
        display_lines = message.split("|")
        print(display_lines)

        write_out = display_lines[0]
        print(f"write_out: {write_out}")
        arduino.write(bytes(write_out, "utf-8"))
        sleep(TIMEOUT / 1000)  # TIMEOUT in miliseconds

        write_out = display_lines[1]
        print(write_out)
        arduino.write(bytes(write_out, "utf-8"))
        sleep(TIMEOUT / 1000)  # TIMEOUT in miliseconds

    else:
        raise ValueError("send_timestamp's message should be a str")


if __name__ == "__main__":
    send_timestamp("W: 4.44.44 *|B: 3.33.33*")
    while True:
        pass
