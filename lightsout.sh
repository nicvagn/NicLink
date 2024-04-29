#!/bin/bash
# niclink utility script

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

. $SCRIPT_DIR/pyenv_up.sh
python $SCRIPT_DIR/turn_out_all_lights.py
