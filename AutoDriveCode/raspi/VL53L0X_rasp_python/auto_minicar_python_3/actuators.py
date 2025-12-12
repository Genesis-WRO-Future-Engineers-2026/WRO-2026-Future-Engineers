"""アクチュエーター制御モジュール - Arduino経由でサーボとESCを制御"""

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
    サーボとESCを管理するクラス（Arduino経由）

    Raspberry Piでパルス幅を計算し、シリアル通信でArduinoに送信。
    Arduinoがパルス波を生成してサーボ・ESCを制御します。
    """

    def __init__(self, serial_port: str = '/dev/serial0'):
        """
        初期化

        Parameters:
            serial_port: Arduinoと接続するシリアルポート
        """
        self._initialize_gpio()

        # Arduino とのシリアル通信を初期化
        self.arduino = ArduinoSerial(port=serial_port)

        # 初期状態に設定（ニュートラル・停止）
        self.set_steering_angle(NEUTRAL_ANGLE)
        self.set_speed(STOP_PULSE)
        time.sleep(1)

    def _initialize_gpio(self):
        """センサー用のGPIOピンを初期化"""
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # センサー用ピンを設定
        GPIO.setup(SENSOR1_SHUTDOWN, GPIO.OUT)
        GPIO.setup(SENSOR2_SHUTDOWN, GPIO.OUT)
        GPIO.setup(SENSOR3_SHUTDOWN, GPIO.OUT)
        GPIO.setup(SENSOR4_SHUTDOWN, GPIO.OUT)
        GPIO.setup(SENSOR5_SHUTDOWN, GPIO.OUT)

    def set_steering_angle(self, angle: float):
        """
        ステアリング角度を設定

        Parameters:
            angle: ステアリング角度（-90～90度）

        処理の流れ:
            1. 角度をパルス幅（ms）に変換
            2. ミリ秒をマイクロ秒に変換
            3. Arduinoにシリアル送信
        """
        # 1. 角度をパルス幅（ms）に変換
        pulse_width_ms = ((angle + 90) / 180) * (
            SERVO_MAX_PULSE_WIDTH_MS - SERVO_MIN_PULSE_WIDTH_MS
        ) + SERVO_MIN_PULSE_WIDTH_MS

        # 2. ミリ秒をマイクロ秒に変換
        pulse_width_us = int(pulse_width_ms * 1000)

        # 3. Arduinoにサーボパルス幅を送信
        self.arduino.send_servo_pulse(pulse_width_us)

    def set_speed(self, pulse_width_ms: float):
        """
        モーター速度を設定

        Parameters:
            pulse_width_ms: パルス幅（ms）

        処理の流れ:
            1. ミリ秒をマイクロ秒に変換
            2. Arduinoにシリアル送信
        """
        # 1. ミリ秒をマイクロ秒に変換
        pulse_width_us = int(pulse_width_ms * 1000)

        # 2. ArduinoにESCパルス幅を送信
        self.arduino.send_esc_pulse(pulse_width_us)

    def stop(self):
        """
        停止状態に設定

        ステアリングをニュートラル、ESCを停止パルスに設定
        """
        self.set_steering_angle(NEUTRAL_ANGLE)
        self.set_speed(STOP_PULSE)

    def cleanup(self):
        """
        クリーンアップ

        停止状態にしてからシリアル通信を切断
        """
        self.stop()
        time.sleep(0.5)
        self.arduino.close()
        print("Actuators cleaned up")
