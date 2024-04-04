#!/bin/bash

echo "NicLink GO!"

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

cd $SCRIPT_DIR/nicsoft

. ./source_pyvenv.sh

python lichess

echo "Thank you for using NicLink"
