#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.

import asyncio

from bleak import BleakClient

from .constants import (
    INITIALIZASION_CODE,
    MASKLOW,
    READCONFIRMATION,
    READDATA,
    WRITECHARACTERISTICS,
    convertDict,
)
from .discovery import GetChessnutAirDevices

""" A api for getting the FEN etc. from the board with bluetooth """
currentFEN = None
oldData = None
CLIENT = None
# the values for specifying the square in rowan LED
ROW_SQUARE_VALUES = [128, 64, 32, 16, 8, 4, 2, 1]

# keeps track of what led's are on.
led = bytearray([0x0A, 0x08, 0x1, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])


def connect() -> None:  # -> bool:
    """try to connect to the board over bluetooth"""
    connect = GetChessnutAirDevices()
    # get device
    asyncio.run(connect.discover())
    # connect to device
    asyncio.run(run(connect))


def disconnect():
    """disscoiiect from the chessboard"""
    print("BLUETOOTH DISCONECT. WHY WOULD I cALL THIS?")


def beep():
    """make the chessboard beep"""
    print("BEEP")


def get_FEN() -> str | None:
    """get the FEN from the chessboard over bluetooth"""
    print("BLUETOOTH get fen")
    return currentFEN


def lightsOut():
    """turn off all the chessboard lights"""
    print("lights out bt")
    led = bytearray([0x0A, 0x08, 0x1, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    # send the led bytearray with all zero for last 8 bytes
    CLIENT.write_gatt_char(WRITECHARACTERISTICS, led)


def set_LED(x, y, status) -> None:
    """set a led on the chessboard"""
    set_bit(led, y, status)

    CLIENT.write_gatt_char(WRITECHARACTERISTICS, led)


def set_all_LEDs(ln1, ln2, ln3, ln4, ln5, ln6, ln7, ln8):
    raise NotImplemented


def updateFEN(data):
    """update the currentFEN
        first two bytes should be 0x01 0x24.
        The next 32 bytes specify the position.

        Each square has a value specifying the piece:
    Value 0 1 2 3 4 5 6 7 8 9 A B C
    Piece . q k b p n R P r B N Q K

            q k b p n R P r B N Q K

    Each of the 32 bytes represents two squares with the order being the squares labelled
    H8,G8,F8...C1,B1,A1. Within each byte the lower 4 bits represent the first square and the
    higher 4 bits represent the second square. This means that if the 32 bits were written out in
    normal hex characters the pairs would actually appear reversed.
    For example, the 32 bytes for the normal starting position with black on the 7th and 8th ranks
    would be shown as:
    58 23 31 85 44 44 44 44 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    00 77 77 77 77 A6 C9 9B 6A
    So the first byte's value of 0x58 means a black rook (0x8) on H8 and a black knight (0x5) on
    G8 and the second byte's value of 0x23 means a black bishop (0x3) on F8 and a black king (0x2)
    on E8.
    """
    chessboard = [8]
    for col_num in range(0, 8):
        empty = 0  # a value for setting empty part's of the fen
        row = reversed(data[col_num * 4 : col_num * 4 + 4])
        print(row)
        # chessboard[col_num] = row
        byte_num = 0
        convertedRow = []
        for b in row:
            breakpoint()
            if b >> 4 == 0:
                empty += 1
                breakpoint()
                continue
            convertedRow[byte_num] = (convertDict[b >> 4], convertDict[b & MASKLOW])
            byte_num += 1

        chessboard[col_num] = convertedRow
    print(chessboard)


def set_bit(v, index, x):
    """Set the index:th bit of v to 1 if x is truthy,
    else to 0, and return the new value."""
    mask = 1 << index  # Compute mask, an integer with just bit 'index' set.
    v &= ~mask  # Clear the bit indicated by the mask (if x is False)
    if x:
        v |= mask  # If x was True, set the bit indicated by the mask.
    return v  # Return the result, we're done.


def printBoard(data):
    """Print the board in a human readable format.
        first two bytes should be 0x01 0x24.
        The next 32 bytes specify the position.

        Each square has a value specifying the piece:
    Value 0 1 2 3 4 5 6 7 8 9 A B C
    Piece . q k b p n R P r B N Q K

            q k b p n R P r B N Q K

    Each of the 32 bytes represents two squares with the order being the squares labelled
    H8,G8,F8...C1,B1,A1. Within each byte the lower 4 bits represent the first square and the
    higher 4 bits represent the second square. This means that if the 32 bits were written out in
    normal hex characters the pairs would actually appear reversed.
    For example, the 32 bytes for the normal starting position with black on the 7th and 8th ranks
    would be shown as:
    58 23 31 85 44 44 44 44 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    00 77 77 77 77 A6 C9 9B 6A
    So the first byte's value of 0x58 means a black rook (0x8) on H8 and a black knight (0x5) on
    G8 and the second byte's value of 0x23 means a black bishop (0x3) on F8 and a black king (0x2)
    on E8.
    """
    for counterColum in range(0, 8):
        print(8 - counterColum, " ", end=" ")
        row = reversed(data[counterColum * 4 : counterColum * 4 + 4])
        for b in row:
            print(convertDict[b >> 4], convertDict[b & MASKLOW], end=" ")
        print("")
    print("    a b c d e f g h\n\n")


async def leds(data):
    """Switch on all non empty squares.
        The other data sent to the board controls the LEDs. There are two control bytes and 8 data
    bytes:
    0x0A 0x08 <R8> <R7> <R6> <R5> <R4> <R3> <R2> <R1>
    where the 8 bytes represent the LEDs with one byte for each row of the board. The first byte
    is for the row furthest away (labelled A8..H8).
    For each byte the value is determined by whether the LED for each square needs to be on
    or off. If the square is off then it will have a value of 0 and if it needs to be on then the value
    will be based on the square position in the row, with values being:
    128 64 32 16 8 4 2 1
    The values for all the squares in the row are added together, meaning the maximum value of
    the byte is 255 which would occur if all of the LEDs in the row were turned on. So to show
    the move E2-E4 (with the board in the normal, non-flipped position) the ten bytes (including
    the controls) would be:
    0A 08 00 00 00 00 08 00 08 00
    To turn off all LEDs you just send the 10 bytes with the last 8 bytes all as zero values
    """

    led = bytearray([0x0A, 0x08, 0x1, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    for counterColum in range(0, 8):
        row = data[counterColum * 4 : counterColum * 4 + 4]
        for counter, b in enumerate(row):
            v = led[counterColum + 2]
            n1 = convertDict[b & MASKLOW]
            if n1.isalnum():
                v = set_bit(v, counter * 2, 1)
                led[counterColum + 2] = v
            n2 = convertDict[b >> 4]
            if n2.isalnum():
                v = set_bit(v, counter * 2 + 1, 1)
                led[counterColum + 2] = v

    await CLIENT.write_gatt_char(WRITECHARACTERISTICS, led)


async def run(connect, debug=False):
    """Connect to the device and run the notification handler.
    then read the data from the device. after 100 seconds stop the notification handler.
    """
    print("device.adress: ", connect.device.address)

    async def notification_handler(characteristic, data):
        """Handle the notification from the device and print the board."""
        global oldData
        # print("data: ", ''.join('{:02x}'.format(x) for x in data))
        if data[2:34] != oldData:
            # printBoard(data[2:34])
            updateFEN(data[2:34])
            await leds(data[2:34])
            oldData = data[2:34].copy()

    global CLIENT
    async with BleakClient(connect.device) as client:
        # TODO: this global variable is a derty trick
        CLIENT = client
        print(f"Connected: {client.is_connected}")
        # send initialisation string
        await client.start_notify(
            READDATA, notification_handler
        )  # start the notification handler
        await client.write_gatt_char(
            WRITECHARACTERISTICS, INITIALIZASION_CODE
        )  # send initialisation string
        await asyncio.sleep(100.0)  ## wait 100 seconds
        await client.stop_notify(READDATA)  # stop the notification handler


def gameover_lights() -> None:
    """just to remind me"""
    raise NotImplemented()


if __name__ == "__main__":
    c = GetChessnutAirDevices()
    # get device
    asyncio.run(c.discover())
    # connect to device
    asyncio.run(run(c))
