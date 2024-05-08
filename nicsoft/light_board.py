# light_board is a part of NicLink
#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the gnu general public license as published by the free software foundation, either version 3 of the license, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but without any warranty; without even the implied warranty of merchantability or fitness for a particular purpose. see the gnu general public license for more details.
#
#  you should have received a copy of the gnu general public license along with NicLink. if not, see <https://www.gnu.org/licenses/>.


class LightBoard:
    """a representation of the LED's on a chessnut air"""

    def __init__(self, lit_squares: List[str]) -> None:
        """init a lightboard with each of the list of squares lit up.
        @param: lit_squares - a list of squares to set as lit in SAN
        """
        light_board = np.array(
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

    def __str__(self) -> str:
        return (
            str(light_board[0]),
            str(light_board[1]),
            str(light_board[2]),
            str(light_board[3]),
            str(light_board[4]),
            str(light_board[5]),
            str(light_board[6]),
            str(light_board[7]),
        )

    def _build_led_map(moves: List[str]) -> None:
        """build the led_map for given uci moves
        @param: moves - move list in uci
        """
        global logger, ZEROS
        zeros = "00000000"
        logger.info("build_led_map_for_move's(%s)", moves)

        led_map = np.copy(ZEROS)

        # get the squars and the coordinates
        s1 = move[:2]
        s2 = move[2:]

        s1_cords = square_cords(s1)
        s2_cords = square_cords(s2)

        # set 1st square
        led_map[s1_cords[1]] = zeros[: s1_cords[0]] + "1" + zeros[s1_cords[0] :]
        # set second square
        led_map[s2_cords[1]] = zeros[: s2_cords[0]] + "1" + zeros[s2_cords[0] :]
        logger.info("led map made for move: %s\n", move)
        log_led_map(led_map)

        return led_map
