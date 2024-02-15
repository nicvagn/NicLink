#  niclink is free software: you can redistribute it and/or modify it under the terms of the gnu general public license as published by the free software foundation, either version 3 of the license, or (at your option) any later version.
#
#  niclink is distributed in the hope that it will be useful, but without any warranty; without even the implied warranty of merchantability or fitness for a particular purpose. see the gnu general public license for more details.
#
#  you should have received a copy of the gnu general public license along with niclink. if not, see <https://www.gnu.org/licenses/>.
import _niclink
import nl_bluetooth
from nl_exceptions import NoMove, IllegalMove
import time
import chess
import readchar
import sys

import logging


class NicLinkManager:
    """manage Chessnut air external board"""

    def __init__(self, refresh_delay, logger=None, bluetooth=False):
        """initialize the link to the chessboard, and set up NicLink"""

        if logger != None:
            self.logger = logger
            self.logger.setLevel(logging.WARN)
        else:
            self.logger = logging.getLogger()

        if bluetooth:
            # connect the board w bluetooth
            self.nl_interface = nl_bluetooth
        else:
            # connect with the external board usb
            self.nl_interface = _niclink

        self.refresh_delay = refresh_delay

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

    def connect(self, bluetooth=False):
        """connect to the chessboard"""

        # connect to the chessboard, this must be done first
        self.nl_interface.connect()

        # because async programming is hard
        testFEN = self.nl_interface.getFEN()
        time.sleep(2)
        # make sure getFEN is working
        testFEN = self.nl_interface.getFEN()

        if testFEN == "" or None:
            exceptionMessage = "Board initialization error. '' or None for FEN. Is the board connected and turned on?"
            raise RuntimeError(exceptionMessage)

        self.logger.info(f"initial fen: { testFEN }")
        self.logger.info("Board initialized")

    def disconnect(self) -> None:
        """disconnect from the chessboard"""
        self.nl_interface.disconnect()
        self.logger.info("Board disconnected")

    def beep(self) -> None:
        """make the chessboard beep"""
        self.nl_interface.beep()

    def set_led(self, square, status):
        """set an LED at a given square to a status (square: a1, e4 etc)"""

        # find the file number by itteration
        files = ["a", "b", "c", "d", "e", "f", "g", "h"]
        found = False
        letter = square[0]

        file_num = 0
        while file_num < len(files):
            if letter == files[file_num]:
                found = True
                break
            file_num += 1

        # find the number by straight conversion, and some math.
        num = int(square[1]) - 1  # it's 0 based

        if not found:
            raise ValueError(f"{ square[1] } is not a valid file")

        # modify the led map to reflect this change
        if status:
            led = 1
        else:
            led = 0
        self.led_status[7 - num][file_num] = led

        # log the led status
        self.logger.info("led status after change:")
        for i in range(8):
            self.logger.info(self.led_status[i])
        # this is supper fucked, but the chessboard interaly starts counting at h8
        self.nl_interface.setLED(7 - num, 7 - file_num, status)

    def turn_off_all_leds(self):
        """turn off all the leds"""
        self.nl_interface.lightsOut()

    def get_FEN(self) -> str:
        """get the FEN from chessboard"""
        return self.nl_interface.getFEN()

    def find_move_from_FEN_change(
        self, new_FEN
    ) -> str:  # a move in quardinate notation
        """get the move that occured to change the game_board fen into a given FEN.
        return the move in coordinate notation
        """

        if new_FEN == self.game_board.board_fen():
            raise NoMove("No FEN differance")

        # get a list of the legal moves
        legal_moves = list(self.game_board.legal_moves)

        tmp_board = self.game_board.copy()
        self.logger.info(
            f"+++ find_move_from_FEN_change(...) called +++\n\
board we are using to check legal moves: \n{self.game_board}"
        )

        for move in legal_moves:
            # self.logger.info(move)
            tmp_board.push(move)  # Make the move on the board

            if (
                tmp_board.board_fen() == new_FEN
            ):  # Check if the board's FEN matches the new FEN
                self.logger.info(move)
                self.last_move = move

                return move  # Return the last move
            tmp_board.pop()  # Undo the move

        error_board = chess.Board()
        error_board.set_board_fen(new_FEN)
        message = f"\n {error_board }\nis not a possible result from a legal move on:\n{ self.game_board }"
        raise IllegalMove(message)

    def check_for_move(self) -> bool:
        """check if there has been a move on the chessboard, and see if it is valid. If so update self.last_move"""

        # ensure the move was valid

        # get current FEN on the external board
        new_FEN = self.nl_interface.getFEN()

        if new_FEN is None:
            raise ValueError("No FEN from chessboard")

        if new_FEN != self.game_board.board_fen:
            # a change has occured on the chessboard

            # check if the move is valid, and set last move
            try:
                self.last_move = self.find_move_from_FEN_change(new_FEN)
            except KeyboardInterrupt:
                self.logger.info("KeyboardInterrupt: bye")
                sys.exit(0)
            except RuntimeError as err:
                self.logger.error(err)
                self.logger.warning(
                    f"\n===== move not valid, undue it and try again. it is white's turn? { self.game_board.turn } =====\n\
board we are using to check for moves:\n{ self.game_board }"
                )
                # show the board diff from what we are checking for legal moves
                print(f"diff from board we are checking legal moves on:\n")
                current_board = chess.Board(new_FEN)
                self.show_board_diff(current_board, self.game_board)
                # pause for the refresh_delay

                time.sleep(self.refresh_delay)
                return False

            except ValueError:
                self.logger.warn("last move is None")
                return False

            return self.last_move

        else:
            self.logger.info("no change.")

        return False

    def set_move_LEDs(self, move) -> None:
        """highlight the last move. Light up the origin and destination LED"""
        # turn out move led's
        self.turn_off_all_leds()
        # make sure last move is of type str
        if type(move) != str:
            try:
                move = move.uci()
            except Exeption as err:
                message = f"{err} was raised exception on trying to convert move { move } to uci."
                self.logger.error(message)

        self.logger.info(f"led on(origin): { move[:2] }")
        self.set_led(move[:2], True)  # source
        self.logger.info(f"led on(dest): { move[2:4] }")
        self.set_led(move[2:4], True)  # dest

    def await_move(self) -> str:
        """wait for a legal move, and return it in coordinate notation after making it on internal board"""
        # loop until we get a valid move
        while True:
            # check for a move. If it move, return it else False
            try:
                move = self.check_for_move()
            except NoMove:
                # no move made, wait refresh_delay and continue
                time.sleep(self.refresh_delay)
                continue

            if move:
                # a move has been played
                self.make_move_game_board(move)
                return move

            # if no move has been played, sleep and check again
            time.sleep(self.refresh_delay)

    def get_last_move(self) -> str:
        """get the last move played on the chessboard"""
        if self.last_move is None:
            raise ValueError("ERROR: last move is None")

        return self.last_move

    def make_move_game_board(self, move) -> None:
        """make a move on the internal rep. of the game_board. update the last move made"""
        self.game_board.push(move)
        # update the last move
        self.last_move = move
        self.logger.info(
            f"made move on internal board \nBOARD POST MOVE:\n{ self.game_board }"
        )

    def set_board_FEN(self, board, FEN) -> None:
        """set a board up according to a FEN"""
        chess.Board.set_board_fen(board, fen=FEN)

    def set_game_board_FEN(self, FEN) -> None:
        """set the internal game board FEN"""
        self.set_board_FEN(self.game_board, FEN)

    def show_FEN_on_board(self, FEN) -> None:
        """print a FEN on on a chessboard"""
        board = chess.Board()
        self.set_board_FEN(board, FEN)
        print(board)

    def show_board_state(self) -> None:
        """show the state of the real world board"""
        curFEN = self.get_FEN()
        self.show_FEN_on_board(curFEN)

    def show_game_board(self) -> None:
        """print the internal game_board"""
        print(self.game_board)

    def set_game_board(self, board) -> None:
        """set the game board"""
        self.game_board = board
        self.last_move = None

    def show_board_diff(self, board1, board2) -> None:
        """show the differance between two boards and output differance"""
        for n in range(1, 9):
            for a in range(ord("a"), ord("h") + 1):
                square = chr(a) + str(n)
                py_square = chess.parse_square(square)
                if board1.piece_at(py_square) != board2.piece_at(py_square):
                    print(
                        f"Square { square } is not the same. \n board1: \
{ board1.piece_at(py_square) } \n board2: { board2.piece_at(py_square) }"
                    )
                    self.beep()
                    time.sleep(1)
                    self.beep()

    def get_game_FEN(self) -> str:
        """get the game board FEN"""
        return self.game_board.fen()

    def is_game_over(
        self,
    ) -> {"over": bool, "winner": str or False, "reason": str} or False:
        """is the internal game over?"""
        if self.game_board.is_checkmate():
            return {"over": True, "winner": self.game_board.turn, "reason": "checkmate"}
        if self.game_board.is_stalemate():
            return {"over": True, "winner": False, "reason": "Is a stalemate"}
        if self.game_board.is_insufficient_material():
            return {"over": True, "winner": False, "reason": "Is insufficient material"}
        if self.game_board.is_fivefold_repetition():
            return {"over": True, "winner": False, "reason": "Is fivefold repetition."}
        if self.game_board.is_seventyfive_moves():
            return {
                "over": True,
                "winner": False,
                "reason": "A game is automatically \
    drawn if the half-move clock since a capture or pawn move is equal to or greater than 150. Other means to end a game take precedence.",
            }

        return False


if __name__ == "__main__":
    nl_instance = NicLinkManager(2, bluetooth=False)
    nl_instance.connect()

    print("set up the board and press enter.")
    nl_instance.show_game_board()
    print("===============")
    readchar.readkey()

    leave = "n"
    while leave == "n":
        move = nl_instance.await_move()
        print(move)
