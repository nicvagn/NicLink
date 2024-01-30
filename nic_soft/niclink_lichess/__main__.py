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

# NicLink shit
import niclink

parser = argparse.ArgumentParser()
parser.add_argument( "--port" )
parser.add_argument( "--tokenfile" )
parser.add_argument( "--correspondence", action="store_true" )
parser.add_argument( "--devmode", action="store_true" )
parser.add_argument( "--quiet", action="store_true" )
parser.add_argument( "--debug", action="store_true" )
args = parser.parse_args()

correspondence = False
if args.correspondence:
    correspondence = True

DEBUG=True # for testing
if args.debug:
    DEBUG = True

DEV=True

TOKEN_FILE='./lichess_token/token'
if args.tokenfile is not None:
    TOKEN_FILE = args.tokenfile

if DEV:
    TOKEN_FILE = './lichess_token/dev_token'

logger = logging.getLogger()
logger.setLevel( logging.DEBUG )
formatter = logging.Formatter( '%(asctime)s %(levelname)s %(module)s %(message)s' )

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
    """ a game on lichess """
    def __init__( self, board_client, nl_inst, game_id, **kwargs ):
        """ Game, the client.board, niclink instance, the game id on lila, idk fam"""
        super().__init__( **kwargs )
        # NicLink instance
        self.nl_inst = nl_inst
        # berserk board_client
        self.board_client = board_client
        # id of the game we are playing
        self.game_id = game_id
        # incoming board stream
        self.stream = board_client.stream_game_state( game_id )
        # current state from stream
        self.current_state = next( self.stream )
        logging.info( f"game init w id: { game_id }" )
 

    def run( self ) -> None:
        for event in self.stream:
            if event['type'] == 'gameState':
                self.handle_state_change( event )
            elif event['type'] == 'chatLine':
                self.handle_chat_line( event )

    def make_move( self, move ):
        """ make a move in a lichess game """
        logging.info( f"move made: { move }" )

        self.board_client.make_move( self.game_id, move )


    def handle_state_change( self, game_state ) -> None:
        """ Handle a state change in the lichess game. """
        # {'type': 'gameState', 'moves': 'd2d3 e7e6 b1c3', 'wtime': datetime.datetime( 1970, 1, 25, 20, 31, 23, 647000, tzinfo=datetime.timezone.utc ), 'btime': datetime.datetime( 1970, 1, 25, 20, 31, 23, 647000, tzinfo=datetime.timezone.utc ), 'winc': datetime.datetime( 1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc ), 'binc': datetime.datetime( 1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc ), 'bdraw': False, 'wdraw': False}

        logging.info( game_state )

        # tmp_chessboard is used to get the current game state from API and parse it into something we can use
        tmp_chessboard = chess.Board()
        moves = game_state['moves'].split( ' ' )
        for move in moves:
            # make the maves on a board    
            tmp_chessboard.push_uci( move )
        
        # set this board as NicLink game board
        self.nl_inst.set_game_board( tmp_chessboard )
        
        logging.info( f"board before move: \n{ self.nl_inst.show_game_board() }" )
        
        # tmp_chessboard.turn == True when white, false when black
        if (tmp_chessboard.turn == self.nl_inst.is_white()):
            logging.info( 'it is our turn' )

            self.nl_inst.await_move() # get the move from niclink

            move = self.nl_inst.get_last_move()
            logging.info( f"move from chessboard { move }" )
   
            logging.info( f'our move: {move}' )
            for attempt in range( 3 ):
                try:
                    # make the move
                    self.make_move( move  )
                    break
                except:
                    e = sys.exc_info()[0]
                    logging.info( f'exception on make_move: {e}' )
                if attempt > 1:
                    logging.debug( f'sleeping before retry' )
                    time.sleep( 3 )



    def handle_chat_line( self, chat_line ):
        print( chat_line )
        pass


def main():
    simplejson_spec = importlib.util.find_spec( "simplejson" )
    if simplejson_spec is not None:
        print( f'ERROR: simplejson is installed. The berserk lichess client will not work with simplejson. Please remove the module. Aborting.' )
        sys.exit(-1 )

    nl_inst = niclink.NicLink( refresh_delay=2 )
    
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
        if DEBUG:
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

    # main program loop
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
                        game = Game( client.board, nl_inst, game_data['id'] )
                        game.daemon = True
                        game.start() # start the game thread
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

