"""Actuator control module - Control servo and ESC via Arduino"""

import time
import RPi.GPIO as GPIO

from config import (
    SENSOR1_SHUTDOWN, SENSOR2_SHUTDOWN, SENSOR3_SHUTDOWN, SENSOR4_SHUTDOWN, SENSOR5_SHUTDOWN,
    SERVO_MIN_PULSE_WIDTH_MS, SERVO_MAX_PULSE_WIDTH_MS,
    NEUTRAL_ANGLE, STOP_PULSE
)
from serial_comm import ArduinoSerial


class Actuator:
    """
    Class to manage servo and ESC (via Arduino)

    Raspberry Pi calculates pulse width and sends it to Arduino via serial.
    Arduino generates PWM pulses to control servo and ESC.
    """

    def __init__(self, serial_port: str = '/dev/serial0'):
        """
        Initialize actuator

        Parameters:
            serial_port: Serial port connected to Arduino
        """
        self._initialize_gpio()

        # Initialize serial communication with Arduino
        self.arduino = ArduinoSerial(port=serial_port)

        # Set initial state (neutral steering, stopped motor)
        self.set_steering_angle(NEUTRAL_ANGLE)
        self.set_speed(STOP_PULSE)
        time.sleep(1)

    def _initialize_gpio(self):
        """Initialize GPIO pins for sensors"""
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # Setup sensor pins
        GPIO.setup(SENSOR1_SHUTDOWN, GPIO.OUT)
        GPIO.setup(SENSOR2_SHUTDOWN, GPIO.OUT)
        GPIO.setup(SENSOR3_SHUTDOWN, GPIO.OUT)
        GPIO.setup(SENSOR4_SHUTDOWN, GPIO.OUT)
        GPIO.setup(SENSOR5_SHUTDOWN, GPIO.OUT)

    def set_steering_angle(self, angle: float):
        """
        Set steering angle

        Parameters:
            angle: Steering angle (-90 to 90 degrees)

        Processing flow:
            1. Convert angle to pulse width (ms)
            2. Convert milliseconds to microseconds
            3. Send to Arduino via serial
        """
        # 1. Convert angle to pulse width (ms)
        pulse_width_ms = ((angle + 90) / 180) * (
            SERVO_MAX_PULSE_WIDTH_MS - SERVO_MIN_PULSE_WIDTH_MS
        ) + SERVO_MIN_PULSE_WIDTH_MS

        # 2. Convert milliseconds to microseconds
        pulse_width_us = int(pulse_width_ms * 1000)

        # 3. Send servo pulse width to Arduino
        self.arduino.send_servo_pulse(pulse_width_us)

    def set_speed(self, pulse_width_ms: float):
        """
        Set motor speed

        Parameters:
            pulse_width_ms: Pulse width in milliseconds

        Processing flow:
            1. Convert milliseconds to microseconds
            2. Send to Arduino via serial
        """
        # 1. Convert milliseconds to microseconds
        pulse_width_us = int(pulse_width_ms * 1000)

        # 2. Send ESC pulse width to Arduino
        self.arduino.send_esc_pulse(pulse_width_us)

    def stop(self):
        """
        Set to stop state

        Set steering to neutral and ESC to stop pulse
        """
        self.set_steering_angle(NEUTRAL_ANGLE)
        self.set_speed(STOP_PULSE)

    def cleanup(self):
        """
        Cleanup

        Stop and disconnect serial communication
        """
        self.stop()
        time.sleep(0.5)
        self.arduino.close()
        print("Actuators cleaned up")
