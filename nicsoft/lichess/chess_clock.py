"""Lichess chess clock."""

#  chess_clock is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  chess_clock is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with chess_clock. If not, see <https://www.gnu.org/licenses/>.
import serial
import sys
import logging
import time
import datetime
from datetime import timedelta


def setup_logging() -> logging.logger:
    """Init logging for module."""
    logger = logging.getLogger("ChessClock")
    logger.info(f"logger created for ChessClock")
    consoleHandler = logging.StreamHandler(sys.stdout)

    logger.setLevel(logging.DEBUG)
    consoleHandler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(levelno)s %(funcName)s %(lineno)d  %(message)s @: %(pathname)s"
    )

    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)
    return logger


class ChessClock:
    """Lichess chess clock.

    Example
    -------
    # Initialize clock
    clock = ChessClock()

    # Set time control: 5 minutes + 3 second increment
    clock.set_time(300, 3)

    # Start the clock
    clock.start()

    # During game, handle moves
    clock.handle_game_state(game_state)

    # Or manually
    clock.send_move('w')  # White moved

    # Pause
    clock.stop()

    # Check status
    status = clock.get_status()
    print(f"White: {status['white_time']}ms, Black: {status['black_time']}ms")

    # Reset for new game
    clock.reset()
    """

    def __init__(self, game_state=None, baud_rate=9600, logger=None):
        """Initialize chess clock.

        Args
        ----
            game_state: maybe an initial game state, else None
            baud_rate: Serial baud rate (default 9600)
            logger: logger to use, is None one is made
        """
        if logger is None:
            self.logger = setup_logging()
        else:
            self.logger = logger
        self.logger.info("LOGGING SETUP FOR CHESS CLOCK")
        self.clock_serial = None
        self.baud_rate = baud_rate
        self.last_move_count = 0
        self.clock_running = False

        # start with white to move. If there is a game state, that will be used
        self.white_to_move = True

        self.is_connected = self.connect_to_clock()
        if self.is_connected == False:
            self.logger.info("failed to connect.")
            raise RuntimeError("could not connect to chess clock")

        if game_state:
            self.handle_game_state(game_state)

    def connect_to_clock(self) -> bool:
        """Connect to chess clock port. udev rule is needed for the /dev symlink

        Example
        -------
        SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="55d3", SYMLINK+="chess_clock"
        """
        try:
            self.clock_serial = serial.Serial(
                "/dev/chess_clock", self.baud_rate, timeout=1
            )
            self.is_connected = True
            self.logger.info("Chess clock connected")

            return True

        except Exception as e:
            self.logger.debug(f"Failed to connect to port. Raised: %s", e)
            self.is_connected = False
            return False

    def send_command(self, command):
        """Send command to chess clock.

        Args
        ----
            command: Command string to send

        Returns
        -------
            None
        """
        if (
            not self.is_connected
            or not self.clock_serial
            or not self.clock_serial.is_open
        ):
            self.logger.warning(f"Chess clock not connected, cannot send: {command}")
            return None

        try:
            self.clock_serial.write(f"{command}\n".encode())
            self.clock_serial.flush()
            self.logger.debug("Sent to clock: %s", command)

            # Wait briefly for response

            time.sleep(0.1)

            # Read response
            if self.clock_serial.in_waiting:
                response = (
                    self.clock_serial.readline()
                    .decode("utf-8", errors="ignore")
                    .strip()
                )
                self.logger.debug("Clock response: %s", response)
                return response

            return None

        except RuntimeError as e:
            self.logger.error("Failed to send command to chess clock: %s", e)
            self.is_connected = False
            return None

    def game_over(self):
        """Display the game over and reset clock."""
        self.send_command("OVER")

    def white_won(self):
        """Display white won by mate."""
        self.send_command("WWON")

    def black_won(self):
        """Display black won by mate."""
        self.send_command("BWON")

    def set_time(
        self, wtime: timedelta, winc: timedelta, btime: timedelta, binc: timedelta
    ):
        """Set the time displayed on LCD

        Parameters
        ----------
        wtime : timedelta
            whites time
        winc : timedelta
            whites increment time
        btime : timedelta
            blacks time
        binc : timedelta
            blacks increment time

        Returns
        ------
        None
        """
        self.logger.info(
            "wtime: %s,  winc: %s, btime: %s, binc: %s",
            wtime,
            winc,
            btime,
            binc,
        )
        # firmware depends on this format and that the unit is seconds
        cmd = f"TIME:{wtime.total_seconds()}+{winc.total_seconds()},{btime.total_seconds()}+{binc.total_seconds()}"
        self.logger.info("time_set w: %s", cmd)
        self.send_command(cmd)

    def start(self):
        """Start the chess clock."""
        self.send_command("START")
        self.clock_running = True
        self.logger.info("Clock started")

    def stop(self):
        """Stop/pause the chess clock."""
        self.send_command("STOP")
        self.clock_running = False
        self.logger.info("Clock stopped")

    def reset(self):
        """Reset clock to default (60 seconds)."""
        self.send_command("RESET")
        self.last_move_count = 0
        self.clock_running = False
        self.logger.info("Clock reset")

    def get_status(self):
        """Get current clock status.

        Returns
        -------
        dict: Clock status with keys: white_time, black_time, increment, running, to_play
        """
        response = self.send_command("STATUS")
        self.logger.info("cmd STATUS got %s", response)
        if response:
            if response.startswith("STATUS:"):
                parts = response.split(":")

                return {
                    "white_time": parts[1],
                    "black_time": parts[2],
                    "running": (parts[3] == "RUNNING"),
                    "to_play": parts[4],
                }
            else:
                self.logger.warning("Could not parse response: %s", response)
        else:
            self.logger.warning("Clock did not respond to STATUS:")

    def move_made(self, game_state=None):
        """Send move signal to chess clock."""
        self.logger.info("move_made entered, game_state: %s", game_state)
        if game_state:
            self.handle_game_state(game_state)

        if self.white_to_move:
            self.send_command("W")
        else:
            self.send_command("B")

    def handle_game_state(self, game_state):
        """Process game state and set clock."""
        if not hasattr(game_state, "moves"):
            self.logger.warning("GameState has no moves attribute")
            return
        if game_state.winner == "black":
            self.black_won()
            return
        if game_state.winner == "white":
            self.white_won()
            return

        if game_state:
            self.white_to_move = game_state.white_to_move()
        else:
            self.white_to_move = not self.white_to_move

        self.logger.info("chess_clock.white_to_move set to: %s", self.white_to_move)

        # send time to clock
        self.set_time(
            game_state.wtime, game_state.winc, game_state.btime, game_state.binc
        )

    def configure_for_game(self, game_start):
        """Configure clock for a time control.

        Args
        ----
        time_control: dict with "winit", "binit", "winc" and "binc"

        Example
        -------
            clock.configure_for_game({"winit":900, "binit":900, "winc":100, "binc":10})
        """

        winit = game_start.get("winit")
        binit = game_start.get("binit")
        winc = game_start.get("winc")
        binc = game_start.get("binc")

        # sometimes it is an int of elapsed milliseconds?
        if not isinstance(winit, timedelta):
            winit = timdelta(seconds=winit)
            binit = timdelta(seconds=binit)
            winc = timdelta(seconds=winc)
            binc = timdelta(seconds=binc)

        self.set_time(winit, winc, binit, binc)
        return self.start()

    def disconnect(self):
        """Close serial connection to chess clock."""
        if self.clock_serial and self.clock_serial.is_open:
            try:
                self.clock_serial.close()
                self.logger.info("Chess clock serial connection closed")
            except Exception as e:
                self.logger.error(f"Error closing chess clock connection: {e}")

        self.is_connected = False
        self.clock_serial = None


def test():
    global logger
    try:
        logger
    except NameError:
        logger = setup_logging()

    cc = ChessClock(logger=logger)

    whiteTime = datetime.timedelta(seconds=3000)
    blackTime = datetime.timedelta(seconds=3000)
    wInc = datetime.timedelta(seconds=30)
    bInc = datetime.timedelta(seconds=30)

    while True:
        exit = input("EOF to exit")
        whiteTime = whiteTime - wInc
        blackTime = blackTime - bInc
        cc.set_time(whiteTime, wInc, blackTime, bInc)
        cc.move_made()


if __name__ == "__main__":
    test()

#  LocalWords:  BMATE WMATE winit binit binc winc WWON BWON
