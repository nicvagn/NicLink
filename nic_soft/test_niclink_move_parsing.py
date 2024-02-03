#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>. 

from niclink import NicLinkManager

import readchar
import sys
import chess

nl_inst = NicLinkManager( 1 )


print( "\n=====================\n Test Move Parsing \n=====================\n" )

exit = 'n'
move_board = chess.Board()
nl_inst.set_game_board( move_board )

while( exit == 'n' ):
    print( "make a legal move:\n" )

    # wait for a move
    nl_inst.await_move()

    if( nl_inst.check_for_move() ):
        # beep to indicate a move was made
        nl_inst.beep()
        print( "\n_________ move detected ________\n")
        # get the new board FEN
        post_move_FEN = nl_inst.get_FEN()


        try:
            # find move from the FEN change
            move = nl_inst.get_last_move()

        except KeyboardInterrupt:
            print("KeyboardInterrupt: bye")
            sys.exit( 0 )
        except RuntimeError as re:
            print( f"{re} reset the board to the previous position an try again" )
            # print( f"previous position: \n{nl_inst.game_board}" )
            print( "leave? 'n' for no, != 'n' yes: " )
            leave = readchar.readkey()

            continue # as move will not be defined

        # make the move on the game board
        nl_inst.make_move_game_board( move )

        print( "\n=================================\n" )
        print("leave? 'n' for no, != 'n' yes: ")
        leave = readchar.readkey()

