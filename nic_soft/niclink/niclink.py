#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>. 
import _niclink
from _niclink import connect, disconnect, uploadMode, realTimeMode, getFEN, setLED, beep
import time
import chess
import copy
import readchar


class NicLink:
    """ manage Chessnut air external board """
    
    def __init__( self, refresh_delay ):
        """ initialize the link to the chessboard, and set up NicLink """
        self.refresh_delay = refresh_delay
        # initialize the chessboard, this must be done first, before chattering at it
        self.connect()
        # this instances game board
        self.game_board = chess.Board()

    def connect( self ):
        """ connect to the chessboard """
        # connect with the external board
        _niclink.connect()
        # make sure getFEN is working
        print(f"initial fen: { _niclink.getFEN() }")
        print("Board initialized")


    def beep( self ):
        """ make the chessboard beep """
        _niclink.beep()

    def get_FEN():
        """ get the FEN from chessboard """
        return _niclink.getFEN();


    def find_move_from_FEN_change( self, new_FEN ):
        """ get the move that occured to change the game_board fen into a given FEN. 
            move returned in coordinate notation """

        # get a list of the legal moves
        legal_moves = list(self.game_board.legal_moves)
        
        print(f"board now: \n{ self.game_board }")
        tmp_board = self.game_board.copy()
        print(f"board we are using to check legal moves: \n{self.game_board}")

        for move in legal_moves:
            #print(move)
            #breakpoint()
            tmp_board.push( move )  # Make the move on the board
            if tmp_board.board_fen() == new_FEN:  # Check if the board's FEN matches the new FEN
                return move  # Return the move in Coordinate notation 
            tmp_board.pop()  # Undo the move

        raise RuntimeError("a valid move was not made")


    def check_for_move( self ):
        """ check if there has been a move on the chessboard, and see if it is valid """

        # ensure the move was valid

        # get current FEN on the external board
        tmpFEN = _niclink.getFEN()

        if(tmpFEN is None):
            raise RuntimeError("No FEN from chessboard")

        new_FEN = tmpFEN
        
        if( new_FEN != self.game_board.board_fen ):
            # a change has occured on the chessboard
            print(f"board prior to move: \n{self.game_board}\n")
            return True

        else:
            print("no change")
        return False

    def make_move_game_board( self, move ):
        """ make a move on the internal rep. of the game_board, move in long algebraic notation """
        self.game_board.push_uci( move )
        print( "made move on internal board\n BOARD POST MOVE: \n" )
        print( self.game_board )


    def set_board_FEN( self, board, FEN ):
        """ set a board up according to a FEN """
        chess.Board.set_board_fen( board, fen=FEN)


    def show_FEN_on_board( self, FEN ):
        """ print a FEN on on a chessboard """
        board = chess.Board()
        self.set_FEN_on_board( board, FEN )
        print( board )


# if module is on "top level" ie: run directly
if __name__ == '__main__':
    nl_instance = NicLink( 2 )

    leave = 'n' 
    while( leave == 'n' ):
        if( nl_instance.check_for_move() ):
            # beep to indicate a move was made
            nl_instance.beep()

            # get the new board FEN
            post_move_FEN = nl_instance.get_FEN()

            # show new fen on board
            print( "post move fen on board" )
            nl_instance.show_FEN_on_board( post_move_FEN )

            try:
                # find move from the FEN change
                move = nl_instance.find_move_from_FEN_change( post_move_FEN )

            except RuntimeError as re:   
                print( re + " reset the board to the privios position an try again" )
            
            # make the move on the game board
            nl_instance.make_move_game_board( move )
            
            print( "=========================================" )
            

        print("leave? ('n for no, != 'n' yes: ")
        leave = readchar.readkey()

