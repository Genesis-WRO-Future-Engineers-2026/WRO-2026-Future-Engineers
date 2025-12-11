"""
アクチュエータ制御モジュール - サーボモーターとESCの制御（pigpio版）
"""

import time
import pigpio
from config import (
    SENSOR1_SHUTDOWN,
    SENSOR2_SHUTDOWN,
    SENSOR3_SHUTDOWN,
    SENSOR4_SHUTDOWN,
    SENSOR5_SHUTDOWN,
    SERVO_PIN,
    ESC_PIN,
    SERVO_MIN_PULSE_WIDTH_US,
    SERVO_MAX_PULSE_WIDTH_US,
    SERVO_CENTER_PULSE_WIDTH_US,
    NEUTRAL_ANGLE,
    STOP_PULSE_US
)


def initialize_pigpio():
    """
    pigpioデーモンに接続し、GPIOピンを初期化します。

    Returns:
    --------
    pi : pigpio.pi
        pigpioインスタンス
    """
    # pigpioデーモンに接続
    pi = pigpio.pi()

    if not pi.connected:
        raise RuntimeError("pigpioデーモンに接続できません。'sudo pigpiod'を実行してください。")

    print("pigpio connected successfully")

    # センサー用ピンを設定（5つのセンサー）
    pi.set_mode(SENSOR1_SHUTDOWN, pigpio.OUTPUT)
    pi.set_mode(SENSOR2_SHUTDOWN, pigpio.OUTPUT)
    pi.set_mode(SENSOR3_SHUTDOWN, pigpio.OUTPUT)
    pi.set_mode(SENSOR4_SHUTDOWN, pigpio.OUTPUT)
    pi.set_mode(SENSOR5_SHUTDOWN, pigpio.OUTPUT)

    # サーボとESCのピンを設定
    pi.set_mode(SERVO_PIN, pigpio.OUTPUT)
    pi.set_mode(ESC_PIN, pigpio.OUTPUT)

    # 初期状態に設定
    set_servo_angle(pi, NEUTRAL_ANGLE)
    set_esc_speed(pi, STOP_PULSE_US)
    time.sleep(1)

    return pi


def set_servo_angle(pi, angle):
    """
    サーボの角度を設定します（pigpio版）。

    Parameters:
    -----------
    pi : pigpio.pi
        pigpioインスタンス
    angle : float
        設定する角度（-90～90度）
    """
    # 角度をパルス幅（マイクロ秒）に変換
    pulse_width_us = ((angle + 90) / 180) * (
        SERVO_MAX_PULSE_WIDTH_US - SERVO_MIN_PULSE_WIDTH_US
    ) + SERVO_MIN_PULSE_WIDTH_US

    # パルス幅を整数に変換
    pulse_width_us = int(pulse_width_us)

    # pigpioでサーボにパルス幅を設定
    pi.set_servo_pulsewidth(SERVO_PIN, pulse_width_us)


def set_esc_speed(pi, pulse_width_us):
    """
    ESCの速度を設定します（pigpio版）。

    Parameters:
    -----------
    pi : pigpio.pi
        pigpioインスタンス
    pulse_width_us : int
        パルス幅（マイクロ秒）
    """
    # pigpioでESCにパルス幅を設定
    pi.set_servo_pulsewidth(ESC_PIN, pulse_width_us)


def cleanup_actuators(pi):
    """
    サーボとESCをクリーンアップします（pigpio版）。

    Parameters:
    -----------
    pi : pigpio.pi
        pigpioインスタンス
    """
    set_servo_angle(pi, NEUTRAL_ANGLE)
    set_esc_speed(pi, STOP_PULSE_US)
    time.sleep(0.5)

    # サーボとESCのPWMを停止
    pi.set_servo_pulsewidth(SERVO_PIN, 0)
    pi.set_servo_pulsewidth(ESC_PIN, 0)

    print("Actuators cleaned up")
