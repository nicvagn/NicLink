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

NO_MOVE_DELAY = 0.5

LIGHT_THREAD_DELAY = 0.8

### logger ###
logger = logging.getLogger("NicLink")


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
            self.logger.error("niclink made it's own logger with logging level ERROR")

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
        self.logger.info(
            "\n\n _run_game(...): game_over event set, resetting NicLink\n"
        )

    def connect(self, bluetooth: bool = False):
        """connect to the chessboard
        @param: bluetooth - should we use bluetooth
        """
        # connect to the chessboard, this must be done first
        self.nl_interface.connect()

        # FIX: give time for NL to connect
        time.sleep(self.thread_sleep_delay)
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

        self.logger.debug("NicLinkManager reset\n")

    def set_led(self, square: str, status: bool) -> None:
        """set an LED at a given square to a status
        @param: square (square: a1, e4 etc)
        @param: status: True | False
        @side_effect: changes led on chessboard
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
        @side_effect: changes board led's. Shut's off all led's, and display's  the move
        """
        self.logger.info("man.set_move_LEDs( %s ) called\n", move)
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

        self.logger.info("move LED's on for move: %s", move)
        move_led_map = build_led_map_for_move(move)
        # log led map
        self.logger.debug("move led map created. Move: %s \n map: ", move)
        log_led_map(move_led_map, self.logger)

        self.set_all_LEDs(move_led_map)

    def set_all_LEDs(self, light_board: np.ndarray[np.str_]) -> None:
        """set all led's on ext. chess board
        @param: light_board - a list of len 8 made up of
                str of len 8 with the 1 for 0 off
                for the led of that square
        """
        self.logger.debug(
            "set_all_LEDs(light_board: np.ndarray[np.str_]): called with following light_board:"
        )

        log_led_map(light_board, self.logger)

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

    def signal_lights(self, sig_num: int) -> None:
        """signal the user via displaying a set of lights on the board
        @parm: sig_num - the signal number coresponding to the signal to show
                ie: 1 - ring of lights
                    2 - left half lit up
                    3 - right half lit up
                    4 - central line
                    5 - cross in center
        @side effect - change the light's on the chess board
        """
        if sig_num == 1:
            """signal 1 - ring of lights"""

            sig = np.array(
                [
                    "11111111",
                    "10000001",
                    "10000001",
                    "10000001",
                    "10000001",
                    "10000001",
                    "10000001",
                    "11111111",
                ],
                dtype=np.str_,
            )
            self.set_all_LEDs(sig)

        elif sig_num == 2:
            """signal 2 - left half lit up"""
            sig = np.array(
                [
                    "00000000",
                    "00000000",
                    "00000000",
                    "00000000",
                    "11111111",
                    "11111111",
                    "11111111",
                    "11111111",
                ],
                dtype=np.str_,
            )

            self.set_all_LEDs(sig)
        elif sig_num == 3:
            """signal 3 - right half lit up"""
            sig = np.array(
                [
                    "11111111",
                    "11111111",
                    "11111111",
                    "11111111",
                    "00000000",
                    "00000000",
                    "00000000",
                    "00000000",
                ],
                dtype=np.str_,
            )
            self.set_all_LEDs(sig)
        elif sig_num == 4:
            """Signal 4 - center line"""
            sig = np.array(
                [
                    "00000000",
                    "00000000",
                    "00000000",
                    "11111111",
                    "11111111",
                    "00000000",
                    "00000000",
                    "00000000",
                ],
                dtype=np.str_,
            )
        elif sig_num == 5:
            """Signal 5 - center cross"""
            sig = np.array(
                [
                    "00011000",
                    "00011000",
                    "00011000",
                    "11111111",
                    "11111111",
                    "00011000",
                    "00011000",
                    "00011000",
                ],
                dtype=np.str_,
            )

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
            self.logger.debug("no fen differance. FEN was %s", old_FEN)
            raise NoMove("No FEN differance")

        self.logger.debug("new_FEN" + new_FEN)
        self.logger.debug("old FEN" + old_FEN)

        # get a list of the legal moves
        legal_moves = list(self.game_board.legal_moves)

        tmp_board = self.game_board.copy()
        self.logger.debug(
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
                self.logger.info("move was found to be: %s", move)

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
        try:
            # will cause an index error if game_board has no moves
            last_move = self.game_board.pop()

            # check if you just have not moved the opponent's piece
            if new_FEN == self.game_board.board_fen():
                self.logger.debug(
                    "board fen is the board fen before opponent move made on chessboard. Returning"
                )
                self.game_board.push(last_move)
                time.sleep(self.refresh_delay)
                return False

            self.game_board.push(last_move)
        except IndexError:
            last_move = False  # if it is an empty list of moves

        if new_FEN != self.game_board.board_fen:
            # a change has occured on the chessboard
            # check to see if the game is over
            if self.game_over.is_set():
                return False

            # check if the move is valid, and set last move
            try:
                self.last_move = self.find_move_from_FEN_change(new_FEN)
            except IllegalMove as err:
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

            # return the move
            with self.lock:
                return self.last_move

        else:
            self.logger.debug("no change in FEN.")
            self.turn_off_all_LEDs()
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
            self.logger.debug(
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
                if move:  # if we got a move, return it and exit
                    self.logger.info(
                        "move %s made on external board. there where %s attempts to get",
                        move,
                        attempts,
                    )
                    return move
                else:
                    self.logger.debug("no move")
                    # if move is false continue
                    continue

            except NoMove:
                # no move made, wait refresh_delay and continue
                attempts += 1
                self.logger.debug("NoMove from chessboard. Attempt: %s", attempts)
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
        update the last move made. and update the move LED's on ext board.
        This is not done automatically so external program's can have more control.
        @param: move - move in uci str
        @side_effect: set's move led's
        """
        if self.last_move == move:
            self.logger.error(
                "make_move_game_board(move) called w move == self.last_move. returning"
            )
            return
        self.logger.debug("move made on gameboard. move %s", move)
        self.game_board.push_uci(move)
        # update the last move and last move time
        self.last_move = move
        self.set_move_LEDs(move)
        self.logger.debug(
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

    def square_in_last_move(self, square: str) -> bool:
        """is the square in the last move?
        @param: square - a square in algabraic notation
        @returns: bool - if the last move contains that square
        """
        if self.last_move:
            if square in self.last_move:
                return True

        return False

    def show_board_diff(self, board1: chess.Board, board2: chess.Board) -> bool:
        """show the differance between two boards and output differance on a chessboard
        @param: board1 - refrence board
        @param: board2 - board to display diff from refrence board
        @side_effect: changes led's to show diff squares
        @returns: bool - if there is a diff
        """
        self.logger.debug(
            "man.show_board_diff entered w board's \n%s\nand\n%s", board1, board2
        )
        # cread a board for recording diff on
        diff_map = np.copy(ZEROS)
        zeros = "00000000"  # for building the diff aray that work's for the way we set LED's

        # go through the squares and turn on the light for ones that are in error
        diff = False
        diff_squares = []  # what squares are the diff's on

        for n in range(0, 8):
            # handle diff's for a file
            for a in range(ord("a"), ord("h")):
                # get the square in algabraic notation form
                square = chr(a) + str(n + 1)  # real life is not 0 based

                py_square = chess.parse_square(square)

                if board1.piece_at(py_square) != board2.piece_at(
                    py_square
                ) or self.square_in_last_move(square):
                    # record the diff in diff array, while keeping the last move lit up
                    self.logger.info(
                        "man.show_board_diff(...): Diff found at square %s", square
                    )

                    # do not record diff's on the move squares, but light them up
                    if not self.square_in_last_move(square):
                        diff = True

                        # add square to list off diff squares
                        diff_squares.append(square)
                        # find the coordinate of the diff square
                        diff_cords = square_cords(square)

                        diff_map[diff_cords[1]] = (
                            zeros[: diff_cords[0]] + "1" + zeros[diff_cords[0] :]
                        )

        if diff:
            # set all the led's on the diff map
            self.set_all_LEDs(diff_map)
            self.logger.info(
                "show_board_diff: diff found --> diff_squares: %s\n",
                diff_squares,
            )

        return diff

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
        self.logger.debug("opponent movet1d %s", move)
        self.last_move = move
        self.set_move_LEDs(move)


### helper functions ###
def square_cords(square) -> (int, int):
    """find cordinates for a given square on the chess board. (0, 0)
    is a1.
    @params: square - std algebraic square, ie b3, a8
    @returns: touple of the (x, y) coordinate of the square (0 based) (file, rank)
    """
    global FILES
    rank = int(square[1]) - 1  # it's 0 based

    # find the file number by itteration
    found = False
    letter = square[0]
    file_num = 0
    while file_num < 8:
        if letter == FILES[file_num]:
            found = True
            break
        file_num += 1

    if not found:
        raise ValueError(f"{ square[0] } is not a valid file")

    return (file_num, rank)


def log_led_map(led_map: np.ndarray[np.str_], logger) -> None:
    """log led map pretty 8th file to the top"""
    logger.debug("\nLOG LED map:\n")
    logger.debug(str(led_map[7]))
    logger.debug(str(led_map[6]))
    logger.debug(str(led_map[5]))
    logger.debug(str(led_map[4]))
    logger.debug(str(led_map[3]))
    logger.debug(str(led_map[2]))
    logger.debug(str(led_map[1]))
    logger.debug(str(led_map[0]))


def build_led_map_for_move(move: str) -> np.ndarray[np.str_]:
    """builmd the led_map for a given uci move
    @param: move - move in uci
    @return: constructed led_map
    """
    global logger, ZEROS
    zeros = "00000000"
    logger.debug("build_led_map_for_move(%s)", move)

    led_map = np.copy(ZEROS)

    # get the squars and the coordinates
    s1 = move[:2]
    s2 = move[2:]
    s1_cords = square_cords(s1)
    s2_cords = square_cords(s2)

    # if they are not on the same rank
    if s1_cords[1] != s2_cords[1]:
        # set 1st square
        led_map[s1_cords[1]] = zeros[: s1_cords[0]] + "1" + zeros[s1_cords[0] :]
        logger.debug("map after 1st move cord (cord): %s", s1_cords)
        log_led_map(led_map, logger)
        # set second square
        led_map[s2_cords[1]] = zeros[: s2_cords[0]] + "1" + zeros[s2_cords[0] :]
        logger.debug("led map made for move: %s\n", move)
        log_led_map(led_map, logger)
    # if they are on the same rank
    else:
        rank = list(zeros)
        rank[s1_cords[0]] = "1"
        rank[s2_cords[0]] = "1"

        print(rank)

        rank_str = "".join(rank)

        # insert into led_map as numpy string
        led_map[s1_cords[1]] = np.str_(rank_str)

    return led_map


#### logger setup ####
def set_up_logger() -> None:
    """Only run when this module is run as __main__"""
    global logger

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(module)s %(message)s")

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(formatter)
    consoleHandler.setLevel(logging.ERROR)
    logger.addHandler(consoleHandler)

    # logging to a file
    fileHandler = logging.FileHandler("NicLink.log")
    logger.addHandler(fileHandler)

    DEBUG = False
    if DEBUG:
        logger.info("DEBUG is set.")
        logger.setLevel(logging.DEBUG)
        fileHandler.setLevel(logging.DEBUG)
        consoleHandler.setLevel(logging.DEBUG)
    else:
        logger.info("DEBUG not set")
        # for dev
        logger.setLevel(logging.INFO)
        consoleHandler.setLevel(logging.INFO)
        fileHandler.setLevel(logging.INFO)
        # logger.setLevel(logging.ERROR) for production
        # consoleHandler.setLevel(logging.ERROR)


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
