import time

import pyfirmata

board = pyfirmata.Arduino("/dev/ttyACM0")

while True:
    board.digital[7].write(1)
    time.sleep(1)
    board.digital[7].write(0)
    time.sleep(1)
