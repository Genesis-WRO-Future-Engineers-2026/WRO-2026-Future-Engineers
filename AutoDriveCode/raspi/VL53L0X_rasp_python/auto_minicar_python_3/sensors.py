"""センサー管理モジュール - VL53L0Xセンサーの初期化と測定"""

import sys
import os
import time
import RPi.GPIO as GPIO
from typing import Dict

# VL53L0Xモジュールのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))
import VL53L0X

from config import (
    SENSOR1_SHUTDOWN, SENSOR2_SHUTDOWN, SENSOR3_SHUTDOWN, SENSOR4_SHUTDOWN, SENSOR5_SHUTDOWN,
    SENSOR1_ADDRESS, SENSOR2_ADDRESS, SENSOR3_ADDRESS, SENSOR4_ADDRESS, SENSOR5_ADDRESS,
    SENSOR1_ANGLE, SENSOR2_ANGLE, SENSOR3_ANGLE, SENSOR4_ANGLE, SENSOR5_ANGLE,
    MIN_TIMING
)


class SensorManager:
    """5つのVL53L0Xセンサーを管理するクラス"""

    def __init__(self):
        """センサーを初期化"""
        self.sensors = {}
        self.angles = {
            'sensor1': SENSOR1_ANGLE,
            'sensor2': SENSOR2_ANGLE,
            'sensor3': SENSOR3_ANGLE,
            'sensor4': SENSOR4_ANGLE,
            'sensor5': SENSOR5_ANGLE
        }
        self._initialize_all_sensors()

    def _initialize_all_sensors(self):
        """全センサーを初期化"""
        # 全センサーをシャットダウン
        GPIO.output(SENSOR1_SHUTDOWN, GPIO.LOW)
        GPIO.output(SENSOR2_SHUTDOWN, GPIO.LOW)
        GPIO.output(SENSOR3_SHUTDOWN, GPIO.LOW)
        GPIO.output(SENSOR4_SHUTDOWN, GPIO.LOW)
        GPIO.output(SENSOR5_SHUTDOWN, GPIO.LOW)
        time.sleep(0.50)

        # センサー1を初期化
        print("Initializing sensor 1 (-70 deg, left)...")
        GPIO.output(SENSOR1_SHUTDOWN, GPIO.HIGH)
        time.sleep(0.50)
        tof1 = VL53L0X.VL53L0X(address=0x29)
        tof1.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
        time.sleep(0.50)
        tof1.stop_ranging()
        tof1 = VL53L0X.VL53L0X(address=SENSOR1_ADDRESS)
        tof1.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
        self.sensors['sensor1'] = tof1
        print(f"  Sensor 1 initialized at address 0x{SENSOR1_ADDRESS:02X}")

        # センサー2を初期化
        print("Initializing sensor 2 (-20 deg)...")
        GPIO.output(SENSOR2_SHUTDOWN, GPIO.HIGH)
        time.sleep(0.50)
        tof2 = VL53L0X.VL53L0X(address=0x29)
        tof2.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
        time.sleep(0.50)
        tof2.stop_ranging()
        tof2 = VL53L0X.VL53L0X(address=SENSOR2_ADDRESS)
        tof2.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
        self.sensors['sensor2'] = tof2
        print(f"  Sensor 2 initialized at address 0x{SENSOR2_ADDRESS:02X}")

        # センサー3を初期化
        print("Initializing sensor 3 (0 deg, front)...")
        GPIO.output(SENSOR3_SHUTDOWN, GPIO.HIGH)
        time.sleep(0.50)
        tof3 = VL53L0X.VL53L0X(address=0x29)
        tof3.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
        time.sleep(0.50)
        tof3.stop_ranging()
        tof3 = VL53L0X.VL53L0X(address=SENSOR3_ADDRESS)
        tof3.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
        self.sensors['sensor3'] = tof3
        print(f"  Sensor 3 initialized at address 0x{SENSOR3_ADDRESS:02X}")

        # センサー4を初期化
        print("Initializing sensor 4 (+20 deg)...")
        GPIO.output(SENSOR4_SHUTDOWN, GPIO.HIGH)
        time.sleep(0.50)
        tof4 = VL53L0X.VL53L0X(address=0x29)
        tof4.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
        time.sleep(0.50)
        tof4.stop_ranging()
        tof4 = VL53L0X.VL53L0X(address=SENSOR4_ADDRESS)
        tof4.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
        self.sensors['sensor4'] = tof4
        print(f"  Sensor 4 initialized at address 0x{SENSOR4_ADDRESS:02X}")

        # センサー5を初期化
        print("Initializing sensor 5 (+70 deg, right)...")
        GPIO.output(SENSOR5_SHUTDOWN, GPIO.HIGH)
        time.sleep(0.50)
        tof5 = VL53L0X.VL53L0X(address=0x29)
        tof5.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
        time.sleep(0.50)
        tof5.stop_ranging()
        tof5 = VL53L0X.VL53L0X(address=SENSOR5_ADDRESS)
        tof5.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
        self.sensors['sensor5'] = tof5
        print(f"  Sensor 5 initialized at address 0x{SENSOR5_ADDRESS:02X}")

        print("All 5 sensors initialized successfully")

    def read_all_distances(self) -> Dict[str, float]:
        """
        全センサーの距離を読み取る

        Returns:
            {"sensor1": distance1, "sensor2": distance2, ...}
        """
        return {
            'sensor1': self.sensors['sensor1'].get_distance(),
            'sensor2': self.sensors['sensor2'].get_distance(),
            'sensor3': self.sensors['sensor3'].get_distance(),
            'sensor4': self.sensors['sensor4'].get_distance(),
            'sensor5': self.sensors['sensor5'].get_distance()
        }

    def get_sensor_angles(self) -> Dict[str, float]:
        """センサーの角度設定を取得"""
        return self.angles

    def get_timing(self) -> int:
        """測定タイミングを取得"""
        timing = self.sensors['sensor1'].get_timing()
        if timing < MIN_TIMING:
            timing = MIN_TIMING
        print(f"Timing {timing/1000} ms")
        return timing

    def cleanup(self):
        """センサーをクリーンアップ"""
        for sensor in self.sensors.values():
            sensor.stop_ranging()
        GPIO.output(SENSOR5_SHUTDOWN, GPIO.LOW)
        GPIO.output(SENSOR4_SHUTDOWN, GPIO.LOW)
        GPIO.output(SENSOR3_SHUTDOWN, GPIO.LOW)
        GPIO.output(SENSOR2_SHUTDOWN, GPIO.LOW)
        GPIO.output(SENSOR1_SHUTDOWN, GPIO.LOW)
        print("Sensors cleaned up")
