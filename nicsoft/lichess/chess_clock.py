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


def setup_logging():
    logger = logging.getLogger("ChessClock")
    logger.warning(f"logger created for ChessClock")

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
    """Usage example:
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

    def __init__(self, port=None, baud_rate=9600):
        """Initialize chess clock

        Args:
            port: Specific serial port (optional, will auto-detect if None)
            baud_rate: Serial baud rate (default 9600)
        """
        self.logger = setup_logging()
        self.logger.error("LOGGING SETUP FOR CHESS CLOCK")
        self.clock_serial = None
        self.port = port
        self.baud_rate = baud_rate
        self.is_connected = False
        self.last_move_count = 0
        self.clock_running = False

        if port:
            self.connect_to_port(port)
        else:
            self.auto_detect_and_connect()

    def auto_detect_and_connect(self):
        """Try to find and connect to Arduino chess clock automatically"""
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
                "/dev/ttyUSB0",
                "/dev/ttyUSB1",
                "/dev/ttyACM0",
                "/dev/ttyACM1",
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
        """Connect to specific serial port"""
        try:
            self.clock_serial = serial.Serial(port, self.baud_rate, timeout=1)
            self.port = port
            self.is_connected = True
            self.logger.info(f"Chess clock connected on {port}")

            time.sleep(2)

            # Read startup message
            if self.clock_serial.in_waiting:
                startup_msg = (
                    self.clock_serial.readline()
                    .decode("utf-8", errors="ignore")
                    .strip()
                )
                self.logger.info(f"Clock startup: {startup_msg}")

            return True

        except Exception as e:
            self.logger.debug(f"Failed to connect to {port}: {e}")
            self.is_connected = False
            return False

    def send_command(self, command):
        """Send command to chess clock

        Args:
            command: Command string to send

        Returns:
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

        except Exception as e:
            self.logger.error(f"Failed to send command to chess clock: {e}")
            self.is_connected = False
            return None

    def game_over(self):
        """Display the game over and reset clock"""
        self.send_command("OVER")

    def white_won(self):
        """Display white won by mate"""
        self.send_command("BMATE")

    def black_won(self):
        """Display black won by mate"""
        self.send_command("WMATE")

    def set_time(self, seconds, increment=0):
        """Set initial time and increment

        Args:
            seconds: Initial time in seconds for each player
            increment: Increment in seconds per move (default 0)

        Returns:
            bool: True if successful
        """
        self.send_command(f"TIME:{seconds}:{increment}")

    def start(self):
        """Start the chess clock"""
        self.send_command("START")
        self.clock_running = True
        self.logger.info("Clock started")

    def stop(self):
        """Stop/pause the chess clock"""
        self.send_command("STOP")
        self.clock_running = False
        self.logger.info("Clock stopped")

    def reset(self):
        """Reset clock to default (60 seconds)"""
        self.send_command("RESET")
        self.last_move_count = 0
        self.clock_running = False
        self.logger.info("Clock reset")

    def get_status(self):
        """Get current clock status

        Returns:
            dict: Clock status with keys: white_time, black_time, increment, running, to_play
        """
        response = self.send_command("STATUS")
        if response and response.startswith("STATUS:"):
            parts = response.split(":")
            if len(parts) == 6:
                return {
                    "white_time": int(parts[1]),
                    "black_time": int(parts[2]),
                    "increment": int(parts[3]),
                    "running": parts[4] == "RUNNING",
                    "to_play": parts[5],
                }
        raise RuntimeException("Could not parse response %s", response)

    def send_move(self):
        """Send move signal to chess clock"""
        self.send_command("m")

    def handle_game_state(self, game_state):
        """Process game state and send move to clock if needed"""
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

        moves = game_state.moves.split() if game_state.moves else []
        current_move_count = len(moves)

        if current_move_count > self.last_move_count:
            self.send_move()

            self.last_move_count = current_move_count

    def configure_for_game(self, time_control):
        """Configure clock for a time control

        Args:
            time_control: dict with 'initial' (seconds) and 'increment' (seconds)

        Example:
            clock.configure_for_game({'initial': 300, 'increment': 5})  # 5+5
        """
        initial = time_control.get("initial", 60000)
        increment = time_control.get("increment", 5)

        self.set_time(initial, increment)

        return self.start()

    def disconnect(self):
        """Close serial connection to chess clock"""
        if self.clock_serial and self.clock_serial.is_open:
            try:
                self.clock_serial.close()
                self.logger.info("Chess clock serial connection closed")
            except Exception as e:
                self.logger.error(f"Error closing chess clock connection: {e}")

        self.is_connected = False
        self.clock_serial = None


if __name__ == "__main__":
    # test
    clock = ChessClock()
    clock.get_status()

    clock.configure_for_game({"initial": 300, "increment": 30})
    clock.start()
    x = 1
    print("enter 0 to exit")
    while x != "0":
        clock.send_move()
        x = input()

    clock.black_won()
