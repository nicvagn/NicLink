# NicLink - A python interface for the Chessnut Air

# Notice
> version 0.7

> checkout this software, it solves the problem's I wanted to solve with NicLink:
    https://chromewebstore.google.com/detail/chessconnect/dmkkcjpbclkkhbdnjgcciohfbnpoaiam?hl=en-GB
# gotchas
    - if: ModuleNotFoundError: No module named 'niclink' make sure your venve is setup, with the .pth file configured. 
    - Make sure you are in said venv
# overview

    - see the python requirements.txt for external requirements
    - run updateNicLink.sh to compile and prepaire the env
    - only tested on gnu/linux with a chessnut air.
    - branches:
        - master: behind the times. More likely to be solid
        - dev: the wild west of new features

## requirements

- hidraw and spdlog they are internal in src/thirdparty
- in order to compile them on Debian you need the package libudev-dev
- python modules listed in requirements.txt
- cmake (3.4 ... 3.20) some distros are behind signifigantly, so I recomend "pip install cmake" after uninstalling the one from your distro

- if cmake can not find python packages (probably) see setting up a python environment and run cmake from the venv 

- If you attempt getting nl set up on your system, I will give you a hand if you need it. I would be intrested in reading a log, too!

## Setting up python venv

make sure  python-dev libusb-1.0-0-dev libudev-dev

In order to use NicLink while it is in development, it is advised to use a virtual environment. I do not have a good enough understanding,
but you have the internet. ( here is a start: https://python.land/virtual-environments/virtualenv ) Go ham. It is now at a point where it should be portable, if you are reeding this, and want to really help me out,
it would be swell to hear how installing NicLink goes. The pyproject.toml should have the requirements. There is a requirements.txt too.

what I did (bash):
    python -m venv nicsoft  - This creates a python venv in nicsoft
    . ./source_pyvenv.sh    - this uses a litle convieniance script, but basically all you have to do is source ./bin/activate (other file extensions if not in bash)

In order to setup your python path correctly, put the niclink.pth file someware in your venv python path.

for me I modified the niclink.pth file to be:
    1. /home/nrv/NicLink

and modified:
    - nicsoft/lib/python3.9/site-packages/niclink.pth to add {whatever}/NicLink/nicsoft
    - to my pythonpath with:
```
import os; var = 'SETUPTOOLS_USE_DISTUTILS'; enabled = os.environ.get(var, 'local') == 'local'; enabled and __import__('_distutils_hack').add_shim(); 
/home/nrv/dev/NicLink/nicsoft/
```
(I no longer recal what the first line does, but if it aint broke, don't fix)

to find out your venv's python path:

( while in the venv )

1. go into your python interpreter
2. following:
   - ">> import sys"
   - ">> print('\n'.join(sys.path))"
4. create a .pth file pointing to the .../NicLink/nicsoft dir in one of the listed dirs in your pythonpath
5. profit


then I ran:

">>> import sys"
">>> print('/n'.join(sys.path))"
and it outputted:
/n/usr/lib/python39.zip/n/usr/lib/python3.9/n/usr/lib/python3.9/lib-dynload/n/home/nrv/NicLink/nicsoft/lib/python3.9/site-packages/n/home/nrv/NicLink

*** jazz hands ***

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

