from ctypes import *
import sys
import os

# get the path of this file
dir_path = os.path.dirname(os.path.realpath(__file__))

#EasyLink = ctypes.CDLL(dir_path + "/libeasylink.so" )

EasyLink = CDLL(dir_path + "/libeasylink.so" )

# test if we can connect from python
EasyLink.testChess()