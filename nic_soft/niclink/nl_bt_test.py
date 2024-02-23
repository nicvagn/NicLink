#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.


from nl_bluetooth import  GetChessnutAirDevices
import asyncio
import nl_bluetooth
from nl_exceptions import NoMove, IllegalMove
import time
import chess
import readchar
import sys


from bleak import BleakClient
from nl_bluetooth import INITIALIZASION_CODE, WRITECHARACTERISTICS, READCONFIRMATION, READDATA, convertDict, MASKLOW

from threading import Thread
import time

def connect(self):
    """connect to the chessboard"""

    # connect to the chessboard, this must be done first
    nl_bluetooth.connect()

    # because async programming is hard
    testFEN = nl_bluetooth.getFEN()
    time.sleep(2)
    # make sure getFEN is working
    testFEN = nl_bluetooth.getFEN()

    if testFEN == "" or None:
        exceptionMessage = "Board initialization error. '' or None for FEN. Is the board connected and turned on?"
        raise RuntimeError(exceptionMessage)

def main():
    connect()

    while True:
        print(nl_bluetooth.getFEN()) 

async def run(connect, debug=False):
    """ Connect to the device and run the notification handler.
    then read the data from the device. after 100 seconds stop the notification handler."""
    print("device.adress: ", connect.device.address)

    async def notification_handler(characteristic, data):
        """Handle the notification from the device and print the board."""
        global oldData
        # print("data: ", ''.join('{:02x}'.format(x) for x in data))
        if data[2:34] != oldData:
            printBoard(data[2:34])
            await leds(data[2:34])
            oldData = data[2:34].copy()
    global CLIENT
    async with BleakClient(connect.device) as client:
        # TODO: this global variable is a derty trick
        CLIENT=client
        print(f"Connected: {client.is_connected}")
        # send initialisation string
        await client.start_notify(READDATA, notification_handler) # start the notification handler
        await client.write_gatt_char(WRITECHARACTERISTICS, INITIALIZASION_CODE) # send initialisation string
        await asyncio.sleep(100.0) ## wait 100 seconds
        await client.stop_notify(READDATA) # stop the notification handler


if __name__ == "__main__":
    connect = GetChessnutAirDevices()
    # get device
    breakpoint()
    asyncio.run(connect.discover())
    # connect to device
    asyncio.run(run(connect, debug=True))
    
