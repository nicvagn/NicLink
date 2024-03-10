#  NicLink is free software: you can redistribute it and/or modify it under the terms of the gnu general public license as published by the free software foundation, either version 3 of the license, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but without any warranty; without even the implied warranty of merchantability or fitness for a particular purpose. see the gnu general public license for more details.
#
#  you should have received a copy of the gnu general public license along with NicLink. if not, see <https://www.gnu.org/licenses/>.

# get the dir this script is in, and add it to the path. For importing the _niclink file. Yes, I know it is a hack, but Fuck ME 
import os
import sys
import time
import chess
import readchar
import threading
import logging

script_dir = os.path.dirname(__file__)
sys.path.append(script_dir)

import _niclink
import nl_bluetooth
from nl_exceptions import *

#  === exception logging ===
# log unhandled exceptions to the log file
def log_except_hook(excType, excValue, traceback):
    global logger
    logger.error("Uncaught exception", exc_info=(excType, excValue, traceback))
sys.excepthook = log_except_hook

def log_handled_exeption(exception: Exception) -> None:
    """log a handled exception"""
    logger.error("Exception handled: %s", exception)


class NicLinkManager(threading.Thread):
    """manage Chessnut air external board in it's own thread"""

    def __init__(self, refresh_delay, logger=None, bluetooth=False):
        """initialize the link to the chessboard, and set up NicLink"""

        # initialize the thread, as a daemon
        threading.Thread.__init__(self, daemon=True)

        if logger != None:
            self.logger = logger
        else:
            self.logger = logging.getLogger()
            self.logger.setLevel(logging.ERROR)

        if bluetooth:
            # connect the board w bluetooth
            self.nl_interface = nl_bluetooth
        else:
            # connect with the external board usb
            self.nl_interface = _niclink

        self.refresh_delay = refresh_delay

        self.connect()
        # set NicLink values to defaults
        self.reset()
        """
        IE:
        ### Treading Events ###
        # a way to kill the program from outside
        self.game_over = threading.Event()
        self.has_moved = threading.Event()
        self.kill_switch = threading.Event()
        self.start_game = threading.Event()
        """

        ### threading lock ###
        # used for access to critical vars to provent race conditions and such
        self.lock = threading.Lock()

    def run(self):
        """run and wait for a game to begin"""
        # run while kill_switch is not set
        while not self.kill_switch.is_set():
            if self.start_game.is_set():
                self.logger.info("_run_game is set. (run)")
                self._run_game()
            time.sleep(self.refresh_delay)

        # disconnect from board
        self.disconnect()

        raise ExitNicLink("Thank you for using NicLink")

    def _run_game(self):
        """handle a chessgame over NicLink"""

        # run a game
        while not self.game_over.is_set() and not self.kill_switch.is_set():

            exit = "n"
            while exit == "n":
                currentFEN = self.get_FEN()
                self.show_FEN_on_board(currentFEN)
                print("do you want to exit? 'n' for no \n")
                exit = readchar.readkey()

            self.logger.info(f"move made: {self.last_move}")
            # set the has moved flag to signal the move
            self.has_moved.set()
            time.sleep(self.refresh_delay)

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

    def reset(self) -> None:
        """reset NicLink"""
        # this instances game board
        self.game_board = chess.Board()
        # the last move the user has played
        self.last_move = None
        # turn off all the lights
        self.turn_off_all_leds()

        ### Treading Events ###
        # a way to kill the program from outside
        self.game_over = threading.Event()
        self.has_moved = threading.Event()
        self.kill_switch = threading.Event()
        self.start_game = threading.Event()

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

        # this is supper fucked, but the chessboard interaly starts counting at h8
        self.nl_interface.setLED(7 - num, 7 - file_num, status)

    def turn_off_all_leds(self):
        """turn off all the leds"""
        self.nl_interface.lightsOut()

    def get_FEN(self) -> str:
        """get the board FEN from chessboard"""
        return self.nl_interface.getFEN()

    def show_board_FEN_on_board(self, boardFEN):
        """show just the board part of FEN on asci chessboard"""
        tmp_board = chess.Board()
        tmp_board.set_board_fen(boardFEN)
        print(tmp_board)

    def find_move_from_FEN_change(
        self, new_FEN
    ) -> str:  # a move in quardinate notation
        """get the move that occured to change the game_board fen into a given FEN.
        return the move in coordinate notation
        """
        old_FEN = self.game_board.board_fen()
        if new_FEN == old_FEN:
            print("no fen differance")
            self.turn_off_all_leds()
            raise NoMove("No FEN differance")

        self.logger.debug("new_FEN" + new_FEN)
        self.logger.debug("old FEN" + old_FEN)

        # get a list of the legal moves
        legal_moves = list(self.game_board.legal_moves)

        tmp_board = self.game_board.copy()
        self.logger.info(
            "+++ find_move_from_FEN_change(...) called +++\n\
current board: \n%s\n board we are using to check legal moves: \n%s",
            self.show_board_FEN_on_board(self.get_FEN()),
            self.game_board,
        )

        for move in legal_moves:
            # self.logger.info(move)
            tmp_board.push(move)  # Make the move on the board

            if (
                tmp_board.board_fen() == new_FEN
            ):  # Check if the board's FEN matches the new FEN
                self.logger.info(move)

                return move  # Return the last move

            tmp_board.pop()  # Undo the move and try another

        error_board = chess.Board()
        error_board.set_board_fen(new_FEN)
        self.show_board_diff(error_board, self.game_board)
        message = f"Board we see:\n{ error_board }\nis not a possible result from a legal move on:\n{ self.game_board }"
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
                log_handled_exeption(err)
                self.logger.warning(
                    "\n===== move not valid, undue it and try again. it is white's turn? %s =====\n\
board we are using to check for moves:\n%s",
                    self.game_board.turn,
                    self.game_board,
                )
                # show the board diff from what we are checking for legal moves
                print(f"diff from board we are checking legal moves on:\n")
                current_board = chess.Board(new_FEN)
                self.show_board_diff(current_board, self.game_board)
                # pause for the refresh_delay

                time.sleep(self.refresh_delay)
                return False

            except ValueError:
                self.logger.warn("self.find_move_from_FEN_change(new_FEN) returned None. No move was found.")
                return False
            with self.lock:
                return self.last_move

        else:
            self.logger.info("no change.")

        return False

    def set_move_LEDs(self, move) -> None:
        """highlight a move. Light up the origin and destination LED"""
        # turn out move led's
        self.turn_off_all_leds()
        # make sure move is of type str
        if type(move) != str:
            try:
                move = move.uci()
            except Exeption as err:
                message = f"{err} was raised exception on trying to convert move { move } to uci."
                self.logger.error(message)

        self.logger.info("led on(origin): %s", move[:2])
        self.set_led(move[:2], True)  # source

        self.logger.info("led on(dest): %s", move[2:4])
        self.set_led(move[2:4], True)  # dest

    def await_move(self) -> str:
        """wait for legal move, and return it in coordinate notation after making it on internal board"""
        # loop until we get a valid move
        attempts = 0
        while not self.game_over.is_set() and not self.kill_switch.is_set():
            self.logger.info(
                "is game_over threading event set? %s", self.game_over.is_set()
            )
            # check for a move. If it move, return it else False
            try:
                if self.check_for_move():
                    move = self.get_last_move()
            except NoMove:
                # no move made, wait refresh_delay and continue
                attempts += 1
                self.logger.info("NoMove from chessboard. Attempt: %s", attempts)
                time.sleep(self.refresh_delay)

                continue

            except IllegalMove as err:
                # IllegalMove made, waiting then trying again
                attempts += 1
                self.logger.error(
                    "\n %s | waiting refresh_delay= %s and checking again.\n",
                    err,
                    self.refresh_delay,
                )
                time.sleep(self.refresh_delay)
                continue

            self.logger.info("move %s made.", move)
            # a move has been played
            self.make_move_game_board(move)
            self.logger.info("move detected and made on gameboard. move %s", move)
            return move

            # if no move has been played, sleep and check again
            time.sleep(self.refresh_delay)

    def get_last_move(self) -> str:
        """get the last move played on the chessboard"""
        with self.lock:
            if self.last_move is None:
                raise ValueError("ERROR: last move is None")

            return self.last_move

    def make_move_game_board(self, move) -> None:
        """make a move on the internal rep. of the game_board. update the last move made"""
        self.game_board.push(move)
        # update the last move
        self.last_move = move
        self.logger.info(
            "made move on internal board, BOARD POST MOVE:\n%s", self.game_board
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
        with self.lock:
            self.game_board = board

    def gameover_lights(self) -> None:
        """show some fireworks"""
        self.nl_interface.gameover_lights()

    def show_board_diff(self, board1, board2) -> None:
        """show the differance between two boards and output differance on the chessboard"""
        # go through the squares and turn on the light for ones that are in error
        self.nl_interface.lightsOut()
        is_diff = False
        for n in range(1, 9):
            for a in range(ord("a"), ord("h") + 1):
                square = chr(a) + str(n)
                py_square = chess.parse_square(square)
                if board1.piece_at(py_square) != board2.piece_at(py_square):
                    print(
                        f"\n\nSquare { square } is not the same. \n board1: \
{ board1.piece_at(py_square) } \n board2: { board2.piece_at(py_square) }"
                    )
                    self.set_led(square, True)
                    is_diff = True
        # if there is a diff beep
        if is_diff:
            self.beep()
        else:
            # set the last move leds
            self.set_move_LEDs(self.get_last_move())

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

def test_bt():
    """test nl_bluetooth"""

    nl_instance = NicLinkManager(2, bluetooth=True)
    nl_instance.connect()


def test_usb():
    """test usb connection"""

    nl_instance = NicLinkManager(2)
    nl_instance.connect()
    print("(test usb connection) set up the board and press enter.")
    nl_instance.show_game_board()
    print("===============")
    readchar.readkey()

    leave = "n"
    while leave == "n":
        nl_instance.gameover_lights()
        move = nl_instance.await_move()
        print(move)


if __name__ == "__main__":
    # test_bt()
    test_usb()
    pass
