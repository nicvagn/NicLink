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

        if port:
            self.connect_to_port(port)
        else:
            self.auto_detect_and_connect()

    def auto_detect_and_connect(self):
        """Try to find and connect to Arduino chess clock automatically"""
        try:
            # Try to find Arduino automatically
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if (
                    "Arduino" in port.description
                    or "CH340" in port.description
                    or "USB" in port.description
                ):
                    if self.connect_to_port(port.device):
                        return True

            # If auto-detect fails, try common ports
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
        """Connect to specific serial port

        Args:
            port: Serial port device path or name

        Returns:
            bool: True if connection successful
        """
        try:
            self.clock_serial = serial.Serial(port, self.baud_rate, timeout=1)
            self.port = port
            self.is_connected = True
            logger.info(f"Chess clock connected on {port}")

            # Wait for Arduino to reset and send ready message
            import time

            time.sleep(2)

            # Clear any startup messages
            if self.clock_serial.in_waiting:
                startup_msg = (
                    self.clock_serial.readline()
                    .decode("utf-8", errors="ignore")
                    .strip()
                )
                logger.debug(f"Clock startup: {startup_msg}")

            return True

        except Exception as e:
            logger.debug(f"Failed to connect to {port}: {e}")
            self.is_connected = False
            return False

    def send_move(self, player):
        """Send move signal to chess clock

        Args:
            player: 'w' or 'white' for white, 'b' or 'black' for black
        """
        if (
            not self.is_connected
            or not self.clock_serial
            or not self.clock_serial.is_open
        ):
            logger.warning("Chess clock not connected, cannot send move")
            return False

        try:
            # Normalize player input
            player_char = player[0].lower()  # 'w' or 'b'

            self.clock_serial.write(player_char.encode())
            self.clock_serial.flush()
            logger.debug(f"Sent '{player_char}' to chess clock")

            # Read any response from clock (for debugging)
            if self.clock_serial.in_waiting:
                response = (
                    self.clock_serial.readline()
                    .decode("utf-8", errors="ignore")
                    .strip()
                )
                logger.debug(f"Clock response: {response}")

            return True

        except Exception as e:
            logger.error(f"Failed to send move to chess clock: {e}")
            self.is_connected = False
            return False

    def handle_game_state(self, game_state):
        """Process game state and send move to clock if needed

        Args:
            game_state: GameState object with moves attribute
        """
        if not hasattr(game_state, "moves"):
            logger.warning("GameState has no moves attribute")
            return

        moves = game_state.moves.split() if game_state.moves else []
        current_move_count = len(moves)

        # Check if a new move was made
        if current_move_count > self.last_move_count:
            # Odd number of moves = white just moved
            # Even number of moves = black just moved
            if current_move_count % 2 == 1:
                self.send_move("w")
            else:
                self.send_move("b")

            self.last_move_count = current_move_count

    def reset(self):
        """Reset move counter for new game"""
        self.last_move_count = 0
        logger.info("Chess clock move counter reset")

    def read_clock_output(self):
        """Read any output from the clock (for debugging)

        Returns:
            str: Output from clock or empty string
        """
        if self.is_connected and self.clock_serial and self.clock_serial.in_waiting:
            try:
                return (
                    self.clock_serial.readline()
                    .decode("utf-8", errors="ignore")
                    .strip()
                )
            except Exception as e:
                logger.error(f"Error reading from clock: {e}")
        return ""

    def reconnect(self):
        """Try to reconnect to the chess clock"""
        self.disconnect()
        if self.port:
            return self.connect_to_port(self.port)
        else:
            return self.auto_detect_and_connect()

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

    def __del__(self):
        """Cleanup on object destruction"""
        self.disconnect()

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.disconnect()
