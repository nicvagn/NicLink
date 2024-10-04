#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.


class NoMove(Exception):
    """Exception raised when there is no move from chessboard (ie: the game board fen == fen from the external board)"""

    def __init__(self, message):
        self.message = message


class IllegalMove(Exception):
    """Exception raised when an illegal move is on the external board"""

    def __init__(self, message):
        self.message = message


class ExitNicLink(Exception):
    """Exception raised to quit NicLink"""

    def __init__(self, message):
        self.message = message


class NoNicLinkFen(Exception):
    """raised when fen is None"""

    def __init__(self, message):
        self.message = message


class NicLinkGameOver(Exception):
    """the game on NicLink is over"""

    def __init__(self, message):
        self.message = message


class NicLinkHandlingGame(Exception):
    """NicLink is handling a game, and the action can not be preformed"""

    def __init__(self, message):
        self.message = message
