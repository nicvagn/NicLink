# NicLink
A python interface for the Chessnut Air. 

The plan is to use this interface together with the berserk API to play on lichess

Uses https://pybind11.readthedocs.io/en/stable/index.html 
    and https://github.com/miguno/EasyLinkSDK
EasyLinkSDK should be cloned into project root.

pyBind should be installed via pip.
ie: pip install pybind11

API key should be in dir called lichess_token and named "token"
If you have a chessnut air, you can start hacking with by running the update_NicLink.sh

as it stands, you must be ROOT to connect to the board. 
IT IS THE ONLY WAY IT CONNECTS
