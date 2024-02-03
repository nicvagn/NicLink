#!/bin/bash
# niclink utility script

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

python $SCRIPT_DIR/nic_soft/turn_out_all_lights.py
