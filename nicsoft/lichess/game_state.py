#  NicLink-lichess is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink-lichess is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

from datetime import timedelta
from typing import List

""" some exceptions """


class NoMoves(Exception):
    """raised when GameState has no moves"""

    def __init__(self, message):
        self.message = message


class GameState:
    """A class used to contain all the information in a berserk board api game state."""

    def __init__(self, game_state: dict) -> None:
        # TODO: FIND OUT HOW EXPENSIVE THIS IS
        self.logger = logging.getLogger("nl_lichess")

        self.logger.info(
            "GameState: gs created w game_state: dict -> %s \n -------- \n", game_state
        )
        if game_state["type"] != "gameState":
            raise ValueError(
                """'GameState instantiated with 
                             a game_state["type"] != "gameState"""
            )

        self.moves: List[str] = game_state["moves"].split(" ")
        self.wtime: timedelta = game_state["wtime"]
        self.btime: timedelta = game_state["btime"]
        self.winc: timedelta = game_state["winc"]
        self.binc: timedelta = game_state["binc"]
        self.status: str = game_state["status"]

        if "winner" in game_state:
            self.winner: str = game_state["winner"]
        else:
            self.winner = False

    def has_moves(self) -> bool:
        """does this game state have any moves? ie: moves was not ''
        @returns: (bool) does this gamestate have any moves?"""
        return self.moves != [""]

    def get_moves(self) -> List[str]:
        """get the moves from this GameState in an array"""
        return self.moves

    def get_last_move(self) -> str:
        """get the last move in uci"""
        if self.has_moves():
            return self.moves[-1]
        else:
            raise NoMoves("no moves in this GameState")

    def first_move(self) -> bool:
        """does this gamestate have two moves?
        @returns: (bool) is first move
        """
        if len(self.moves) < 2:
            return True
        return False

    def is_white_to_move(self) -> bool:
        """is white to move in this gamestate
        @returns: (bool) if it is whites move
        """
        if self.has_moves():
            # if odd number of moves, black to move
            return len(self.moves) % 2 == 0
        else:
            # if there are no moves, it is white to move
            return True

    def get_wtime(self) -> timedelta:
        """get white's time from this GameState"""
        return self.wtime

    def get_btime(self) -> timedelta:
        """get black's time from this GamState"""
        return self.btime

    def get_winc(self) -> timedelta:
        """get white's incriment from this GameState"""
        return self.winc

    def get_binc(self) -> timedelta:
        """get black's incriment from this GameState"""
        return self.winc

    def get_status(self) -> str:
        """get the status from this GameState"""
        return self.status

    def __str__(self) -> str:
        return f"GameState, Moves: { self.moves }, status: {self.status},\n \
                wtime: { self.wtime } btime: { self.btime }"
