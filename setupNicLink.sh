#!/usr/bin/env bash
# make a special test_NicLink dir
echo "WARN - will fetch python requirements, but Not C++ ones"


SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
cd $SCRIPT_DIR/test_Niclink

mkdir -p ${SCRIPT_DIR}/NicLink
echo "Cloning NicLink into your Home folder."

git clone https://github.com/nicvagn/NicLink 

echo "cloning submodules"
cd NicLink
git submodule update --init --recursive .



echo "making python virtual env"
python3 -m venv venv 

echo "entering the venv"
. ${SCRIPT_DIR}/venv/bin/activate

echo "ensuring the python package manager is installed"
python -m ensurepip --upgrade

cd ${SCRIPT_DIR}/NicLink
echo "installing python deps"
python -m pip installing -r requirements.txt


echo "building NicLink"
./updateNicLink.sh

