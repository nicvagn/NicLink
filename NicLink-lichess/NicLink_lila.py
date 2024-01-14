# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU General Public License for more details. You should have received a copy of 
# the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>. 
# (utf-8) - Nicolas Vaagen "nrv"

# sys - IDK
import sys
import os
import time
import logging
import logging.handlers
import traceback
import argparse
import threading
import importlib

#chess
import chess
import chess.pgn

#lichess API 
import berserk

# chessnut air (NicLink)
import NicLink

parser = argparse.ArgumentParser()
parser.add_argument("--port")
parser.add_argument("--tokenfile")
parser.add_argument("--calibrate", action="store_true")
parser.add_argument("--addpiece", action="store_true")
parser.add_argument("--correspondence", action="store_true")
parser.add_argument("--devmode", action="store_true")
parser.add_argument("--quiet", action="store_true")
parser.add_argument("--debug", action="store_true")
args = parser.parse_args()

# try to set up NicLink
try:
    nicLink = NicLink.connect()
except RuntimeError:
    print(f"ERROR: unable to connect to chessboard.")
    sys.exit(-1)

# the gameid of the active game
game_id = None;

portname = "auto"
if args.port is not None:
    portname = args.port

TOKEN_FILE = "../lichess_token/token"

if args.tokenfile is not None:
    TOKEN_FILE = args.tokenfile

correspondence = False
if args.correspondence:
    correspondence = True

DEBUG=True # for dev
if args.debug:
    DEBUG=True

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levejname)s %(module)s %(messages)s')

"""
# keep track of the chess game for leagal moves etc
"""
class Game(threading.Thread):

    def handleStateChange(self, gameState):
        print(gameState)


    #handle chat from opponent
    def handleChatLine(self, chatLine):
        print(chatLine)
        pass

#nic modifyed
def main():
    simplejson_spec = importlib.util.find_spec("simplejson")
    if simplejson_spec is not None:
        print(f'ERROR: simplejson is installed. The berserk lichess client will not work with simplejson. Please remove the module. Aborting.')
        sys.exit(-1)

    try:
        logging.info(f'reading token from {TOKEN_FILE}')
        with open(TOKEN_FILE) as f:
            token = f.read().strip()
    except FileNotFoundError:
        print(f'ERROR: cannot find token file')
        sys.exit(-1)
    except PermissionError:
        print(f'ERROR: permission denied on token file')
        sys.exit(-1)

    try:
        session = berserk.TokenSession(token)
    except:
        e = sys.exc_info()[0]
        print(f"cannot create session: {e}")
        logging.info(f'cannot create session {e}')
        sys.exit(-1)

    try:
        if args.devmode:
            client = berserk.Client(session, base_url="https://lichess.dev")
        else:
            client = berserk.Client(session)
    except:
        e = sys.exc_info()[0]
        logging.info(f'cannot create lichess client: {e}')
        print(f"cannot create lichess client: {e}")
        sys.exit(-1)

    def is_correspondence(gameId):
        try:
            for game in client.games.get_ongoing():
                if game['gameId'] == gameId:
                    if game['speed'] == "correspondence":
                        return True
        except:
            e = sys.exc_info()[0]
            print(f"cannot determine game speed: {e}")
            logging.info(f'cannot determine if game is correspondence: {e}')
            return False
        return False

    # main game loop
    while True:
        try:
            logging.debug(f'board event loop')
            for event in client.board.stream_incoming_events():
                if event["type"] == "challenge":
                    print("Challenge retreived")
                    print(event)
                elif event["type"] == "gameStart":
                    # {'type': 'gameStart', 'game': {'id': 'pCHwBReX'}}
                    game_data = event["game"] # store the game data from api
                    logging.info(f"game start recieved: {game_data['id']}")
        
                    # check for correspondance
                    if not correspondence:
                        if is_correspondence(game_data['id']):
                            logging.info(f"skipping corespondance game: {game_data["id"]}")
                            continue
                    try:


                        game = Game # TODO !!!!
                        game.daemon = True
                        game.start()
                    except berserk.exceptions.ResponseError as e:
                            if 'This game cannot be played with the Board API' in str(e):
                                print('cannot play this game via board api')
                            logging.info(f'ERROR: {e}')
                            continue

                    # new game
                    game = Game()
                    # TODO REFRANCE ON LN 23O CERBITO SRC                  


    
        except berserk.exceptions.ResponseError as e:
            print(f'ERROR: Invalid server response: {e}')
            logging.info('Invalid server response: {e}')
            if 'Too Many Requests for url' in str(e):
                time.sleep(10)


"""
# create a new game. This will involve creating a refrance game in our code.\
"""
def newGame(game_id):
    gameBoard = chess.Board()
    game = Game()
    

if __name__ == '__main__':
    main()
