#!/bin/bash

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

NUM_THREADS=$(grep -c ^processor /proc/cpuinfo)  # use all the cpu 

# make a build dir if non exists
mkdir -p $SCRIPT_DIR/build
# enter build dir
cd $SCRIPT_DIR/build

# clean
../clean.sh

# cmake
cmake ../src 

# build a new
make -j $NUM_THREADS

# move into the niclink module
cp -f _nic*.so ../nicsoft/niclink

echo "Moved _niclinkCPYTHONNONSENSE.so to ../nicsoft/niclink/_niclinkCPYNONSENSE.so"
