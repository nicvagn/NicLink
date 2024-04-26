#  NicLink-lichess is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink-lichess is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.


"""sample

{'fullId': 'V272Z7t1PcgG',
 'gameId': 'V272Z7t1',
 'fen': 'rnbqkb1r/pp3ppp/3p1n2/2p1p3/2P1P3/2N2N2/PP1P1PPP/R1BQKB1R w KQkq - 0 5',
 'color': 'white',
 'lastMove': 'e7e5',
 'source': 'lobby',
 'status': {'id': 20, 'name': 'started'},
 'variant': {'key': 'standard', 'name': 'Standard'},
 'speed': 'correspondence',
 'perf': 'correspondence',
 'rated': True, 'hasMoved': True,
 'opponent': {'id': 'caleb-isaac-leiva',
              'username': 'Caleb-Isaac-Leiva',
              'rating': 1500},
 'isMyTurn': True,
 'secondsLeft': 1205340}

"""


class GameStart:
    """A class used to contain all the information in a berserk board api game start."""

    def __init__(self, game_start: dict) -> None:
        """initialize this GameStart from berserk dict"""
        self.fullId = game_start["fullId"]
        self.gameId = game_start["gameId"]
        self.fen = game_start["fen"]
        self.colour = game_start["color"]
        self.lastMove = game_start["lastMove"]
        self.source = game_start["source"]
        self.status = game_start["status"]
        self.variant = game_start["variant"]
        self.speed = game_start["speed"]
        self.perf = game_start["perf"]
        self.rated = game_start["rated"]
        self.opponent = game_start["opponent"]
        self.isMyTurn = game_start["isMyTurn"]
        self.secondsLeft = game_start["secondsLeft"]
