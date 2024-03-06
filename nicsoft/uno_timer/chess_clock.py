#  chess_clock is a part of NicLink
#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the gnu general public license as published by the free software foundation, either version 3 of the license, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but without any warranty; without even the implied warranty of merchantability or fitness for a particular purpose. see the gnu general public license for more details.
#
#  you should have received a copy of the gnu general public license along with NicLink. if not, see <https://www.gnu.org/licenses/>.

import pyfirmata
import threading
import time
import os
import sys
if __name__ == '__main__':
    # import shinanigans. If this is not __main__ this should already be done
    script_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(script_dir)
    sys.path.append(parent_dir)

arduino_address = "/dev/ttyACM0"
# the wait time for refreshing the clock
CLOCK_REFRESH = 0.3

class ChessClock(threading.Thread)
    """in charge of the time in a chessgame"""

    def __init__(self, game: Game, arduino_address=None **kwargs):
        super.__init__(**kwargs)
        if arduino_address is not None:
            arduino = pyfirmata.Arduino(arduino_address)

            bmoved = threading.Event()
            wmoved = threading.Event()

            # make this a daemon, a ChessClock has little use alone
            self.setDaemon(True)
        
    def start(game_state: dict) -> None:
        """start the countdown for a chess game"""
        # {'type': 'gameState', 'moves': 'd2d3 e7e6 b1c3', 'wtime': datetime.datetime( 1970, 1, 25, 20, 31, 23, 647000, tzinfo=datetime.timezone.utc ), 'btime': datetime.datetime( 1970, 1, 25, 20, 31, 23, 647000, tzinfo=datetime.timezone.utc ), 'winc': datetime.datetime( 1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc ), 'binc': datetime.datetime( 1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc ), 'bdraw': False, 'wdraw': False}
        breakpoint()

        # stuff about current game
        # whites total game time
        self.white_time = game_state["wtime"]
        self.black_time = game_state["btime"]

        # the white and black increment
        self.white_inc = game_state["winc"]
        self.black_inc = game_state["binc"]

        # start time    
        start_time = time.time()

        time.sleep(1)
        uno.digital[13].write(1)

    def run():
        """run the chessclock"""
        
        while True:
            pass



arduino = pyfirmata.Arduino(arduino_address)
def test_clock() -> None:
    """test the external Arduino chess clock"""
    toggle = False
    while True:
        if toggle:
            arduino.digital[7].write(1)
        else:
            arduino.digital[7].write(0)
        time.sleep(1)
        toggle = not toggle

