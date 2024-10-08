#  This file is a part of NicLink
#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

print("NicLink: Running all tests")
import logging
import time

import chess
import numpy as np
import readchar
import test_niclink_board_compairison as nlbc
import test_niclink_FEN as nlf
import test_niclink_lights as nll
import test_niclink_move_parsing as nlmv

from niclink import NicLinkManager

ONES = np.array(
    [
        "11111111",
        "11111111",
        "11111111",
        "11111111",
        "11111111",
        "11111111",
        "11111111",
        "11111111",
    ],
    dtype=np.str_,
)
ZEROS = np.array(
    [
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
    ],
    dtype=np.str_,
)
global logger

logger = logging.getLogger("test_all")


def test_usb():
    """test usb connection"""
    global logger

    b1 = chess.Board()
    b2 = chess.Board()
    b2.push_uci("e2e4")
    nl_man = NicLinkManager(2, logger=logger)

    nl_man.signal_lights(1)

    logger.info("TEST: show board diff: shold be e2e4 lit up.")
    nl_man.show_board_diff(b1, b2)
    readchar.readchar()

    print("TEST: set_move_led w map")
    print("e2e4")
    nl_man.set_move_LEDs("e2e4")
    readchar.readchar()
    print("BOARD CLEAR, press a key")
    nl_man.set_all_LEDs(ZEROS)

    readchar.readchar()

    print("TEST: man.show_board_diff(b1,b2)")
    nl_man.show_board_diff(b1, b2)

    readchar.readchar()
    print("(test usb connection) testing  set_all_LEDs.")

    nl_man.set_all_LEDs(ONES)
    print("all the lights should be on, confirm and press enter")
    readchar.readchar()

    nl_man.set_all_LEDs(ZEROS)
    print("all the lights should be off, confirm and press enter")
    readchar.readchar()

    print(
        "testing  man.signal_lights(). lights should flash on and return to showing last move"
    )
    nl_man.signal_lights(1)

    print("(test usb connection) set up the board and press enter.")
    nl_man.show_game_board()
    print(
        "Now, make a move on the board and test move geting. Press return when ready. This is the last test."
    )
    readchar.readkey()

    while True:
        # TODO: make sure await move work's
        move = nl_man.await_move()
        nl_man.make_move_game_board(move)
        print(move)
        time.sleep(2)

        print(
            "testing  man.signal_lights(). lights should flash on and return to showing last move"
        )
        nl_man.signal_lights(1)


if __name__ == "__main__":

    test_usb()
