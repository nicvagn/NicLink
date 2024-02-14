# NicLink - A python interface for the Chessnut Air

# Notice
> version 0.3
> checkout this software, it solves the problem's I wannted to solve with NicLink:
    https://chromewebstore.google.com/detail/chessconnect/dmkkcjpbclkkhbdnjgcciohfbnpoaiam?hl=en-GB

## overview 

    - see the python requirements.txt for external requirements
    - only tested on gnu/linux with a chessnut air.
    - branches:
        - master: behind the times. More likely to be solid
        - dev: the wild west of new features

## Using the board on lichess with the board api
        
    In the ROOT/nic_soft/niclink_lichess dir create a dir called lichess_token.
    in this dir create a file called token. This will be a plain text file containing
    only the text of your lichess auth token.

    example:
         filename: nic_sof/niclink_lichess/token
         content: lip_5PIkq4soaF3XyFGvelx


   then cd .. and run python niclink_lichess

## Use with gnu/linux:

    In order to use NicLink as a user in the wheel group 
    ( group can be arbitrary )
    You must give the user read and write permissions for the Chessnut air.
    This can be done through a udev rule.

    create a 99-chessnutair.rules file: /etc/udev/rules.d/99-chessnutair.rules,
    with the following:

        SUBSYSTEM=="usb", ATTRS{idVendor}:="2d80", /
        ATTRS{idProduct}:="8002", GROUP="wheel", MODE="0660"

        # set the permissions for device files
        KERNEL=="hidraw*", GROUP="wheel", MODE="0660"

    my chessnutair has the following properties, if your's differs, adjust.

        ID:  {vendor id} 2d80 : {product id} 8002

        mount poin: /dev/hidraw2

    This gives wheel group access to all of your hidraw devices,
    but wheel usualy has sudo access so they have that anyway with sudo

## playing with stockfish

    > you can play with stockfish with NicLink!

    In order to do so, you should read ./play_stockfish/README.md for further info


## have something to add/suggest?

contact me:

[nicolasvaagen@gmail.com](nicolasvaagen@gmail.com)

or, make a pull request!

# have a great day! 
# chessnutair
python script able to connect to the chessnut air board using bluetooth

Here you will find a script able to read the position of the pieces in the chess board and print the board on the PC screen. Additionally it will switch on the leds of those squares that are not empty. If a piece is moved a new board will be printed on the screen and the corresponding leds switched off/on.
The connection are made by bluetooth using the library bleak and no driver is needed. Regarding supported systems I believe the only limitations are those imposed by the bleak library that are (https://bleak.readthedocs.io/en/latest/):

 * Supports Windows 10, version 16299 (Fall Creators Update) or greater
 * Supports Linux distributions with BlueZ >= 5.43 (See Linux backend for more details)
 * OS X/macOS support via Core Bluetooth API, from at least OS X version 10.11

So far, I have only tested this shofware in Ubuntu 18.

## Installation and execution
 1. download code
 1. install dependencies (pip3 install -r requeriments.txt
 1. Execute python3 ./main.py
 
 The chessnut air board need to be paired to the PC in which you are running this.
 
