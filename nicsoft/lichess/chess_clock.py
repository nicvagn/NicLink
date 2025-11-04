#  chess_clock is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  chess_clock is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with chess_clock. If not, see <https://www.gnu.org/licenses/>.
import serial
import serial.tools.list_ports
import logging

logger = logging.getLogger(__name__)


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

            logger.warning("Chess clock not found on any port")
            return False

        except Exception as e:
            logger.error(f"Failed to auto-detect chess clock: {e}")
            return False

    def connect_to_port(self, port):
        """Connect to specific serial port"""
        try:
            self.clock_serial = serial.Serial(port, self.baud_rate, timeout=1)
            self.port = port
            self.is_connected = True
            logger.info(f"Chess clock connected on {port}")

            import time

            time.sleep(2)

            # Read startup message
            if self.clock_serial.in_waiting:
                startup_msg = (
                    self.clock_serial.readline()
                    .decode("utf-8", errors="ignore")
                    .strip()
                )
                logger.info(f"Clock startup: {startup_msg}")

            return True

        except Exception as e:
            logger.debug(f"Failed to connect to {port}: {e}")
            self.is_connected = False
            return False

    def send_command(self, command):
        """Send command to chess clock

        Args:
            command: Command string to send

        Returns:
            str: Response from clock or None
        """
        if (
            not self.is_connected
            or not self.clock_serial
            or not self.clock_serial.is_open
        ):
            logger.warning(f"Chess clock not connected, cannot send: {command}")
            return None

        try:
            self.clock_serial.write(f"{command}\n".encode())
            self.clock_serial.flush()
            logger.debug(f"Sent to clock: {command}")

            # Wait briefly for response
            import time

            time.sleep(0.1)

            # Read response
            if self.clock_serial.in_waiting:
                response = (
                    self.clock_serial.readline()
                    .decode("utf-8", errors="ignore")
                    .strip()
                )
                logger.debug(f"Clock response: {response}")
                return response

            return None

        except Exception as e:
            logger.error(f"Failed to send command to chess clock: {e}")
            self.is_connected = False
            return None

    def set_time(self, seconds, increment=0):
        """Set initial time and increment

        Args:
            seconds: Initial time in seconds for each player
            increment: Increment in seconds per move (default 0)

        Returns:
            bool: True if successful
        """
        response = self.send_command(f"TIME:{seconds}:{increment}")
        if response and response.startswith("TIME_SET"):
            logger.info(f"Clock time set: {seconds}s + {increment}s increment")
            return True
        return False

    def start(self):
        """Start the chess clock"""
        response = self.send_command("START")
        if response == "CLOCK_STARTED":
            self.clock_running = True
            logger.info("Clock started")
            return True
        return False

    def stop(self):
        """Stop/pause the chess clock"""
        response = self.send_command("STOP")
        if response == "CLOCK_STOPPED":
            self.clock_running = False
            logger.info("Clock stopped")
            return True
        return False

    def reset(self):
        """Reset clock to default (60 seconds)"""
        response = self.send_command("RESET")
        if response == "CLOCK_RESET":
            self.last_move_count = 0
            self.clock_running = False
            logger.info("Clock reset")
            return True
        return False

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
        return None

    def send_move(self, player):
        """Send move signal to chess clock

        Args:
            player: 'w' or 'white' for white, 'b' or 'black' for black
        """
        if not self.clock_running:
            logger.warning("Clock not running, ignoring move")
            return False

        player_char = player[0].lower()
        response = self.send_command(player_char)

        if response and "MOVED" in response:
            logger.debug(f"Move registered: {response}")
            return True
        return False

    def handle_game_state(self, game_state):
        """Process game state and send move to clock if needed"""
        if not hasattr(game_state, "moves"):
            logger.warning("GameState has no moves attribute")
            return

        moves = game_state.moves.split() if game_state.moves else []
        current_move_count = len(moves)

        if current_move_count > self.last_move_count:
            if current_move_count % 2 == 1:
                self.send_move("w")
            else:
                self.send_move("b")

            self.last_move_count = current_move_count

    def configure_for_game(self, time_control):
        """Configure clock based on lichess time control

        Args:
            time_control: dict with 'initial' (seconds) and 'increment' (seconds)

        Example:
            clock.configure_for_game({'initial': 300, 'increment': 5})  # 5+5
        """
        initial = time_control.get("initial", 300)
        increment = time_control.get("increment", 0)

        if self.set_time(initial, increment):
            return self.start()
        return False

    def disconnect(self):
        """Close serial connection to chess clock"""
        if self.clock_serial and self.clock_serial.is_open:
            try:
                self.clock_serial.close()
                logger.info("Chess clock serial connection closed")
            except Exception as e:
                logger.error(f"Error closing chess clock connection: {e}")

        self.is_connected = False
        self.clock_serial = None
