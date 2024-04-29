#  NicLink-lichess is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink-lichess is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

from typing import TypedDict

from game import Game

"""sample

{'type': 'gameStart',
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
    }
"""


class GameStart(TypedDict):
    """A class used to contain all the information in a berserk board api game start"""

    type: str
    game: Game
