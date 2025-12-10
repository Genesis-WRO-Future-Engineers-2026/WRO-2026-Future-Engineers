"""
センサー関連モジュール - VL53L0X距離センサーの初期化と制御
"""

import sys
import os
import time
import RPi.GPIO as GPIO

# VL53L0Xモジュールのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))
import VL53L0X
from config import (
    SENSOR1_SHUTDOWN,
    SENSOR2_SHUTDOWN,
    SENSOR3_SHUTDOWN,
    SENSOR1_ADDRESS,
    SENSOR2_ADDRESS,
    SENSOR3_ADDRESS,
    MIN_TIMING
)


def initialize_sensors():
    """
    VL53L0X距離センサーを初期化します。

    Returns:
    --------
    tof : VL53L0X
        センサー1（0度）のオブジェクト
    tof1 : VL53L0X
        センサー2（20度）のオブジェクト
    tof2 : VL53L0X
        センサー3（70度）のオブジェクト
    """
    # すべてのセンサーをシャットダウン
    GPIO.output(SENSOR1_SHUTDOWN, GPIO.LOW)
    GPIO.output(SENSOR2_SHUTDOWN, GPIO.LOW)
    GPIO.output(SENSOR3_SHUTDOWN, GPIO.LOW)
    time.sleep(0.50)

    # センサーオブジェクトを作成
    tof = VL53L0X.VL53L0X(address=SENSOR1_ADDRESS)
    tof1 = VL53L0X.VL53L0X(address=SENSOR2_ADDRESS)
    tof2 = VL53L0X.VL53L0X(address=SENSOR3_ADDRESS)

    # センサー1を起動（0度）
    GPIO.output(SENSOR1_SHUTDOWN, GPIO.HIGH)
    time.sleep(0.50)
    tof.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)

    # センサー2を起動（20度）
    GPIO.output(SENSOR2_SHUTDOWN, GPIO.HIGH)
    time.sleep(0.50)
    tof1.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)

    # センサー3を起動（70度）
    GPIO.output(SENSOR3_SHUTDOWN, GPIO.HIGH)
    time.sleep(0.50)
    tof2.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)

    return tof, tof1, tof2


def get_timing(tof):
    """
    センサーの測定タイミングを取得します。

    Parameters:
    -----------
    tof : VL53L0X
        センサーオブジェクト

    Returns:
    --------
    timing : int
        測定タイミング（マイクロ秒）
    """
    timing = tof.get_timing()
    if timing < MIN_TIMING:
        timing = MIN_TIMING
    print("Timing %d ms" % (timing/1000))
    return timing


def read_distance(tof):
    """
    センサーから距離を読み取ります。

    Parameters:
    -----------
    tof : VL53L0X
        センサーオブジェクト

    Returns:
    --------
    distance : float or None
        測定された距離（mm）。エラーの場合はNone
    """
    distance = tof.get_distance()
    if distance > 0:
        return distance
    else:
        return None


def cleanup_sensors(tof, tof1, tof2):
    """
    センサーをクリーンアップします。

    Parameters:
    -----------
    tof : VL53L0X
        センサー1
    tof1 : VL53L0X
        センサー2
    tof2 : VL53L0X
        センサー3
    """
    tof2.stop_ranging()
    GPIO.output(SENSOR3_SHUTDOWN, GPIO.LOW)
    tof1.stop_ranging()
    GPIO.output(SENSOR2_SHUTDOWN, GPIO.LOW)
    tof.stop_ranging()
    GPIO.output(SENSOR1_SHUTDOWN, GPIO.LOW)
