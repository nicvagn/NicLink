#!/bin/bash

echo "This script must be run . ./activate_pyvenv.sh!!!"

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
source $SCRIPT_DIR/bin/activate
