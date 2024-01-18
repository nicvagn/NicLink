#    This file is part of NicLink.
#
#    NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#    NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>. 

import NicLink
import time
import chess



REFRESH_DELAY = 2 #The time between checks of board for move
active_colour = 'w'

internal_chess = chess
internal_board = internal_chess.Board()


def init_chessboard():
    """ initialize chessboard """
    # connect with the external board
    NicLink.connect()
    # make sure getFEN is working
    print(NicLink.getFEN())

def find_move_from_fen_change( initial_fen, new_fen ):
    board = chess.Board(initial_fen)
    legal_moves = list(board.legal_moves)

    for move in legal_moves:
        board.push(move)  # Make the move on the board
        if board.fen() == new_fen:  # Check if the board's FEN matches the new FEN
            return move  # Return the move in Coordinate notation 
        board.pop()  # Undo the move



def check_for_move( lastFEN ):

    print("current board:")
    currentFEN = NicLink.getFEN()
    print("================")
    if( lastFEN != currentFEN and currentFEN != ''):
        #a change has occured on the chessboard
        print("CHANGE")
        move = find_move_from_fen_change(lastFEN, currentFEN)
        print(move)
        return True
       

    #the last fen becomes the current FEN
    return False

# from https://stackoverflow.com/questions/66770587/how-do-i-get-the-played-move-by-comparing-two-different-fens
nums = {1:"a", 2:"b", 3:"c", 4:"d", 5:"e", 6:"f", 7:"g", 8:"h"}
def get_uci(board1, board2, who_moved):
    str_board = str(board1).split("\n")
    str_board2 = str(board2).split("\n")
    move = ""
    flip = False
    if who_moved == "w":
        for i in range(8)[::-1]:
            for x in range(15)[::-1]:
                if str_board[i][x] != str_board2[i][x]:
                    if str_board[i][x] == "." and move == "":
                        flip = True
                    move+=str(nums.get(round(x/2)+1))+str(9-(i+1))
    else:
        for i in range(8):
            for x in range(15):
                if str_board[i][x] != str_board2[i][x]:
                    if str_board[i][x] == "." and move == "":
                        flip = True
                    move+=str(nums.get(round(x/2)+1))+str(9-(i+1))
    if flip:
        move = move[2]+move[3]+move[0]+move[1]
    return move
# ===================

init_chessboard()

currentFEN = chess.Board.starting_fen
pastFEN = chess.Board.starting_fen
while( True ):


    if( check_for_move(pastFEN) ):
        print("MOVE")
        pastFEN = currentFEN
    
    time.sleep(REFRESH_DELAY)



initial_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
new_fen = "rnbqkbnr/pppppppp/8/8/8/4P3/PPPP1PPP/RNBQKBNR b KQkq - 0 1"  # Example of a new FEN after 1. e4

move_san = find_move_from_fen_change(initial_fen, new_fen)
print(f"The move was: {move_san}")
time.sleep(REFRESH_DELAY)
