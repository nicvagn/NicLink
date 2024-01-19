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



REFRESH_DELAY = 3 #The time between checks of board for move
active_colour = 'w'



def init_chessboard():
    """ initialize chessboard """
    # connect with the external board
    NicLink.connect()
    # make sure getFEN is working
    print(f"initial fen: { NicLink.getFEN() }")
    print("Board initialized")

def find_move_from_fen_change( initial_fen, new_fen ):

    """ get the move that occured to change one fen into another """ 
    board = chess.Board(initial_fen)
    legal_moves = list(board.legal_moves)

    print(f"board we are using to check legal moves: \n{board}")

    for move in legal_moves:
        print(move)
        breakpoint()
        board.push(move)  # Make the move on the board
        if board.board_fen() == new_fen:  # Check if the board's FEN matches the new FEN
            return move  # Return the move in Coordinate notation 
        board.pop()  # Undo the move

    raise RuntimeError("a valid move was not made")



def check_for_move():
    """ check if there has been a move on the chessboard, and see if it is valid """
    global pastFEN, currentFEN

    # ensure the move was valid
    tmpFEN = NicLink.getFEN()
    if(tmpFEN == None):
        raise RuntimeError("No FEN from chessboard")

    currentFEN = tmpFEN
    print(f"board now: \n {chess.Board(currentFEN)}")
    find_move_from_fen_change(pastFEN, currentFEN)
    
    if( pastFEN != currentFEN and currentFEN != ''):
        # a change has occured on the chessboard
        print("CHANGE")
        print(f"past fen: \n {pastFEN}\n")
        print(f"current fen: \n {currentFEN}\n")

        #check if move is valid
        move = find_move_from_fen_change(pastFEN, currentFEN)
        if( move != None and move != ''):
            # if it is a valid move, return true
            print(move)
            #the last fen becomes the current FEN
            pastFEN = currentFEN
            return True
    return False

def print_FEN( FEN ):
    """ print a FEN on on a chessboard """
    board = chess.Board()
    chess.Board.set_board_fen( board, fen=FEN)
    print( board )

# initialize the chessboard, this must be done first, before chattering at it
init_chessboard()

# initial values for fen's
currentFEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
pastFEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"

while( True ):
    print("print FEN test")
    print_FEN( "rnbqkbnr/pppppppp/8/8/8/4P3/PPPP1PPP/RNBQKBNR")
    try:
        if( check_for_move() ):
            print("change in board.")
            print(f"past fen: \n {pastFEN}\n")
            print(f"current fen: \n {currentFEN}\n")

            if(pastFEN == ''):
                #print("pastFEN is ''")
                pass
            elif(currentFEN == ''):
                #print("currentFEN is ''")
                pass
            else:
                move = find_move_from_fen_change( pastFEN, currentFEN )
                print(f"Move was: {move}.")

    except (RuntimeError, ValueError) as err:
        print(err)
        continue # pass onto the next loop iteration, skipping the rest of the loop 

    pastFEN = currentFEN
    
    print(f"====== {currentFEN} ======")
    time.sleep(REFRESH_DELAY)



"""
initial_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
new_fen = "rnbqkbnr/pppppppp/8/8/8/4P3/PPPP1PPP/RNBQKBNR b KQkq - 0 1"  # Example of a new FEN after 1. e4

move_san = find_move_from_fen_change(initial_fen, new_fen)
print(f"The move was: {move_san}")
time.sleep(REFRESH_DELAY)
"""
