#  This file is a part of NicLink
#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.


import readchar

from niclink import NicLinkManager


def test():
    print("\n+++++ NicLink: testing signals ++++\n")

    print("nl.signal_lights(1): press enter for next")
    nl.signal_lights(1)
    readchar.readchar()
    print("nl.signal_lights(2): press enter for next")
    nl.signal_lights(2)
    readchar.readchar()
    print("nl.signal_lights(3): press enter for next")
    nl.signal_lights(3)
    readchar.readchar()
    print("nl.signal_lights(4): press enter for next")
    nl.signal_lights(4)
    readchar.readchar()
    print("nl.signal_lights(5): press enter for next")
    nl.signal_lights(5)
    readchar.readchar()
    print("nl.signal_lights(6): press enter for next")
    nl.signal_lights(6)
    readchar.readchar()

    print("end")


if __name__ == "__main__":

    # connect to the board
    nl = NicLinkManager(1)
    test()
