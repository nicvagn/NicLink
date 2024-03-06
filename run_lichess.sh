#!/bin/bash

echo "NicLink GO!"

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

cd $SCRIPT_DIR/nicsoft

python lichess_NicLink

echo "Thank you for using NicLink"
