# NicLink - A python interface for the Chessnut Air

# Notice
> version 0.7

> checkout this software, it solves the problem's I wanted to solve with NicLink:
    https://chromewebstore.google.com/detail/chessconnect/dmkkcjpbclkkhbdnjgcciohfbnpoaiam?hl=en-GB

# overview

    - see the python requirements.txt for external requirements
    - run updateNicLink.sh to compile and prepaire the env
    - only tested on gnu/linux with a chessnut air.
    - branches:
        - master: behind the times. More likely to be solid
        - dev: the wild west of new features
        - bluetooth: in dev, not in a good place yet
## Setting up python venv

In order to use NicLink while it is in development, it is advised to use a virtual environment. I do not have a good enough understanding,
but you have the internet. Go ham. It is now at a point where it should be portable, if you are reeding this, and want to really help me out,
it would be swell to hear how installing NicLink goes. The pyproject.toml should have the requirements. There is a requirements.txt too.

## Using the board on lichess with the board api

    In the ROOT/nic_soft/niclink_lichess dir create a dir called lichess_token.
    in this dir create a file called token. This will be a plain text file containing
    only the text of your lichess auth token.

    example:
         `filename: nic_sof/niclink_lichess/token`
         `content: lip_5PIkq4soaF3XyFGvelx`

    then cd .. and run python niclink_lichess

    It can play games that can be played w board API ( only tested rapid and classical ).

    The board will beap at you when an inncorect position is on the board.


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

## Connect w bluetooth

    not mature enough to doc, but exists (Is a broken mess, save yourself)

## have something to add/suggest?

contact me:

[nicolasvaagen@gmail.com](nicolasvaagen@gmail.com)

or, make a pull request!

# have a great day!

