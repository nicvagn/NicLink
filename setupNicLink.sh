#!/usr/bin/env bash
# make a special test_NicLink dir
echo "WARN - will fetch python requirements, but Not C++ ones"

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

echo "cloning submodules"
cd SCRIPT_DIR

git submodule update --init --recursive .
git pull

echo "making python virtual env"
python3 -m venv venv 

echo "entering the venv"
. ${SCRIPT_DIR}/venv/bin/activate

echo "ensuring the python package manager is installed"
python -m ensurepip --upgrade

echo "installing berserk from the github. The one from pip does not work currently"
cd ${SCRIPT_DIR}
git clone https://github.com/lichess-org/berserk.git/

python -m pip install ${SCRIPT_DIR}/berserk


cd ${SCRIPT_DIR}/NicLink
echo "installing python deps"
python -m pip install -r requirements.txt


echo "building NicLink"
${SCRIPT_DIR}/updateNicLink.sh

