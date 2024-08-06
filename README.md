# NicLink - A python interface for the Chessnut Air

> version 0.95

# Notice

> check out this software, it solves the problem's I wanted to solve with NicLink:

    https://chromewebstore.google.com/detail/chessconnect/dmkkcjpbclkkhbdnjgcciohfbnpoaiam?hl=en-GB

# SETUP:

    - there is a github action to help you with setup,
      I am not framilular but give it a look if you are
    - there is also a shell script called setubNicLink.sh in the git root, that will clone NicLink and install python deps
    - see the python requirements.txt for external python requirements

    - see "## non pip requirements" below for further C++ and system req's

    - get all the required submodules with
      `$ git submodule update --init --recursive`
    - once you have the build environment ready, run updateNicLink.sh to compile and prepare the C++ EasyLinkSDK code.
    - only tested on gnu/linux with a chessnut air.
    - branches:
      - master: behind the times. More likely to be solid
      - dev: the wild west of new features

## non pip requirements

these are system requirements, python requirements are needed too

on Fedora:

    ```
    cmake
    gcc
    g++
    python-devel
    pybind11-devel
    libudev-devel
    hidapi-devel
    ```

#### detailed ramblings on packages:

    On arch, libusb backend was giving me some trouble. hidraw seems to be working

    > requirements:
    - hidraw and spdlog are internal in src/thirdparty
    - in order to compile them on Debian you need:

      - checkout the community fork of the EasylinkSDK and get that building first.
        You have to build that as a component of NicLink
        Link: `https://github.com/miguno/EasyLinkSDK`

      - libudev-dev or on fedora libudev-devel or equivalent on your distros

      - hidapi and hidapi-devel (or -dev)

        - requirements:
        - pybind11-devel in order to compile the code
        - python-dev or python-devel or whatever it is on your distro needed to build pybind code
        - only needed if using the libusb backend:
          - libusb (https://github.com/libusb/libusb/releases) - this is included as a submodule

    - pip configured for python 3.12

    - python 3.12 and python-dev (or python-devel, you need python.h anyway) and python modules listed in requirements.txt

    - cmake (3.4 ... 3.20) some distros are behind significantly, so I recommend "pip install cmake"
      after uninstalling the one from your distro. Or it will probably be fine ...

    - modern gcc (I used gcc 13.2) and gcc-c++

      > so you need gcc, cmake, gcc-c++, python-devel, pybind11, pybind11-devel and the kichen sink
      > I satisfied the requirement via: sudo dnf install gcc cmake g++ python-devel pybind11-devel

    - if cmake can not find python packages (probably) see setting up a python environment and run cmake from the venv

    - If you attempt getting nl set up on your system, I will give you a hand if you need it. I would be interested in reading a log, too!

    if you get a dev environment set up, I would like to know about it.

    > The system packages required, and the system

## Setting up python venv

    In order to use NicLink while it is in development, it is advised to use a virtual environment.
    I do not have a good enough understanding, but you have the internet.
    ( here is a start: https://python.land/virtual-environments/virtualenv ) Go ham.

    It is now at a point where it should be portable, if you are reeding this, and want to really
    help me out, it would be swell to hear how installing NicLink goes. requirements.txt should
    have the python requirements. (see ## requirements for non-pip requirements)

# what I did (bash):

I created the venv for niclink to live in.

    cd ~/NicLink/

    python -m venv nicsoft  - This creates a python venv in nicsoft, and should be ran in the
                              NicLink root dir

    . ./activate    - this uses a lille convenance script, but basically all you have to
                              do is source ./bin/activate
                                  (other file extensions if not in bash (or zsh))

then I installed the python packages in the venv. So within the venv:

`python -m pip install -r requirements.txt`

> In order to setup your python path correctly,
> put a (adjusted for your system) niclink.pth file somewhere in your venv python path.

and modified: - venv/lib/python3.12/site-packages/niclink.pth to add
/home/nrv/dev/NicLink/nicsoft to my pythonpath by adding a file with:

```
/home/nrv/dev/NicLink/nicsoft/
```

## to find out your venv's python path:

> ( while in the venv )

1. go into your python interpreter and do:

```
>> import sys
>> print('\n'.join(sys.path))
```

    1. this will tell you your pythonpath
    2. create a .pth file pointing to the .../NicLink/nicsoft dir in one of the listed dirs on your pythonpath
    3. profit

2. test that NicLink dir was added to your python path:

```
>>> import sys
>>> print('/n'.join(sys.path))
```

and it outputted:
/n/usr/lib64/python312.zip/n/usr/lib64/python3.12/n/usr/lib64/python3.12/lib-dynload/n/home/nrv/.local/lib/python3.12/site-packages/n**editable**.nicsoft-0.1.0.finder.**path_hook**/n/usr/local/lib64/python3.12/site-packages/n/usr/local/lib/python3.12/site-packages/n/usr/lib64/python3.12/site-packages/n/usr/lib/python3.12/site-packages

**_ jazz hands _**

# COMPILIING C++ Easylink and pybind11 module code

> after you set up the python environment and C++ dependancies, and are in the python environment:

    - under gnu/linux + Tux Racer run the bash script updateNicLink.sh. It handles usind cmake
      to create the make files, and compiling them in the build dir. It then moves the .so created
      into the niclink dir for use in the pyenv.

    - I do not develop under any other os, so figure it out I guess. Or, install gentoo.

# Using the board on lichess with the board api

In the ROOT/nicsoft/lichess dir create a dir called lichess_token.
in this dir create a file called token. This will be a plain text file containing
only the text of your lichess auth token.

example:
`filename: nicsoft/lichess/token`
`content: lip_5PIkq4soaF3XyFGvelx`

then cd .. and run python lichess

It can play games that can be played w board API ( only tested rapid and classical ).

The board will beep at you when an incorrect position is on the board.

# Use with gnu/linux:

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

    mount point: /dev/hidraw2

This gives wheel group access to all of your hidraw devices,
but wheel usually has sudo access so they have that anyway with sudo

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
