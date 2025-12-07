"""
センサー関連モジュール - VL53L0X距離センサーの初期化と制御
"""

import time
import VL53L0X
import RPi.GPIO as GPIO
from config import (
    SENSOR1_SHUTDOWN,
    SENSOR2_SHUTDOWN,
    SENSOR1_ADDRESS,
    SENSOR2_ADDRESS,
    MIN_TIMING
)


def initialize_sensors():
    """
    VL53L0X距離センサーを初期化します。

    Returns:
    --------
    tof : VL53L0X
        センサー1（20度）のオブジェクト
    tof1 : VL53L0X
        センサー2（70度）のオブジェクト
    """
    # 両方のセンサーをシャットダウン
    GPIO.output(SENSOR1_SHUTDOWN, GPIO.LOW)
    GPIO.output(SENSOR2_SHUTDOWN, GPIO.LOW)
    time.sleep(0.50)

    # センサーオブジェクトを作成
    tof = VL53L0X.VL53L0X(address=SENSOR1_ADDRESS)
    tof1 = VL53L0X.VL53L0X(address=SENSOR2_ADDRESS)

    # センサー1を起動
    GPIO.output(SENSOR1_SHUTDOWN, GPIO.HIGH)
    time.sleep(0.50)
    tof.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)

    # センサー2を起動
    GPIO.output(SENSOR2_SHUTDOWN, GPIO.HIGH)
    time.sleep(0.50)
    tof1.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)

    return tof, tof1


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


def cleanup_sensors(tof, tof1):
    """
    センサーをクリーンアップします。

    Parameters:
    -----------
    tof : VL53L0X
        センサー1
    tof1 : VL53L0X
        センサー2
    """
    tof1.stop_ranging()
    GPIO.output(SENSOR2_SHUTDOWN, GPIO.LOW)
    tof.stop_ranging()
    GPIO.output(SENSOR1_SHUTDOWN, GPIO.LOW)
