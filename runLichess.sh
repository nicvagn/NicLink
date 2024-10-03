#!/usr/bin/env bash

echo "NicLink GO!"

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

. $SCRIPT_DIR/activate

# we are brought to the script dir by activate
python -m nicsoft.lichess
