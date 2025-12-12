"""Serial communication module - Send PWM pulse width to Arduino"""

import serial
import time
from typing import Optional

from config import (
    SERIAL_PORT,
    SERIAL_BAUDRATE,
    SERIAL_TIMEOUT,
    SERVO_MIN_PULSE_WIDTH_US,
    SERVO_MAX_PULSE_WIDTH_US,
    ESC_MIN_PULSE_WIDTH_US,
    ESC_MAX_PULSE_WIDTH_US
)


class ArduinoSerial:
    """
    Class for serial communication with Arduino to send/receive pulse widths

    Communication protocol:
        Servo: "S<pulse_width_us>" e.g., "S1500" -> 1500 microseconds
        ESC:   "E<pulse_width_us>" e.g., "E1500" -> 1500 microseconds
    """

    def __init__(self, port: str = SERIAL_PORT, baudrate: int = SERIAL_BAUDRATE, timeout: float = SERIAL_TIMEOUT):
        """
        Initialize serial port

        Parameters:
            port: Serial port name (default: config.SERIAL_PORT)
            baudrate: Baud rate (default: config.SERIAL_BAUDRATE)
            timeout: Timeout in seconds (default: config.SERIAL_TIMEOUT)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection: Optional[serial.Serial] = None
        self._connect()

    def _connect(self):
        """Connect to serial port"""
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            # Wait for Arduino reset (Arduino resets when serial connection is established)
            time.sleep(2)
            print(f"Serial connected: {self.port} @ {self.baudrate}bps")
        except serial.SerialException as e:
            print(f"Failed to open serial port {self.port}: {e}")
            self.serial_connection = None

    def send_servo_pulse(self, pulse_width_us: int) -> bool:
        """
        Send servo pulse width to Arduino

        Parameters:
            pulse_width_us: Pulse width in microseconds

        Returns:
            True on success, False on failure
        """
        # Constrain pulse width to range defined in config.py
        pulse_width_us = max(SERVO_MIN_PULSE_WIDTH_US, min(SERVO_MAX_PULSE_WIDTH_US, pulse_width_us))

        command = f"S{pulse_width_us}\n"
        return self._send_command(command)

    def send_esc_pulse(self, pulse_width_us: int) -> bool:
        """
        Send ESC pulse width to Arduino

        Parameters:
            pulse_width_us: Pulse width in microseconds

        Returns:
            True on success, False on failure
        """
        # Constrain pulse width to range defined in config.py
        pulse_width_us = max(ESC_MIN_PULSE_WIDTH_US, min(ESC_MAX_PULSE_WIDTH_US, pulse_width_us))

        command = f"E{pulse_width_us}\n"
        return self._send_command(command)

    def _send_command(self, command: str) -> bool:
        """
        Send command to serial port

        Parameters:
            command: Command string to send

        Returns:
            True on success, False on failure
        """
        if self.serial_connection is None or not self.serial_connection.is_open:
            print("Serial connection not available")
            return False

        try:
            self.serial_connection.write(command.encode('utf-8'))
            self.serial_connection.flush()
            return True
        except serial.SerialTimeoutException:
            print(f"Serial write timeout: {command.strip()}")
            return False
        except Exception as e:
            print(f"Serial write error: {e}")
            return False

    def close(self):
        """Close serial port"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("Serial connection closed")

    def __del__(self):
        """Destructor - Ensure serial port is closed"""
        self.close()
