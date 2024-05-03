#  NicLink is free software: you can redistribute it and/or modify it under the terms of the gnu general public license as published by the free software foundation, either version 3 of the license, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but without any warranty; without even the implied warranty of merchantability or fitness for a particular purpose. see the gnu general public license for more details.
#
#  you should have received a copy of the gnu general public license along with NicLink. if not, see <https://www.gnu.org/licenses/>.


import logging

# system
import sys
import threading
import time

# type hints
from numbers import Number

# pip libraries
import chess
import numpy as np
import readchar

# mine
import niclink._niclink as _niclink
import niclink.nl_bluetooth
from niclink.nl_exceptions import *

### CONSTANTS ###
ONES = np.array(
    [
        "11111111",
        "11111111",
        "11111111",
        "11111111",
        "11111111",
        "11111111",
        "11111111",
        "11111111",
    ],
    dtype=np.str_,
)
ZEROS = np.array(
    [
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
        "00000000",
    ],
    dtype=np.str_,
)

FILES = np.array(["a", "b", "c", "d", "e", "f", "g", "h"])

NO_MOVE_DELAY = 0.8

LIGHT_THREAD_DELAY = 0.5


class NicLinkManager(threading.Thread):
    """manage Chessnut air external board in it's own thread"""

    def __init__(
        self,
        refresh_delay: Number,
        thread_sleep_delay=1,
        logger: logging.Logger = None,
        bluetooth: bool = False,
    ):
        """initialize the link to the chessboard, and set up NicLink"""

        # initialize the thread, as a daemon
        threading.Thread.__init__(self, daemon=True)

        # HACK: delay for how long threads should sleep, alowing other threads to work
        self.thread_sleep_delay = thread_sleep_delay

        if logger != None:
            self.logger = logger
        else:
            self.logger = logging.getLogger("niclink")
            self.logger.setLevel(logging.ERROR)
            self.logger.error("niclink made it's own logger")

        if bluetooth:
            # connect the board w bluetooth
            self.nl_interface = niclink.nl_bluetooth
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
        # used for access to critical vars to provent race conditions
        # and such
        self.lock = threading.Lock()

        self.led_map = np.zeros((8, 8), dtype=np.str_)

    def run(self):
        """run and wait for a game to begin"""
        # run while kill_switch is not set
        while not self.kill_switch.is_set():
            if self.start_game.is_set():
                self.logger.info("_run_game is set. (run)")
                self._run_game()
            time.sleep(self.thread_sleep_delay)

        # disconnect from board
        self.disconnect()

        raise ExitNicLink("Thank you for using NicLink (raised in NicLinkManager.run()")

    def _run_game(self):
        """handle a chessgame over NicLink"""
        # run a game, ie wait for GemeOver event
        self.game_over.wait()
        # game is over, reset NicLink
        self.reset()
        self.logger.info("_run_game(...): game_over event set, resetting NicLink")

    def connect(self, bluetooth: bool = False):
        """connect to the chessboard
        @param: bluetooth - should we use bluetooth
        """
        # connect to the chessboard, this must be done first
        self.nl_interface.connect()

        # because async programming is hard
        testFEN = self.nl_interface.get_FEN()
        time.sleep(self.thread_sleep_delay)
        # make sure get_FEN is working
        testFEN = self.nl_interface.get_FEN()

        if testFEN == "" or None:
            exceptionMessage = "Board initialization error. '' or None for FEN.  \
Is the board connected and turned on?"
            raise RuntimeError(exceptionMessage)

        self.logger.info(f"Board initialized: initial fen: { testFEN }\n")

    def disconnect(self) -> None:
        """disconnect from the chessboard"""
        self.nl_interface.disconnect()
        self.logger.info("\n-- Board disconnected --\n")

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
        self.turn_off_all_LEDs()

        ### Treading Events ###
        # a way to kill the program from outside
        self.game_over = threading.Event()
        self.has_moved = threading.Event()
        self.kill_switch = threading.Event()
        self.start_game = threading.Event()

        self.logger.info("NicLinkManager reset\n")

    def set_led(self, square: str, status: bool):
        """set an LED at a given square to a status
        @param: square (square: a1, e4 etc)
        @param: status: True | False
        """
        global FILES

        # find the file number by itteration
        found = False
        letter = square[0]

        file_num = 0
        while file_num < 8:
            if letter == FILES[file_num]:
                found = True
                break
            file_num += 1

        # find the number by straight conversion, and some math.
        num = int(square[1]) - 1  # it's 0 based

        if not found:
            raise ValueError(f"{ square[1] } is not a valid file")

        # this is supper fucked, but the chessboard interaly starts counting at h8
        self.nl_interface.set_LED(7 - num, 7 - file_num, status)

    def set_move_LEDs(self, move: str) -> None:
        """highlight a move. Light up the origin and destination LED
        @param: move: a move in uci
        """
        self.logger.info("man.set_move_LEDs( %s ) called\n", move)
        # turn off the led's
        self.turn_off_all_LEDs()
        # make sure move is of type str
        if type(move) != str:
            try:
                self.logger.error(
                    "\n\n set_move_LEDs entered with a move of type chess.Move\n\n"
                )
                move = move.uci()
            except Exception as err:
                message = f"{err} was raised exception on trying to convert move { move } to uci."
                self.logger.error(message)
        if move is not None:
            self.logger.info("led on(origin): %s", move[:2])
            self.set_led(move[:2], True)  # source

            self.logger.info("led on(dest): %s", move[2:4])
            self.set_led(move[2:4], True)  # dest
        else:
            raise NoMove("NicLinkManager.set_move_LEDs(): Move is None")

    def set_all_LEDs(self, light_board: np.ndarray[np.str_]) -> None:
        """set all led's on ext. chess board
        @param: light_board - a list of len 8 made up of
                str of len 8 with the 1 for 0 off
                for the led of that square
        """
        self.logger.info(
            "set_all_LEDs(light_board: np.ndarray[np.str_]): called with \
                light_board %s",
            light_board,
        )

        # the pybind11 use 8 str, because it is difficult
        # to use complex data structures between languages
        self.nl_interface.set_all_LEDs(
            str(light_board[0]),
            str(light_board[1]),
            str(light_board[2]),
            str(light_board[3]),
            str(light_board[4]),
            str(light_board[5]),
            str(light_board[6]),
            str(light_board[7]),
        )

    def turn_off_all_LEDs(self) -> None:
        """turn off all the leds"""
        self.nl_interface.lights_out()

    def get_FEN(self) -> str:
        """get the board FEN from chessboard"""
        fen = self.nl_interface.get_FEN()
        if fen is not None:
            return fen
        else:
            raise NoNicLinkFEN("No fen got from board")

    def put_board_FEN_on_board(self, boardFEN: str) -> chess.Board:
        """show just the board part of FEN on asci chessboard,
           then return it for logging purposes
        @param: boardFEN: just the board part of a fen,
                          ie: 8/8/8/8/8/8/8 for empty board ...
        @return: a chess.Board with that board fen on it
        """
        tmp_board = chess.Board()
        tmp_board.set_board_fen(boardFEN)
        print(tmp_board)
        return tmp_board

    def find_move_from_FEN_change(
        self, new_FEN: str
    ) -> str:  # a move in quardinate notation
        """get the move that occured to change the game_board fen into a given FEN.
        @param: new_FEN a board fen of the pos. of external board to parse move from
        return: the move in coordinate notation
        """
        old_FEN = self.game_board.board_fen()
        if new_FEN == old_FEN:
            print("no fen differance")
            raise NoMove("No FEN differance")

        self.logger.debug("new_FEN" + new_FEN)
        self.logger.debug("old FEN" + old_FEN)

        # get a list of the legal moves
        legal_moves = list(self.game_board.legal_moves)

        tmp_board = self.game_board.copy()
        self.logger.info(
            "+++ find_move_from_FEN_change(...) called +++\n\
current board: \n%s\n board we are using to check legal moves: \n%s\n",
            self.put_board_FEN_on_board(self.get_FEN()),
            self.game_board,
        )
        # find move by bmute force
        for move in legal_moves:
            # self.logger.info(move)
            tmp_board.push(move)  # Make the move on the board

            if (
                tmp_board.board_fen() == new_FEN
            ):  # Check if the board's FEN matches the new FEN
                self.logger.info(move)

                return move.uci()  # Return the last move

            tmp_board.pop()  # Undo the move and try another

        error_board = chess.Board()
        error_board.set_board_fen(new_FEN)
        self.show_board_diff(error_board, self.game_board)
        message = f"Board we see:\n{ str(error_board) }\nis not a possible result from \
a legal move on:\n{ str(self.game_board) }\n"
        raise IllegalMove(message)

    def check_for_move(self) -> bool | str:
        """check if there has been a move on the chessboard, and see if it is valid.
        If so update self.last_move
        """
        # ensure the move was valid

        # get current FEN on the external board
        new_FEN = self.nl_interface.get_FEN()

        if new_FEN is None:
            raise ValueError("No FEN from chessboard")

        if new_FEN != self.game_board.board_fen:
            # a change has occured on the chessboard
            # check to see if the game is over
            if self.game_over.is_set():
                return False

            # check if the move is valid, and set last move
            try:
                self.last_move = self.find_move_from_FEN_change(new_FEN)
            except RuntimeError as err:
                log_handled_exeption(err)
                self.logger.warning(
                    "\n===== move not valid, undue it and try again. it is white's \
turn? %s =====\n board we are using to check for moves:\n%s\n",
                    self.game_board.turn,
                    self.game_board,
                )
                # show the board diff from what we are checking for legal moves
                print(f"diff from board we are checking legal moves on:\n")
                current_board = chess.Board(new_FEN)
                self.show_board_diff(current_board, self.game_board)
                # pause for the refresh_delay and allow other threads to run

                time.sleep(self.refresh_delay)
                return False

            except ValueError:
                self.logger.warn(
                    "self.find_move_from_FEN_change(new_FEN) returned None. \
No move was found."
                )
                return False
            with self.lock:
                return self.last_move

        else:
            self.logger.info("no change.")
            # pause for a refresher
            time.sleep(self.refresh_delay)

            return False

    def await_move(self) -> str | None:
        """wait for legal move, and return it in coordinate notation after
        making it on internal board
        """
        global NO_MOVE_DELAY
        # loop until we get a valid move
        attempts = 0
        while not self.kill_switch.is_set():
            self.logger.info(
                "is game_over threading event set? %s", self.game_over.is_set()
            )
            # check for a move. If it move, return it else False
            try:
                move = False

                # check if the game is over
                if self.game_over.is_set():
                    return
                if self.check_for_move():
                    move = self.get_last_move()

                if move:
                    self.logger.info(
                        "move %s made on external board. there where %s attempts to get",
                        move,
                        attempts,
                    )
                else:
                    self.logger.info("no move")
                    # if move is false continue
                    continue

            except NoMove:
                # no move made, wait refresh_delay and continue
                attempts += 1
                self.logger.info("NoMove from chessboard. Attempt: %s", attempts)
                time.sleep(NO_MOVE_DELAY)

                continue

            except IllegalMove as err:
                # IllegalMove made, waiting then trying again
                attempts += 1
                self.logger.error(
                    "\nIllegal Move: %s | waiting NO_MOVE_DELAY= %s and checking again.\n",
                    err,
                    NO_MOVE_DELAY,
                )
                time.sleep(NO_MOVE_DELAY)
                continue

            return move

        # exit Niclink
        raise ExitNicLink(
            "in await_move():\nkill_switch.is_set: %s" % (self.kill_switch.is_set(),)
        )

    def get_last_move(self) -> str:
        """get the last move played on the chessboard"""
        with self.lock:
            if self.last_move is None:
                raise ValueError("ERROR: last move is None")

            return self.last_move

    def make_move_game_board(self, move: str) -> None:
        """make a move on the internal rep. of the game_board.
        update the last move made. This is not done automatically,
        so external program's can have more control
        @param: move - move in uci str
        """
        self.logger.info("move made on gameboard. move %s", move)
        self.game_board.push_uci(move)
        # update the last move
        self.last_move = move
        self.set_move_LEDs(move)
        self.logger.info(
            "made move on internal board, BOARD POST MOVE:\n%s", self.game_board
        )

    def set_board_FEN(self, board: chess.Board, FEN: str) -> None:
        """set a board up according to a FEN"""
        chess.Board.set_board_fen(board, fen=FEN)

    def set_game_board_FEN(self, FEN: str) -> None:
        """set the internal game board FEN"""
        self.set_board_FEN(self.game_board, FEN)

    def show_FEN_on_board(self, FEN: str) -> chess.Board:
        """print a FEN on on a chessboard
        @param: FEN - (str) FEN to display on board
        @returns: a board with the fen on it
        """
        board = chess.Board()
        self.set_board_FEN(board, FEN)
        print(board)
        return board  # for logging purposes

    def show_board_state(self) -> None:
        """show the state of the real world board"""
        curFEN = self.get_FEN()
        self.show_FEN_on_board(curFEN)

    def show_game_board(self) -> None:
        """print the internal game_board. Return it for logging purposes"""
        print(self.game_board)

    def set_game_board(self, board: chess.Board) -> None:
        """set the game board
        @param: board - the board to set as the game board
        """
        with self.lock:
            self.game_board = board

    def gameover_lights(self) -> None:
        """show some fireworks"""
        self.nl_interface.gameover_lights()

    def show_board_diff(self, board1: chess.Board, board2: chess.Board) -> None:
        """show the differance between two boards and output differance on a chessboard
        @param: board1 - refrence board
        @param: board2 - board to display diff from refrence board
        """
        # cread a board for recording diff on
        diff_board = np.zeros((8, 8), dtype=np.byte)
        # go through the squares and turn on the light for ones that are in error
        for n in range(0, 8):
            # because unicode ord("a") is 96, :. the offset
            for a in range(ord("a"), ord("h")):
                square = chr(a) + str(n + 1)  # real life is not 0 based
                py_square = chess.parse_square(square)
                if board1.piece_at(py_square) != board2.piece_at(py_square):
                    # record the diff in diff array
                    diff_board[n][a - 97] = 1

        self.logger.info("show_board_diff: diff_board %s\n", diff_board)

        if np.count_nonzero(diff_board) != 0:
            self.beep()
            self.logger.info("show_board_diff: diff found, self.beep()ing\n")
            time.sleep(NO_MOVE_DELAY)

    def get_game_FEN(self) -> str:
        """get the game board FEN"""
        return self.game_board.fen()

    def is_game_over(
        self,
    ) -> dict | bool:
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
    drawn if the half-move clock since a capture or pawn move is equal to or greater \
    than 150. Other means to end a game take precedence.",
            }

        return False

    def opponent_moved(self, move: str) -> None:
        """the other player moved in a chess game.
        Signal LEDS_changed and update last move
        @param: move - the move in a uci str
        """
        self.last_move = move
        self.set_move_LEDs(move)


# logger setup
logger = logging.getLogger("niclink")
logger.setLevel(logging.DEBUG)


#  === exception logging ===
# log unhandled exceptions to the log file
def log_except_hook(excType, excValue, traceback):
    global logger
    logger.error("Uncaught exception", exc_info=(excType, excValue, traceback))


def log_handled_exeption(exception: Exception) -> None:
    """log a handled exception"""
    global logger
    logger.error("Exception handled: %s", exception)


# setup except hook
sys.excepthook = log_except_hook


###### TEST SHIT #######
def test_bt():
    """test nl_bluetooth"""
    global logger
    nl_man = NicLinkManager(2, logger=logger, bluetooth=True)


def test_usb():
    """test usb connection"""
    global logger
    b1 = chess.Board()
    b2 = chess.Board()
    b2.push_uci("e2e4")
    nl_man = NicLinkManager(2, logger=logger)
    # so nothing messes with the leds
    print("TEST: man.show_board_diff(b1,b2)")
    nl_man.show_board_diff(b1, b2)
    print("(test usb connection) testing  set_all_LEDs.")
    # create a np.array of all true

    nl_man.set_all_LEDs(ONES)
    print("all the lights should be on, confirm and press enter")
    readchar.readchar()

    nl_man.set_all_LEDs(ZEROS)
    print("all the lights should be off, confirm and press enter")
    readchar.readchar()

    print("(test usb connection) set up the board and press enter.")
    nl_man.show_game_board()
    print("= set up cb, and test move parsing and set_move_LEDs(move) ")
    readchar.readkey()

    while True:
        move = nl_man.await_move()

        print(move)


if __name__ == "__main__":
    # test_bt()
    test_usb()
