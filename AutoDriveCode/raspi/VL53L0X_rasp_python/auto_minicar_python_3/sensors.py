"""
センサー関連モジュール - VL53L0X距離センサーの初期化と制御（pigpio版）
"""

import sys
import os
import time

# VL53L0Xモジュールのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))
import VL53L0X
from config import (
    SENSOR1_SHUTDOWN,
    SENSOR2_SHUTDOWN,
    SENSOR3_SHUTDOWN,
    SENSOR4_SHUTDOWN,
    SENSOR5_SHUTDOWN,
    SENSOR1_ADDRESS,
    SENSOR2_ADDRESS,
    SENSOR3_ADDRESS,
    SENSOR4_ADDRESS,
    SENSOR5_ADDRESS,
    MIN_TIMING
)


def initialize_sensors(pi):
    """
    VL53L0X距離センサーを初期化します（5つのセンサー）（pigpio版）。

    複数のVL53L0Xセンサーを使用する場合、各センサーを順番に起動して
    I2Cアドレスを変更する必要があります。全てのセンサーはデフォルトで
    0x29を使用するため、アドレス衝突を避けるため以下の手順を踏みます：
    1. 全センサーをシャットダウン
    2. センサー1のみ起動してアドレスを変更
    3. センサー2を起動してアドレスを変更
    4. センサー3を起動してアドレスを変更
    5. センサー4を起動してアドレスを変更
    6. センサー5を起動してアドレスを変更

    Parameters:
    -----------
    pi : pigpio.pi
        pigpioインスタンス

    Returns:
    --------
    tuple : (tof1, tof2, tof3, tof4, tof5)
        tof1 : VL53L0X - センサー1（-70度・左）のオブジェクト
        tof2 : VL53L0X - センサー2（-20度）のオブジェクト
        tof3 : VL53L0X - センサー3（0度・正面）のオブジェクト
        tof4 : VL53L0X - センサー4（+20度）のオブジェクト
        tof5 : VL53L0X - センサー5（+70度・右）のオブジェクト
    """
    # すべてのセンサーをシャットダウン
    pi.write(SENSOR1_SHUTDOWN, 0)
    pi.write(SENSOR2_SHUTDOWN, 0)
    pi.write(SENSOR3_SHUTDOWN, 0)
    pi.write(SENSOR4_SHUTDOWN, 0)
    pi.write(SENSOR5_SHUTDOWN, 0)
    time.sleep(0.50)

    # センサー1を起動してアドレスを設定（-70度・左）
    print("Initializing sensor 1 (-70 deg, left)...")
    pi.write(SENSOR1_SHUTDOWN, 1)
    time.sleep(0.50)
    tof1 = VL53L0X.VL53L0X(address=0x29)  # デフォルトアドレスで起動
    tof1.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
    time.sleep(0.50)
    tof1.stop_ranging()
    tof1 = VL53L0X.VL53L0X(address=SENSOR1_ADDRESS)
    tof1.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
    print(f"  Sensor 1 initialized at address 0x{SENSOR1_ADDRESS:02X}")

    # センサー2を起動してアドレスを設定（-20度）
    print("Initializing sensor 2 (-20 deg)...")
    pi.write(SENSOR2_SHUTDOWN, 1)
    time.sleep(0.50)
    tof2 = VL53L0X.VL53L0X(address=0x29)  # デフォルトアドレスで起動
    tof2.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
    time.sleep(0.50)
    tof2.stop_ranging()
    tof2 = VL53L0X.VL53L0X(address=SENSOR2_ADDRESS)
    tof2.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
    print(f"  Sensor 2 initialized at address 0x{SENSOR2_ADDRESS:02X}")

    # センサー3を起動してアドレスを設定（0度・正面）
    print("Initializing sensor 3 (0 deg, front)...")
    pi.write(SENSOR3_SHUTDOWN, 1)
    time.sleep(0.50)
    tof3 = VL53L0X.VL53L0X(address=0x29)  # デフォルトアドレスで起動
    tof3.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
    time.sleep(0.50)
    tof3.stop_ranging()
    tof3 = VL53L0X.VL53L0X(address=SENSOR3_ADDRESS)
    tof3.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
    print(f"  Sensor 3 initialized at address 0x{SENSOR3_ADDRESS:02X}")

    # センサー4を起動してアドレスを設定（+20度）
    print("Initializing sensor 4 (+20 deg)...")
    pi.write(SENSOR4_SHUTDOWN, 1)
    time.sleep(0.50)
    tof4 = VL53L0X.VL53L0X(address=0x29)  # デフォルトアドレスで起動
    tof4.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
    time.sleep(0.50)
    tof4.stop_ranging()
    tof4 = VL53L0X.VL53L0X(address=SENSOR4_ADDRESS)
    tof4.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
    print(f"  Sensor 4 initialized at address 0x{SENSOR4_ADDRESS:02X}")

    # センサー5を起動してアドレスを設定（+70度・右）
    print("Initializing sensor 5 (+70 deg, right)...")
    pi.write(SENSOR5_SHUTDOWN, 1)
    time.sleep(0.50)
    tof5 = VL53L0X.VL53L0X(address=0x29)  # デフォルトアドレスで起動
    tof5.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
    time.sleep(0.50)
    tof5.stop_ranging()
    tof5 = VL53L0X.VL53L0X(address=SENSOR5_ADDRESS)
    tof5.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
    print(f"  Sensor 5 initialized at address 0x{SENSOR5_ADDRESS:02X}")

    print("All 5 sensors initialized successfully")
    return tof1, tof2, tof3, tof4, tof5


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


def cleanup_sensors(pi, tof1, tof2, tof3, tof4, tof5):
    """
    センサーをクリーンアップします（5つのセンサー）（pigpio版）。

    Parameters:
    -----------
    pi : pigpio.pi
        pigpioインスタンス
    tof1 : VL53L0X
        センサー1（-70度）
    tof2 : VL53L0X
        センサー2（-20度）
    tof3 : VL53L0X
        センサー3（0度）
    tof4 : VL53L0X
        センサー4（+20度）
    tof5 : VL53L0X
        センサー5（+70度）
    """
    tof5.stop_ranging()
    pi.write(SENSOR5_SHUTDOWN, 0)
    tof4.stop_ranging()
    pi.write(SENSOR4_SHUTDOWN, 0)
    tof3.stop_ranging()
    pi.write(SENSOR3_SHUTDOWN, 0)
    tof2.stop_ranging()
    pi.write(SENSOR2_SHUTDOWN, 0)
    tof1.stop_ranging()
    pi.write(SENSOR1_SHUTDOWN, 0)

    print("Sensors cleaned up")
