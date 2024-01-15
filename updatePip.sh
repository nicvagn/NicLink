#!/bin/bash
# update the NicLink package in your python3.12 packages for Pip
cd ./build
cmake ../src
make

cp -fr ~/dev/NicLink/pip_package/NicLink /home/nrv/.local/lib/python3.12/site-packages
