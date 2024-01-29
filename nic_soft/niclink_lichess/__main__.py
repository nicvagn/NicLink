#  NicLink-lichess is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink-lichess is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>. 

# sys stuff
import sys
import time
import logging
import logging.handlers
import os
import argparse
import threading
import importlib

# chess stuff
import chess.pgn
import chess
import berserk

#NicLink shit
import niclink

parser = argparse.ArgumentParser()
parser.add_argument( "--port" )
parser.add_argument( "--tokenfile" )
parser.add_argument( "--correspondence", action="store_true" )
parser.add_argument( "--devmode", action="store_true" )
parser.add_argument( "--quiet", action="store_true" )
parser.add_argument( "--debug", action="store_true" )
args = parser.parse_args()


TOKEN_FILE='./lichess_token/token'
if args.tokenfile is not None:
    TOKEN_FILE = args.tokenfile

correspondence = False
if args.correspondence:
    correspondence = True

DEBUG=True # for testing
if args.debug:
    DEBUG = True

logger = logging.getLogger()
logger.setLevel( logging.DEBUG )
formatter = logging.Formatter( '%( asctime )s %( levelname )s %( module )s %( message )s' )

if not args.quiet:
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter( formatter )
    logger.addHandler( consoleHandler )

# log unhandled exceptions to the log file
def my_excepthook( excType, excValue, traceback, logger=logger ):
    logger.error( "Uncaught exception",
                 exc_info=( excType, excValue, traceback ) )
sys.excepthook = my_excepthook

logging.info( "NicLink_lichess startup" )

class Game( threading.Thread ):
    def __init__( self, client, niclink, game_id, **kwargs ):
        super().__init__( **kwargs )
        self.niclink = niclink
        self.current_state = next( self.stream )

    def run( self ):
        for event in self.stream:
            if event['type'] == 'gameState':
                self.handle_state_change( event )
            elif event['type'] == 'chatLine':
                self.handle_chat_line( event )

    def make_move:
        """ make a move in a lichess game """


    def handle_state_change( self, game_state ):
        # {'type': 'gameState', 'moves': 'd2d3 e7e6 b1c3', 'wtime': datetime.datetime( 1970, 1, 25, 20, 31, 23, 647000, tzinfo=datetime.timezone.utc ), 'btime': datetime.datetime( 1970, 1, 25, 20, 31, 23, 647000, tzinfo=datetime.timezone.utc ), 'winc': datetime.datetime( 1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc ), 'binc': datetime.datetime( 1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc ), 'bdraw': False, 'wdraw': False}

        print( game_state )
        tmp_chessboard = chess.Board()
        moves = game_state['moves'].split( ' ' )
        self.niclink.set_game_board_FEN( chess.STARTING_BOARD_FEN )
        for move in moves:
            self.niclink.make_move_game_board( move )
            print( move )
        if tmp_chessboard.turn == niclink.get_color():
            logging.info( 'it is our turn' )
            logging.info( f'our move: {moves}' )
            for attempt in range( 3 ):
                try:
                    self.niclink.await_move()
                    break
                except:
                    e = sys.exc_info(  )[0]
                    logging.info( f'exception on make_move: {e}' )
                if attempt > 1:
                    logging.debug( f'sleeping before retry' )
                    time.sleep( 3 )

            # get the move from niclink        
            move = self.niclink.get_last_move()
            # make the move

    def handle_chat_line( self, chat_line ):
        print( chat_line )
        pass


def main():
    simplejson_spec = importlib.util.find_spec( "simplejson" )
    if simplejson_spec is not None:
        print( f'ERROR: simplejson is installed. The berserk lichess client will not work with simplejson. Please remove the module. Aborting.' )
        sys.exit(-1 )

    niclink = niclink.niclink.NicLink( refresh_delay=2 )
    
    try:
        logging.info( f'reading token from {TOKEN_FILE}' )
        with open( TOKEN_FILE ) as f:
            token = f.read().strip()
    except FileNotFoundError:
        print( f'ERROR: cannot find token file' )
        sys.exit( -1 )
    except PermissionError:
        print( f'ERROR: permission denied on token file' )
        sys.exit( -1 )

    try:
        session = berserk.TokenSession( token )
    except:
        e = sys.exc_info(  )[0]
        print( f"cannot create session: {e}" )
        logging.info( f'cannot create session {e}' )
        sys.exit( -1 )

    try:
        if args.devmode:
            client = berserk.Client( session, base_url="https://lichess.dev" )
        else:
            client = berserk.Client( session )
    except:
        e = sys.exc_info()[0]
        logging.info( f'cannot create lichess client: {e}' )
        print( f"cannot create lichess client: {e}" )
        sys.exit( -1 )

    def is_correspondence( gameId ):
        try:
            for game in client.games.get_ongoing(  ):
                if game['gameId'] == gameId:
                    if game['speed'] == "correspondence":
                        return True
        except:
            e = sys.exc_info()[0]
            print( f"cannot determine game speed: {e}" )
            logging.info( f'cannot determine if game is correspondence: {e}' )
            return False
        return False

    while True:
        try:
            logging.debug( f'==== board event loop ====' )
            for event in client.board.stream_incoming_events():
                if event['type'] == 'challenge':
                    print( "Challenge received" )
                    print( event )
                elif event['type'] == 'gameStart':
                    # {'type': 'gameStart', 'game': {'id': 'pCHwBReX'}}
                    game_data = event['game']
                    logging.info( f"game start received: {game_data['id']}" )

                    # check if game speed is correspondence, skip those if --correspondence argument is not set
                    if not correspondence:
                        if is_correspondence( game_data['id'] ):
                            logging.info( f"skipping corespondence game: {game_data['id']}" )
                            continue

                    try:
                        game = Game( client, niclink, game_data['id'] )
                        game.daemon = True
                        game.start()
                    except berserk.exceptions.ResponseError as e:
                        if 'This game cannot be played with the Board API' in str( e ):
                            print( 'cannot play this game via board api' )
                        logging.info( f'ERROR: {e}' )
                        continue


        except berserk.exceptions.ResponseError as e:
            print( f'ERROR: Invalid server response: {e}' )
            logging.info( 'Invalid server response: {e}' )
            if 'Too Many Requests for url' in str( e ):
                time.sleep( 10 )

if __name__ == '__main__':
    main()

