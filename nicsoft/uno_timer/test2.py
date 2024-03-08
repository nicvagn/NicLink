from pyfirmata import Arduino, util, STRING_DATA

board = Arduino("/dev/ttyACM0")
board.send_sysex( STRING_DATA, util.str_to_two_byte_iter('fuck') )

def msg( text ):
    if text:
        board.send_sysex( STRING_DATA, util.str_to_two_byte_iter( text ) )

msg("reeeeeeeeeeeeee")
