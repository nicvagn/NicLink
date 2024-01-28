#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>. 
 
import _niclink
import niclink

import readchar

nl_instance = niclink.NicLink( 2 )

leave = 'n'
while( leave == 'n' ):
    if( nl_instance.check_for_move() ):
        # beep to indicate a move was made
        nl_instance.beep()

        # get the new board FEN
        post_move_FEN = nl_instance.get_FEN()

        try:
            # find move from the FEN change
            move = nl_instance.get_last_move()

        except RuntimeError as re:   
            print( f"{re} reset the board to the previous position an try again" )
            print( f"previous position: \n{nl_instance.game_board}" ) 
            print( "leave? ('n for no, != 'n' yes: " )
            leave = readchar.readkey()

            continue # as move will not be defined

        # make the move on the game board
        nl_instance.make_move_game_board( move )
        
        print( "=========================================" )
        

    print("leave? ('n for no, != 'n' yes: ")
    leave = readchar.readkey()

