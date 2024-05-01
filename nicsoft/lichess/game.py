#  game is a part of NicLink-lichess
#
#  NicLink-lichess is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink-lichess is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

from datetime import timedelta

"""samples
correspondence:
    'game': {
     'fullId': 'aTBGIIVYsqYL',
     'gameId': 'aTBGIIVY',
     'fen': 'r4rk1/p1p1q1pp/1pb1pnn1/2N2p2/5B2/5PP1/PQ2P1BP/2RR2K1 w - - 1 22',
     'color': 'white',
     'lastMove': 'd8e7',
     'source': 'friend',
     'status': {'id': 20, 'name': 'started'},
     'variant': {'key': 'standard', 'name': 'Standard'},
     'speed': 'correspondence',
     'perf': 'correspondence',
     'rated': False,
     'hasMoved': True,
     'opponent': {'id': 'musaku', 'username': 'musaku', 'rating': 1500},
     'isMyTurn': True,
     'compat': {'bot': False, 'board': True},
     'id': 'aTBGIIVY'}

"""


class Game:
    """A class used to contain a lichess api Game, and conveiniance functions"""

    def __init__(self, game_event: dict) -> None:
        """initialize this Game"""
        logger = logging.getLogger("nl_lichess")
        logger.info("Game class created")

        self.fullId: str = game_event["fullId"]
        self.gameId: str = game_event["gameId"]
        self.id = self.gameId
        self.fen: str = game_event["fen"]
        self.colour: str = game_event["color"]
        self.lastMove: str = game_event["lastMove"]
        self.source: str = game_event["source"]
        self.status: dict = game_event["status"]
        self.variant = game_event["variant"]
        self.speed: str = game_event["speed"]
        self.perf: bool = game_event["perf"]
        self.rated: bool = game_event["rated"]
        self.opponent: dict = game_event["opponent"]
        self.isMyTurn: bool = game_event["isMyTurn"]
        if "secondsLeft" in game_event:
            self.secondsLeft: number = game_event["secondsLeft"]
        else:
            self.secondsLeft = None
        if "hasMoved" in game_event:
            self.hasMoved: bool = game_event["hasMoved"]
        else:
            self.hasMoved = "unknown"

    def __str__(self) -> str:
        """returns a partial rep. of this Game as a str"""
        return str(
            {
                "fullId": self.fullId,
                "gameId": self.gameId,
                "fen": self.fen,
                "color": self.colour,
                "status": self.status,
                "speed": self.speed,
                "hasMoved": self.hasMoved,
            }
        )

    # HACK: assumes black and white time is seconds left
    def get_wtime(self) -> timedelta:
        """get whites time from this gamestart"""
        return timedelta(seconds=self.secondsLeft)

    # HACK:
    def get_btime(self) -> timedelta:
        """get black's time from GameStart"""
        return timedelta(seconds=self.secondsLeft)

    def is_corespondance(self) -> bool:
        """is this a correspondence GameStart"""
        return self.correspondence == "True"

    def playing_white(self) -> bool:
        """are they playing white in this GameStart"""
        return self.colour == "white"

    def is_my_turn(self) -> bool:
        """is iy my turn in this GameStart"""
        return self.isMyTurn
