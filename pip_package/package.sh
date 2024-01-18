#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd $SCRIPT_DIR

cp -f ../build/NicLink.cpython-312-x86_64-linux-gnu.so NicLink/
