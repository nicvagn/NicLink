# NicLink Python API to EasyLink SDK

> WARN: not guarinteed to be up to date

    The main gateway that you will interact with is a class called NicLinkManeger

    it takes one required param ( refresh delay ) and one optional ( logger )
```
class NicLinkManager:
    """manage Chessnut air external board"""
 
    def __init__(self, refresh_delay, logger=None):
        """initialize the link to the chessboard, and set up NicLink"""
        if logger != None:
            self.logger = logger
            self.logger.setLevel(logging.WARN)
        else:
            self.logger = logging.getLogger()

        self.refresh_delay = refresh_delay
        # initialize the chessboard, this must be done first, before chattering at it
        self.connect()
        # this instances game board
        self.game_board = chess.Board()
        # the last move the user has played
        self.last_move = None
        # the status of the leds. We have to keep track of this
        self.led_status = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]

    def connect(self):
        """connect to the chessboard"""

    def disconnect(self) -> None:
        """disconnect from the chessboard"""

    def beep(self) -> None:
        """make the chessboard beep"""

    def set_led(self, square, status):
        """set an LED at a given square to a status (square: a1, e4 etc)"""

    def turn_off_all_leds(self):

    def get_FEN(self) -> str:
        """get the FEN from chessboard"""
    def find_move_from_FEN_change(
        self, new_FEN
    ) -> str:  # a move in quardinate notation
        """get the move that occured to change the game_board fen into a given FEN.
        return the move in coordinate notation
        """

    def check_for_move(self) -> bool:
        """check if there has been a move on the chessboard, and see if it is valid. If so update self.last_move"""

    def set_move_LEDs(self, last_move) -> None:
        """highlight the last move. Light up the origin and destination LED"""

    def await_move(self) -> str:
        """wait for a legal move, and return it in coordinate notation after making it on internal board """

    def get_last_move(self) -> str:
        """get the last move played on the chessboard"""

    def make_move_game_board(self, move) -> None:
        """make a move on the internal rep. of the game_board. update the last move made"""

    def set_board_FEN(self, board, FEN) -> None:
        """set a board up according to a FEN"""

    def set_game_board_FEN(self, FEN) -> None:
        """set the internal game board FEN"""

    def show_board_diff(self, board1, board2) -> None:
        """show the differance between two boards and output differance"""

    def show_FEN_on_board(self, FEN) -> None:
        """print a FEN on on a chessboard"""

    def show_game_board(self) -> None:
        """print the internal game_board"""

    def set_game_board(self, board) -> None:
        """set the game board"""

    def get_game_FEN(self) -> str:
        """get the game board FEN"""
        return self.game_board.fen()

    def is_game_over(
        self,
    ) -> {"over": bool, "winner": str or False, "reason": str} or False:
        """is the internal game over?"""
```
