#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.to use the len() function
import niclink
import chess

print("test niclink board compaire")

b1 = chess.Board()
b2 = chess.Board()

nl = niclink.NicLinkManager(1)

print("test identical boards(should be no diff)")
nl.show_board_diff(b1, b2)

print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

print("should be a diff on e2 e4")
b1.push_uci("e2e4")
nl.show_board_diff(b1, b2)

print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

print("should be a lot of diffs")
b2.set_fen("rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2")
nl.show_board_diff(b1, b2)
