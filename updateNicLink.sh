#!/usr/bin/env bash

THIS_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

NUM_THREADS=$(grep -c ^processor /proc/cpuinfo)  # use all the cpu 


# make a build dir if non exists
mkdir -p $THIS_DIR/build
# enter build dir
cd $THIS_DIR/build

# clean
../clean.sh

# cmake
cmake ../src 

# build a new
make -j $NUM_THREADS

# move into the niclink module
cp -f _nic*.so ${THIS_DIR}/nicsoft/niclink

echo "Moved executable to ../nicsoft/niclink/_niclinkCPYNONSENSE.so"
