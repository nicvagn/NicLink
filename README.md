# NicLink - A python interface for the Chessnut Air

# Notice

> version 0.8

> checkout this software, it solves the problem's I wanted to solve with NicLink:

    https://chromewebstore.google.com/detail/chessconnect/dmkkcjpbclkkhbdnjgcciohfbnpoaiam?hl=en-GB

# gotchas

- if: ModuleNotFoundError: No module named 'niclink' make sure your venv is setup, with the .pth file configured.
- Make sure you are in said venv
- make sure you can build the community fork of EasyLinkSDK because I use a basically unmodified version, just w python bindings
  Link: `https://github.com/miguno/EasyLinkSDK`
- if you need, install python3.12 from "deadsnakes" google is your bud.
- if cmake can not find your PYTHON_INCLUDE_DIR OR PYTHON_LIBRARIES:
  ``` bash:
        cmake ../src \
        > -DPYTHON_INCLUDE_DIR=$(python3.12 -c "import sysconfig; print(sysconfig.get_path("include"))") \
        > -DPYTHON_LIBRARY=$(python3.12 -c "import sysconfig.get_config_var('LIBDIR'))")
        ```

# overview

- see the python requirements.txt for external requirements
- run updateNicLink.sh to compile and prepare the env
- only tested on gnu/linux with a chessnut air.
- branches:
  - master: behind the times. More likely to be solid
  - dev: the wild west of new features

## requirements

- get all the required submodules w `git pull recurse-submodules`
- hidraw and spdlog they are internal in src/thirdparty
- in order to compile them on Debian you need:

  - checkout the community fork of the EasylinkSDK and get that building first.
    You have to build that as a component of NicLink
    Link: `https://github.com/miguno/EasyLinkSDK`
  - libudev-dev or on fedora libudev-devel or equivalent on your distros
  - hidapi and hidapi-devel (or -dev)

    - requirements:
    - libusb (https://github.com/libusb/libusb/releases) - this is included as a submodule
    - pybind11-devel in order to compile the code
    - python-dev or python-devel or whatever it is on your distro needed to build pybind code

- pip also obviously
- python 3.12 and python-dev (or python-devel, you need python.h anyway) and python modules listed in requirements.txt
- cmake (3.4 ... 3.20) some distros are behind significantly, so I recommend "pip install cmake" after uninstalling the one from your distro
- modern gcc (I used gcc 13.2) and gcc-c++

  > so you need gcc, cmake, gcc-c++, python-devel, pybind11, pybind11-devel and the kichen sink
  > I satisfied the requirement via: sudo dnf install gcc cmake g++ python-devel pybind11-devel

- if cmake can not find python packages (probably) see setting up a python environment and run cmake from the venv

- If you attempt getting nl set up on your system, I will give you a hand if you need it. I would be interested in reading a log, too!

## Setting up python venv

make sure python-dev (or python-devel or ...) libusb-1.0-0-dev libudev-dev or equivalent are installed

In order to use NicLink while it is in development, it is advised to use a virtual environment. I do not have a good enough understanding,
but you have the internet. ( here is a start: https://python.land/virtual-environments/virtualenv ) Go ham. It is now at a point where it should be portable, if you are reeding this, and want to really help me out,
it would be swell to hear how installing NicLink goes. requirements.txt should have the requirements.

> what I did (bash):

    python -m venv nicsoft  - This creates a python venv in nicsoft, and should be ran in the NicLink root dir
    cd nicsoft              - enter nicsoft
    . ./source_pyvenv.sh    - this uses a lille convenance script, but basically all you have to do is source ./bin/activate (other file extensions if not in bash)

python -m pip install -r requirements.txt - install python requirements, needed to compile and run NicLink

> In order to setup your python path correctly, put the niclink.pth file someware in your venv python path.

for me I modified the niclink.pth file to be: 1. /home/nrv/NicLink

and modified: - nicsoft/lib/python3.12/site-packages/niclink.pth to add {whatever}/NicLink/nicsoft - to my pythonpath with:

```
import os; var = 'SETUPTOOLS_USE_DISTUTILS'; enabled = os.environ.get(var, 'local') == 'local'; enabled and __import__('_distutils_hack').add_shim();
/home/nrv/dev/NicLink/nicsoft/
```

(I no longer recal what the first line does, but if it aint broke, don't fix)

to find out your venv's python path:

( while in the venv )

1. go into your python interpreter and do:

```
>> import sys
>> print('\n'.join(sys.path))
```

> this will tell you your pythonpath 2. create a .pth file pointing to the .../NicLink/nicsoft dir in one of the listed dirs in your pythonpath 3. profit

to test that NicLink dir was added to your python path:

```
>>> import sys
>>> print('/n'.join(sys.path))
```

and it outputted:
/n/usr/lib64/python312.zip/n/usr/lib64/python3.12/n/usr/lib64/python3.12/lib-dynload/n/home/nrv/.local/lib/python3.12/site-packages/n**editable**.nicsoft-0.1.0.finder.**path_hook**/n/usr/local/lib64/python3.12/site-packages/n/usr/local/lib/python3.12/site-packages/n/usr/lib64/python3.12/site-packages/n/usr/lib/python3.12/site-packages

**_ jazz hands _**

## compiling C++ Easylink and pybind11 module code

> after you set up the python environment, and are in said environment

- under gnu/linux + Tux Racer run the bash script updateNicLink.sh. It handles usind cmake
  to create the make files, and compiling them in the build dir. It then moves the .so created
  into the niclink dir for use in the pyenv.

- I do not develop under any other os, so figure it out I guess. Or, install gentoo.

## Using the board on lichess with the board api

In the ROOT/nicsoft/lichess dir create a dir called lichess_token.
in this dir create a file called token. This will be a plain text file containing
only the text of your lichess auth token.

example:
`filename: nicsoft/lichess/token`
`content: lip_5PIkq4soaF3XyFGvelx`

then cd .. and run python lichess

It can play games that can be played w board API ( only tested rapid and classical ).

The board will beep at you when an incorrect position is on the board.

## playing with stockfish

> you can play with stockfish with NicLink!

In order to do so, you should read ./play_stockfish/README.md for further info

> be warned, I have not touched this in a while.

## Connect w bluetooth

not mature enough to doc, but exists (Is a broken mess, save yourself)

## have something to add/suggest?

contact me:

[nicolasvaagen@gmail.com](nicolasvaagen@gmail.com)

or, make a pull request!

# have a great day!
