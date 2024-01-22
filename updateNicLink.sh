#!/bin/bash

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

# enter build dir
cd $SCRIPT_DIR/build

# clean
../clean.sh

# cmake
cmake ../src 

# build a new
make

# move into the niclink module
cp -f _nic*.so ../nic_soft/niclink
