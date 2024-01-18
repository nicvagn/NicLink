#!/bin/bash
# update the NicLink package
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd $SCRIPT_DIR/build
cmake $SCRIPT_DIR/src
make

cp -f $SCRIPT_DIR/build/*.so $SCRIPT_DIR/pip_package/NicLink

echo "NicLink in pip_package updated."
