#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.


from niclink import NicLinkManager

import readchar

nl_inst = NicLinkManager(1)

print("\n+++++ niclink test: FEN reading ++++\n")

exit = "n"
while exit == "n":
    currentFEN = nl_inst.get_FEN()
    nl_inst.show_FEN_on_board(currentFEN)
    print("do you want to exit? 'n' for no \n")
    exit = readchar.readchar()
