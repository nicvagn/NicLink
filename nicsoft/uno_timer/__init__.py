#  chessclock is a part of NicLink
#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the gnu general public license as published by the free software foundation, either version 3 of the license, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but without any warranty; without even the implied warranty of merchantability or fitness for a particular purpose. see the gnu general public license for more details.
#
#  you should have received a copy of the gnu general public license along with NicLink. if not, see <https://www.gnu.org/licenses/>.

import pyfirmata
import time

uno = pyfirmata.Arduino("/dev/ttyACM0")

def start_chess_clock(game_length) -> None:
    """start the countdown for a chess game"""
    breakpoint()


while True:
    uno.digital[13].write(1)
    time.sleep(1)
    uno.digital[13].write(0)
    time.sleep(1)
