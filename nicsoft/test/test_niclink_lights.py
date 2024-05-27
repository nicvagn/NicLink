#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

import time

from niclink import NicLinkManager

print("\n\n====== NicLink test lights ====== \n")


# connect to the board
nl = NicLinkManager(1)


def test_led():
    print("all the lights should come on, starting with a1 finishing with h8")
    for x in range(1, 9):
        nl.beep()
        for a in range(1, 9):
            square = chr(ord("`") + a) + str(x)
            print(square + " on")
            nl.set_led(square, True)

            time.sleep((0.01))

    for x in range(1, 9):
        for a in range(1, 9):
            square = chr(ord("`") + a) + str(x)
            print(square + " off")
            nl.set_led(square, False)


def set_move_leds(move):
    nl.set_move_LEDs(move)


test_led()
# set_move_leds("a4h4")
