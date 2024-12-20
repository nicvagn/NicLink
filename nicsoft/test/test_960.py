#  NicLink is free software you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

import sys
import time

import chess
import readchar

from niclink import NicLinkManager


def test():

    print("\n=====================\n Test 960 Move Parsing \n=====================\n")

    leave = "n"

    while leave == "n":
        print("make a legal move:\n")

        # wait for a move
        try:
            move = nl.await_move()
        except ValueError:
            print("No move, pausing for 3 seconds and trying again")

            time.sleep(3)
            continue

        # show the internal board state
        # nl_inst.show_game_board()

        print(f"\n==== { move } ====\n")
        print("leave? 'n' for no, != 'n' yes: ")
        leave = readchar.readkey()


if __name__ == "__main__":

    nl = NicLinkManager(2, None)

    nl.start_960("nbqrknbr/pppppppp/8/8/8/8/PPPPPPPP/NBQRKNBR")
    test()
