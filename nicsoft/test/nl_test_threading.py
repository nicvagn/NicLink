#  niclink is free software: you can redistribute it and/or modify it under the terms of the gnu general public license as published by the free software foundation, either version 3 of the license, or (at your option) any later version.
#
#  niclink is distributed in the hope that it will be useful, but without any warranty; without even the implied warranty of merchantability or fitness for a particular purpose. see the gnu general public license for more details.
#
#  you should have received a copy of the gnu general public license along with niclink. if not, see <https://www.gnu.org/licenses/>.

import threading
import logging
import readchar
from niclink import NicLinkManager

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)

nl_thread = NicLinkManager(2, logger)

nl_thread.start()


def test_threading():
    """test usb connection"""

    print("set up the board and press enter.")
    nl_thread.show_game_board()
    print("===============")
    readchar.readkey()

    # set the niclink flag for starting a game
    nl_thread.start_game.set()

    leave = "n"
    while leave == "n":
        print("leave test_threading? ('n' for no)")
        leave = readchar.readkey()

    nl_thread.gameover_lights()
    # set the nl_thread kill switch
    nl_thread.kill_switch.set()


test_threading()
