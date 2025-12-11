"""
アクチュエータ制御モジュール - サーボモーターとESCの制御
"""

import time
import RPi.GPIO as GPIO
from config import (
    SENSOR1_SHUTDOWN,
    SENSOR2_SHUTDOWN,
    SENSOR3_SHUTDOWN,
    SENSOR4_SHUTDOWN,
    SENSOR5_SHUTDOWN,
    SERVO_PIN,
    ESC_PIN,
    PWM_FREQUENCY,
    SERVO_MIN_PULSE_WIDTH_MS,
    SERVO_MAX_PULSE_WIDTH_MS,
    NEUTRAL_ANGLE,
    STOP_PULSE
)


def initialize_gpio():
    """
    GPIOピンを初期化します（センサー、サーボ、ESC）

    Returns:
    --------
    servo_pwm : GPIO.PWM
        サーボ用PWMオブジェクト
    esc_pwm : GPIO.PWM
        ESC用PWMオブジェクト
    """
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    # センサー用ピンを設定（5つのセンサー）
    GPIO.setup(SENSOR1_SHUTDOWN, GPIO.OUT)
    GPIO.setup(SENSOR2_SHUTDOWN, GPIO.OUT)
    GPIO.setup(SENSOR3_SHUTDOWN, GPIO.OUT)
    GPIO.setup(SENSOR4_SHUTDOWN, GPIO.OUT)
    GPIO.setup(SENSOR5_SHUTDOWN, GPIO.OUT)

    # サーボとESCのピンを設定
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    GPIO.setup(ESC_PIN, GPIO.OUT)

    # PWM初期化
    servo_pwm = GPIO.PWM(SERVO_PIN, PWM_FREQUENCY)
    esc_pwm = GPIO.PWM(ESC_PIN, PWM_FREQUENCY)
    servo_pwm.start(0)
    esc_pwm.start(0)

    # 初期状態に設定
    set_servo_angle(servo_pwm, NEUTRAL_ANGLE)
    set_esc_speed(esc_pwm, STOP_PULSE)
    time.sleep(1)

    return servo_pwm, esc_pwm


def set_servo_angle(servo_pwm, angle):
    """
    サーボの角度を設定します。

    Parameters:
    -----------
    servo_pwm : GPIO.PWM
        サーボ用PWMオブジェクト
    angle : float
        設定する角度（-90～90度）
    """
    # 角度をパルス幅に変換
    pulse_width_ms = ((angle + 90) / 180) * (
        SERVO_MAX_PULSE_WIDTH_MS - SERVO_MIN_PULSE_WIDTH_MS
    ) + SERVO_MIN_PULSE_WIDTH_MS

    # パルス幅をデューティサイクルに変換（50Hzの場合、1周期は20ms）
    duty_cycle = (pulse_width_ms / 20.0) * 100
    servo_pwm.ChangeDutyCycle(duty_cycle)


def set_esc_speed(esc_pwm, pulse_width_ms):
    """
    ESCの速度を設定します。

    Parameters:
    -----------
    esc_pwm : GPIO.PWM
        ESC用PWMオブジェクト
    pulse_width_ms : float
        パルス幅（ms）
    """
    # パルス幅をデューティサイクルに変換（50Hzの場合、1周期は20ms）
    duty_cycle = (pulse_width_ms / 20.0) * 100
    esc_pwm.ChangeDutyCycle(duty_cycle)


def cleanup_actuators(servo_pwm, esc_pwm):
    """
    サーボとESCをクリーンアップします。

    Parameters:
    -----------
    servo_pwm : GPIO.PWM
        サーボ用PWMオブジェクト
    esc_pwm : GPIO.PWM
        ESC用PWMオブジェクト
    """
    set_servo_angle(servo_pwm, NEUTRAL_ANGLE)
    set_esc_speed(esc_pwm, STOP_PULSE)
    time.sleep(0.5)
    servo_pwm.stop()
    esc_pwm.stop()
