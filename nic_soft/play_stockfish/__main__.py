#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

# sys stuff
import sys
import time
import logging
import logging.handlers
import os
import sys
import argparse
import threading
import importlib
import readchar

# chess stuff
import chess.pgn
import chess

# NicLink shit
from niclink import NicLinkManager
# the fish
from stockfish import Stockfish

logger = logging.getLogger( "NicLin" )
print( logging.INFO )
logger.setLevel( logging.INFO )
print(logger)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
print(ch)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

class Game(threading.Thread):
    """ a chessgame with stockfish handled in it's own thread """

    def __init__(self, NicLinkManager, playing_white, stockfish_level=5, **kwargs ):
        super().__init__(**kwargs)
        self.nl_inst = NicLinkManager
        # bool of if your playing white
        self.playing_white = playing_white
        # init stockfish
        self.fish = Stockfish()
        self.fish.set_skill_level( stockfish_level )
        # list of all the game moves
        self.moves = []
        # is the game over?
        self.game_over = False
        # current state of the game board
        self.board = chess.Board()

    def handle_human_turn(self) -> None:
        """ Handle a human turn in the game """

        logger.info("it is our turn")

        try:
            move = self.nl_inst.await_move()  # await move from e-board the move from niclink
            print( f"move from board: { move }" )
        except ValueError:
            print("no move gotten from board, passing")
            return

        logger.info(f"move from chessboard { move }")

    
    def handle_fish_turn( self ) -> None:
        """ handle fish's turn """
        logger.info( "Fish's turn" )
        self.fish.set_fen_position(self.board.fen())

        # get stockfishes move
        fish_move = self.fish.get_best_move()
        logger.info( f"Fish's move { fish_move }" )

        self.board.push_uci( fish_move )

    def start( self ) -> None:
        """ start playing the game """

        self.run()


    def run( self ) -> None:
        """ run the game thread """

        while( not self.game_over ):
            if( self.playing_white ):
                # if we go first, go first
                self.handle_human_turn()            


            # do the fish turn
            self.handle_fish_turn()


            # if we are playing white, skip to next iter
            if( self.playing_white ):
                continue
            # case we are black
            self.handle_human_turn()




def main():
    print( logging.INFO )
    logger.setLevel( logging.INFO )
    # and a NicLinkManager
    nl_inst = NicLinkManager( refresh_delay=2 ) # logger=logger )
    
    print( "Do you want to play white? (y/n)" )
    playing_w = readchar.readkey()
    playing_white = ( playing_w == 'y' ) 


    game = Game(nl_inst, playing_white )

    game.start()



if __name__ == "__main__":
    main()
