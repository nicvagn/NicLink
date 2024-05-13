#!/usr/bin/env bash
# make a special test_NicLink dir
echo "WARN - will fetch python requirements, but Not C++ ones"

mkdir -p ~/test_Niclink/NicLink/build

cd ~/test_Niclink/
echo "Cloning NicLink into your Home folder."

git clone https://github.com/nicvagn/NicLink 

echo "cloning submodules"
cd NicLink
git submodule update --init --recursive .



echo "making python virtual env"
python3 -m venv venv 

echo "entering the venv"
. ~/test_Niclink/venv/bin/activate

echo "ensuring the python package manager is installed"
python -m ensurepip --upgrade


cd ~/test_Niclink/NicLink/nicsoft/

python -m pip install -r requirements.txt

echo "building NicLink"
./updateNicLink.sh

