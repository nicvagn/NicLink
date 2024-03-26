#  chess_clock is a part of NicLink
#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the gnu general public license as published by the free software foundation, either version 3 of the license, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but without any warranty; without even the implied warranty of merchantability or fitness for a particular purpose. see the gnu general public license for more details.
#
#  you should have received a copy of the gnu general public license along with NicLink. if not, see <https://www.gnu.org/licenses/>.
from time import sleep, perf_counter, sleep
from datetime import datetime, timedelta, timezone
import zmq
import logging

import threading

log = logging.getLogger('chess_clock')
log.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
log.addHandler(ch)

class ChessClock(threading.Thread):
    """set's up a server for an external rasberry pi chess clock"""

    def __init__(self, external_clock_ip, game_id, **kwargs):
        self.super.__init__(**kwargs)
        self.ext_ip = external_clock_ip


def build_time_stamp(spent_time: timedelta, game_time: timedelta) -> str:
    """build a timestamp from a timedelta for a countdown timer in the format %H%M%S"""
    game_secs = game_time.total_seconds()
    game_minutes = int(game_secs / 60) % 60
    game_secs = game_secs - (game_minutes * 60)
    
    spent_secs = spent_time.total_seconds()
    spent_minutes = int(spent_secs / 60) % 60
    spent_secs = spent_secs - (spent_minutes * 60)

    ts = f"{str(game_minutes - spent_minutes)[:5]}:{str(game_secs - spent_secs)[:5]}"
    log.info("calculated ts: %s", ts)
    return ts 


context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")


while True:
    #  Wait for next request from client
    message = socket.recv()
    print(f"Received request: {message}")

    #  Do some 'work'
    sleep(1)

    #  Send reply back to client
    socket.send(b"B: 1:00 || W: 1:00")

while True:
    # calculate time spent
    spent_time = timedelta(seconds=1202, microseconds=490000)
    # build time stamp
    time_stamp = build_time_stamp(spent_time, spent_time) 
    hello = socket.recv()
    #  Send time stamp to client
    socket.send_string(time_stamp)

    sleep(0.5)
