#  NicLink is free software you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

from niclink import NicLinkManager

import readchar
import sys
import chess
import time

nl_inst = NicLinkManager(2)


print("\n=====================\n Test Move Parsing \n=====================\n")

leave = "n"

while leave == "n":
    print("make a legal move:\n")

    # wait for a move
    try:
        nl_inst.await_move()
    except ValueError:
        print( "No move, pausing for 3 seconds and trying again" )

        time.sleep(3)
        continue

    if nl_inst.check_for_move():
        # beep to indicate a move was made
        nl_inst.beep()

        # show the post move fen on a board
        nl_inst.show_game_board()

        try:
            # find move from the FEN change
            move = nl_inst.get_last_move()

            print(f"\n_________ {move} detected ________\n")
        except KeyboardInterrupt:
            print("KeyboardInterrupt: bye")
            sys.exit(0)
        except RuntimeError as re:
            print(f"{re} reset the board to the previous position an try again")
            # print( f"previous position: \n{nl_inst.game_board}" )
            print("leave? 'n' for no, != 'n' yes: ")
            leave = readchar.readkey()

            continue  # as move will not be defined


    print("\n=================================\n")
    print("leave? 'n' for no, != 'n' yes: ")
    leave = readchar.readkey()
