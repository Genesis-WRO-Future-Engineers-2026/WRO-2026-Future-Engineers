"""アクチュエーター制御モジュール - サーボとESCの制御"""

import time
import RPi.GPIO as GPIO

from config import (
    SENSOR1_SHUTDOWN, SENSOR2_SHUTDOWN, SENSOR3_SHUTDOWN, SENSOR4_SHUTDOWN, SENSOR5_SHUTDOWN,
    SERVO_PIN, ESC_PIN, PWM_FREQUENCY,
    SERVO_MIN_PULSE_WIDTH_MS, SERVO_MAX_PULSE_WIDTH_MS,
    NEUTRAL_ANGLE, STOP_PULSE
)


class Actuator:
    """サーボとESCを管理するクラス"""

    def __init__(self):
        """GPIO初期化"""
        self.servo_pwm = None
        self.esc_pwm = None
        self._initialize_gpio()

    def _initialize_gpio(self):
        """GPIOピンを初期化"""
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # センサー用ピンを設定
        GPIO.setup(SENSOR1_SHUTDOWN, GPIO.OUT)
        GPIO.setup(SENSOR2_SHUTDOWN, GPIO.OUT)
        GPIO.setup(SENSOR3_SHUTDOWN, GPIO.OUT)
        GPIO.setup(SENSOR4_SHUTDOWN, GPIO.OUT)
        GPIO.setup(SENSOR5_SHUTDOWN, GPIO.OUT)

        # サーボとESCのピンを設定
        GPIO.setup(SERVO_PIN, GPIO.OUT)
        GPIO.setup(ESC_PIN, GPIO.OUT)

        # PWM初期化
        self.servo_pwm = GPIO.PWM(SERVO_PIN, PWM_FREQUENCY)
        self.esc_pwm = GPIO.PWM(ESC_PIN, PWM_FREQUENCY)
        self.servo_pwm.start(0)
        self.esc_pwm.start(0)

        # 初期状態に設定
        self.set_steering_angle(NEUTRAL_ANGLE)
        self.set_speed(STOP_PULSE)
        time.sleep(1)

    def set_steering_angle(self, angle: float):
        """
        ステアリング角度を設定

        Parameters:
            angle: ステアリング角度（-90～90度）
        """
        # 角度をパルス幅に変換
        pulse_width_ms = ((angle + 90) / 180) * (
            SERVO_MAX_PULSE_WIDTH_MS - SERVO_MIN_PULSE_WIDTH_MS
        ) + SERVO_MIN_PULSE_WIDTH_MS

        # デューティサイクルに変換（50Hzの場合、1周期は20ms）
        duty_cycle = (pulse_width_ms / 20.0) * 100
        self.servo_pwm.ChangeDutyCycle(duty_cycle)

    def set_speed(self, pulse_width_ms: float):
        """
        モーター速度を設定

        Parameters:
            pulse_width_ms: パルス幅（ms）
        """
        duty_cycle = (pulse_width_ms / 20.0) * 100
        self.esc_pwm.ChangeDutyCycle(duty_cycle)

    def stop(self):
        """停止"""
        self.set_steering_angle(NEUTRAL_ANGLE)
        self.set_speed(STOP_PULSE)

    def cleanup(self):
        """クリーンアップ"""
        self.stop()
        time.sleep(0.5)
        self.servo_pwm.stop()
        self.esc_pwm.stop()
        print("Actuators cleaned up")
