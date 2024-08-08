#!/usr/bin/env bash

SCRIPT_DIR=$( dirname $( readlink -m $( type -p ${0} )))

cd $SCRIPT_DIR

# enter the python venv
source ./activate

python ./nicsoft/test/__main__.py
