"""Lichess chess clock."""

#  chess_clock is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  chess_clock is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with chess_clock. If not, see <https://www.gnu.org/licenses/>.
import serial
import sys
import serial.tools.list_ports
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

    def __init__(
        self, game_state=None, port="/dev/ttyACM0", baud_rate=9600, logger=None
    ):
        """Initialize chess clock.

        Args
        ----
            game_state: maybe an initial game state, else None
            port: Specific serial port (optional, will auto-detect if None)
            baud_rate: Serial baud rate (default 9600)
            logger: logger to use, is None one is made
        """
        if logger is None:
            self.logger = setup_logging()
        else:
            self.logger = logger
        self.logger.info("LOGGING SETUP FOR CHESS CLOCK")
        self.clock_serial = None
        self.port = port
        self.baud_rate = baud_rate
        self.is_connected = False
        self.last_move_count = 0
        self.clock_running = False

        if game_state:
            self.wtime: timedelta = game_state.get_wtime()
            self.btime: timedelta = game_state.get_btime()
            self.winc: timedelta = game_state.get_winc()
            self.binc: timedelta = game_state.get_binc()

        if port:
            self.logger.info("connecting to port: %s", port)
            self.connect_to_port(port)
        else:

            self.logger.info("Trying to auto-connect")
            self.auto_detect_and_connect()

    def auto_detect_and_connect(self):
        """Try to find and connect to Arduino chess clock automatically."""
        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if (
                    "Arduino" in port.description
                    or "CH340" in port.description
                    or "USB" in port.description
                ):
                    if self.connect_to_port(port.device):
                        return True

            common_ports = [
                "/dev/ttyACM0",
                "/dev/ttyACM1",
                "/dev/ttyUSB0",
                "/dev/ttyUSB1",
                "COM3",
                "COM4",
                "COM5",
            ]
            for port in common_ports:
                if self.connect_to_port(port):
                    return True

            self.logger.warning("Chess clock not found on any port")
            return False

        except Exception as e:
            self.logger.error(f"Failed to auto-detect chess clock: {e}")
            return False

    def connect_to_port(self, port):
        """Connect to specific serial port."""
        try:
            self.clock_serial = serial.Serial(port, self.baud_rate, timeout=1)
            self.port = port
            self.is_connected = True
            self.logger.info(f"Chess clock connected on {port}")

            return True

        except Exception as e:
            self.logger.debug(f"Failed to connect to {port}: {e}")
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
            self.logger.debug(f"Sent to clock: {command}")

            # Wait briefly for response

            time.sleep(0.1)

            # Read response
            if self.clock_serial.in_waiting:
                response = (
                    self.clock_serial.readline()
                    .decode("utf-8", errors="ignore")
                    .strip()
                )
                self.logger.debug(f"Clock response: {response}")
                return response

            return None

        except RuntimeError as e:
            self.logger.error(f"Failed to send command to chess clock: {e}")
            self.is_connected = False
            return None

    def game_over(self):
        """Display the game over and reset clock."""
        self.send_command("OVER")

    def white_won(self):
        """Display white won by mate."""
        self.send_command("BMATE")

    def black_won(self):
        """Display black won by mate."""
        self.send_command("WMATE")

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
        white_ms = int(wtime.total_seconds() * 1000)
        black_ms = int(btime.total_seconds() * 1000)
        winc_ms = int(winc.total_seconds() * 1000)
        binc_ms = int(binc.total_seconds() * 1000)

        self.logger.info(
            "wtime_ms: %s,  winc_ms: %s, btime_ms: %s, binc_ms: %s",
            white_ms,
            winc_ms,
            black_ms,
            binc_ms,
        )
        # firmware depends on this format
        cmd = f"TIME:{white_ms}+{winc_ms},{black_ms}+{binc_ms}"
        self.logger.info("time_set cmd: %s", cmd)
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

        self.send_command("m")

    def handle_game_state(self, game_state):
        """Process game state and send move to clock if needed."""
        if not hasattr(game_state, "moves"):
            self.logger.warning("GameState has no moves attribute")
            return
        if game_state.winner == "black":
            self.black_won()
            return
        if game_state.winner == "white":
            self.white_won()
            return

        if game_state.status != "started":
            self.game_over()
            return

        # send time to clock
        self.set_time(
            game_state.wtime, game_state.btime, game_state.winc, game_state.binc
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

        self.set_time(winit, binit, winc, binc)
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


if __name__ == "__main__":
    test()

#  LocalWords:  BMATE WMATE winit binit binc winc
