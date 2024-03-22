#  chess_clock is a part of NicLink
#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the gnu general public license as published by the free software foundation, either version 3 of the license, or (at your option) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but without any warranty; without even the implied warranty of merchantability or fitness for a particular purpose. see the gnu general public license for more details.
#
#  you should have received a copy of the gnu general public license along with NicLink. if not, see <https://www.gnu.org/licenses/>.
from subprocess import Popen, PIPE
from time import sleep, perf_counter
from datetime import datetime, timedelta, timezone
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
import logging

log = logging.getLogger('simple_example')
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

# Modify this if you have a different sized character LCD
lcd_columns = 16
lcd_rows = 2


"""
physical layout
pi  lcd
#22 rs
#17 enable
#6  d4
#13 d5
#19 d6
#26 d7
"""
lcd_rs = digitalio.DigitalInOut(board.D22)
lcd_en = digitalio.DigitalInOut(board.D17)
lcd_d4 = digitalio.DigitalInOut(board.D6)
lcd_d5 = digitalio.DigitalInOut(board.D13)
lcd_d6 = digitalio.DigitalInOut(board.D19)
lcd_d7 = digitalio.DigitalInOut(board.D26)


# Initialise the lcd class
lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                      lcd_d7, lcd_columns, lcd_rows)


def timedelta_from_millis(millis: float) -> timedelta:
    """Return a timedelta (A duration expressing the difference between two datetime or date instances to microsecond resolution.)
    for a given milliseconds.
    """
    return timedelta(milliseconds=millis)


def run_cmd(cmd):
    """run a shell comand, return as asci"""
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output.decode('ascii')

# wipe LCD screen before we start
lcd.clear()


def display(message: str) -> None:
    """clear lcd then display a message on the 2 x 16 LCD"""
    lcd.clear()
    lcd.message = message

def build_time_stamp(spent_time: timedelta, game_time: timedelta) -> str:
    """build a timestamp from a timedelta for a countdown timer in the format %H%M%S"""
    game_secs = game_time.total_seconds()
    game_minutes = int(game_secs / 60) % 60
    game_secs = game_secs - (game_minutes * 60)
    
    spent_secs = spent_time.total_seconds()
    spent_minutes = int(spent_secs / 60) % 60
    spent_secs = spent_secs - (spent_minutes * 60)

    ts = f"{game_minutes - spent_minutes}:{game_secs - spent_secs}"
    log.info("calculated ts: %s", ts)
    return ts

def minutes_to_millis(minutes) -> float:
    """convert milliseconds to minutes"""
    return minutes * 6000

def update_time_display(w_time: str, b_time: str) -> None:
    """update the time display for display on a 2 X 16 LCD"""
    lcd_message = f"W: {w_time} \nB: {b_time}"
    
    display(lcd_message)

start_time = datetime.now(timezone.utc)
game_time_mins = 2
game_time = timedelta_from_millis(minutes_to_millis(game_time_mins))
fin_time = start_time + game_time


while True:
    # calculate time spent
    spent_time = abs(start_time - datetime.now(timezone.utc))
    # build time stamp
    time_stamp = build_time_stamp(spent_time, game_time) 
    # display the time stamp on lcd
    update_time_display(time_stamp, time_stamp)
    log.info("Time Stamp: %s", time_stamp)
    log.info("is now > fin_time? %s", str(datetime.now(timezone.utc) >= fin_time))
    if(datetime.now(timezone.utc) >= fin_time):
        display("Time is up")
        break
    sleep(0.5)

print("exited loop")

