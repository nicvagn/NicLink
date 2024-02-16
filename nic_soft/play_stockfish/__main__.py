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

# debbuging
import pdb
import traceback

# chess stuff
import chess.pgn
import chess

# NicLink shit
from niclink import NicLinkManager

# the fish
from stockfish import Stockfish

logger = logging.getLogger("NL play Fish")
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter("%(name)s - %(levelname)s | %(message)s")

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


class Game(threading.Thread):
    """a chessgame with stockfish handled in it's own thread"""

    def __init__(
        self, NicLinkManager, playing_white, stockfish_level=5, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.nl_inst = NicLinkManager
        # bool of if your playing white
        self.playing_white = playing_white
        # init stockfish
        self.fish = Stockfish()
        self.fish.set_skill_level(stockfish_level)
        # list of all the game moves
        self.moves = []
        # is the game over?
        self.game_over = False

    def check_for_game_over(self) -> None:
        """check if the game is over"""
        # is_game_over() will return False or a dictionary with:
        # {"over": bool, "winner": str or False, "reason": str}
        over_state = self.nl_inst.is_game_over()
        if not over_state:
            # the game is still going
            return
        # otherwise, tell the user and exit
        if over_state["winner"]:
            winner = "Black"
        else:
            winner = "White"
        print(
            f"Winner: { winner } reason: {over_state['reason']} \n \
have a nice day."
        )

        sys.exit(0)

    def handle_human_turn(self) -> None:
        """Handle a human turn in the game"""
        global logger 
        logger.info("\n--- human turn ---\n")

        try:
            move = (
                self.nl_inst.await_move()
            )  # await move from e-board the move from niclink
            print(f"move from board: { move }")
        except KeyboardInterrupt:
            print("Bye!")
            sys.exit(0)


        logger.info(f"move from chessboard { move }")

        # check if the game is done
        self.check_for_game_over()

    def handle_fish_turn(self) -> None:
        """handle fish's turn"""
        global logger
        logger.info("Fish's turn")
        self.fish.set_fen_position(self.nl_inst.get_game_FEN())

        # get stockfishes move
        fish_move = chess.Move.from_uci(self.fish.get_best_move())
        logger.info(f"Fish's move { fish_move }")

        # make move on the niclink internal board
        self.nl_inst.make_move_game_board(fish_move)
        self.nl_inst.set_move_LEDs(fish_move)

        print(f"board after fish turn:")
        self.nl_inst.show_game_board()

        # check for game over
        self.check_for_game_over()


    def start(self) -> None:
        """start playing the game"""

        # start by turning off all the lights
        self.nl_inst.turn_off_all_leds()

        self.run()

    def run(self) -> None:
        """run the game thread"""

       # main game loop
        while True:
            if self.playing_white:
                # if we go first, go first
                self.handle_human_turn()

            # do the fish turn
            self.handle_fish_turn()

            if not self.playing_white:
                # case we are black
                self.handle_human_turn()


def main():
    # NicLinkManager
    nl_inst = NicLinkManager(refresh_delay=2, logger=logger)

    nl_inst.connect()

    print("\n%%%%%% NicLink vs Stockfish %%%%%%\n")

    print("What level do you want for the fish? (1 - 33) for info enter i, else level")

    while True:
        sf_lvl = input("level (1 - 33):")
        if sf_lvl == "i":
            print(
                """I found this online, and stole it:

Stockfish 16 UCI_Elo was calibrated with CCRL.

   # PLAYER             :  RATING  ERROR  POINTS  PLAYED   (%)
   1 master-skill-19    :  3191.1   40.4   940.0    1707    55
   2 master-skill-18    :  3170.3   39.3  1343.0    2519    53
   3 master-skill-17    :  3141.3   37.8  2282.0    4422    52
   4 master-skill-16    :  3111.2   37.1  2773.0    5423    51
   5 master-skill-15    :  3069.5   37.2  2728.5    5386    51
   6 master-skill-14    :  3024.8   36.1  2702.0    5339    51
   7 master-skill-13    :  2972.9   35.4  2645.5    5263    50
   8 master-skill-12    :  2923.1   35.0  2653.5    5165    51
   9 master-skill-11    :  2855.5   33.6  2524.0    5081    50
  10 master-skill-10    :  2788.3   32.0  2724.5    5511    49
  11 stash-bot-v25.0    :  2744.0   31.5  1952.5    3840    51
  12 master-skill-9     :  2702.8   30.5  2670.0    5018    53
  13 master-skill-8     :  2596.2   28.5  2669.5    4975    54
  14 stash-bot-v21.0    :  2561.2   30.0  1338.0    3366    40
  15 master-skill-7     :  2499.5   28.5  1934.0    4178    46
  16 stash-bot-v20.0    :  2452.6   27.7  1606.5    3378    48
  17 stash-bot-v19.0    :  2425.3   26.7  1787.0    3365    53
  18 master-skill-6     :  2363.2   26.4  2510.5    4379    57
  19 stash-bot-v17.0    :  2280.7   25.4  2209.0    4378    50
  20 master-skill-5     :  2203.7   25.3  2859.5    5422    53
  21 stash-bot-v15.3    :  2200.0   25.4  1757.0    4383    40
  22 stash-bot-v14      :  2145.9   25.5  2890.0    5167    56
  23 stash-bot-v13      :  2042.7   25.8  2263.5    4363    52
  24 stash-bot-v12      :  1963.4   25.8  1769.5    4210    42
  25 master-skill-4     :  1922.9   25.9  2690.0    5399    50
  26 stash-bot-v11      :  1873.0   26.3  2203.5    4335    51
  27 stash-bot-v10      :  1783.8   27.8  2568.5    4301    60
  28 master-skill-3     :  1742.3   27.8  1909.5    4439    43
  29 master-skill-2     :  1608.4   29.4  2064.5    4389    47
  30 stash-bot-v9       :  1582.6   30.2  2130.0    4230    50
  31 master-skill-1     :  1467.6   31.3  2015.5    4244    47
  32 stash-bot-v8       :  1452.8   31.5  1953.5    3780    52
  33 master-skill-0     :  1320.1   32.9   651.5    2083    31

credit: https://chess.stackexchange.com/users/25998/eric\n"""
            )
            continue

        if int(sf_lvl) > 0 and int(sf_lvl) <= 33:
            break

        else:
            print("invalid. Try again")
            continue

    print("Do you want to play white? (y/n)")
    playing_w = readchar.readkey()
    playing_white = playing_w == "y"

    game = Game(nl_inst, playing_white, stockfish_level=sf_lvl)
    print("game started")
    if playing_white:
        print("make a move please")
    game.start()


if __name__ == "__main__":
    main()
