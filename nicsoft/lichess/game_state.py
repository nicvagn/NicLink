#  NicLink-lichess is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink-lichess is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

from datetime import timedelta


class GameState:
    """A class used to contain all the information in a berserk board api game state."""

    def __init__(self, game_state: dict) -> None:
        if game_state["type"] != "gameState":
            raise ValueError(
                """'GameState instantiated with 
                             a game_state["type"] != "gameState"""
            )

        self.moves: str = game_state["moves"]
        self.wtime: timedelta = game_state["wtime"]
        self.btime: timedelta = game_state["btime"]
        self.winc: timedelta = game_state["winc"]
        self.binc: timedelta = game_state["binc"]
        self.status: str = game_state["status"]

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
