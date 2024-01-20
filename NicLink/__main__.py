#    This file is part of NicLink.
#
#    NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#    NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>. 

import NicLink
from NicLink import *
import time
import chess



REFRESH_DELAY = 7 #The time between checks of board for move

game_board = chess.Board()



def init_chessboard():
    """ initialize chessboard """
    # connect with the external board
    NicLink.connect()
    # make sure getFEN is working
    print(f"initial fen: { NicLink.getFEN() }")
    print("Board initialized")

def find_move_from_fen_change( new_FEN ):
    """ get the move that occured to change one fen into another """
    global game_board

    # get a list of the legal moves
    legal_moves = list(game_board.legal_moves)

    print(f"board now: \n{ game_board }")
    print(f"board we are using to check legal moves: \n{game_board}")

    for move in legal_moves:
        print(move)
        #breakpoint()
        game_board.push(move)  # Make the move on the board
        if game_board.board_fen() == new_FEN:  # Check if the board's FEN matches the new FEN
            return move  # Return the move in Coordinate notation 
        game_board.pop()  # Undo the move

    raise RuntimeError("a valid move was not made")



def check_for_move():
    """ check if there has been a move on the chessboard, and see if it is valid """
    global game_board

    # ensure the move was valid

    # get current FEN on the external board
    tmpFEN = NicLink.getFEN()

    if(tmpFEN == None):
        raise RuntimeError("No FEN from chessboard")

    new_FEN = tmpFEN
    
    if( new_FEN != game_board.board_fen ):
        # a change has occured on the chessboard
        print("CHANGE")
        print(f"board now: \n{game_board}\n")

        #check if move is valid
        move = find_move_from_fen_change( new_FEN )
        if( move != None and move != ''):
            # if it is a valid move, return true
            print(f"{move} is it the move")
            # the last fen becomes the current FEN
            pastFEN = new_FEN
            # change the active colour
            
            return True
    else:
        print("no change")
    return False

def print_FEN( FEN ):
    """ print a FEN on on a chessboard """
    board = chess.Board()
    chess.Board.set_board_fen( board, fen=FEN)
    print( board )


# initialize the chessboard, this must be done first, before chattering at it
init_chessboard()

# initial values for fen's
newFEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"

while( True ):
    #print_FEN( "rnbqkbnr/pppppppp/8/8/8/4P3/PPPP1PPP/RNBQKBNR")
    try:
        if( check_for_move() ):
            print("change in board.")
            print(f"new fen: \n {newFEN}\n")

            if(newFEN == '' or newFEN == None):
                print("pastFEN is None")
                pass
            else:
                move = find_move_from_fen_change( pastFEN, currentFEN )
                print(f"Move was: {move}.")

    except (RuntimeError, ValueError) as err:
        print(err)

    
    # print(f"====== {currentFEN} ======")
    time.sleep(REFRESH_DELAY)
    NicLink.beep()
