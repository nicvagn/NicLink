#!/usr/bin/env bash
# niclink utility script

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

. $SCRIPT_DIR/activate
python $SCRIPT_DIR/nicsoft/turn_out_all_lights.py
