#!/bin/bash

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

cd $SCRIPT_DIR/build

../clean.sh

cmake ../src 

make

cp -f *.so NicLink
