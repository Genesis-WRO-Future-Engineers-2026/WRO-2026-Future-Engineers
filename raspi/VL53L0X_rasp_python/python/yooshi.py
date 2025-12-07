#!/usr/bin/python

# MIT License
# 
# Copyright (c) 2017 John Bryan Moore
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time
import math
import VL53L0X
import RPi.GPIO as GPIO

# GPIO for Sensor 1 shutdown pin
SENSOR1_SHUTDOWN = 20
# GPIO for Sensor 2 shutdown pin
SENSOR2_SHUTDOWN = 21

# 壁と平行時の基準角度と許容誤差
PARALLEL_ANGLE = 110.0
TOLERANCE = 2.0


def calculate_wall_approach_angle(distance1, distance2, angle1=20, angle2=70):
    """
    2つのセンサーの距離測定値から、70度センサー位置での三角形の角度を計算

    Parameters:
    -----------
    distance1 : float
        センサー1(20度)で測定した壁までの距離
    distance2 : float
        センサー2(70度)で測定した壁までの距離
    angle1 : float
        センサー1の角度(デフォルト: 20度)
    angle2 : float
        センサー2の角度(デフォルト: 70度)

    Returns:
    --------
    triangle_angle : float
        70度センサー位置での三角形の内角(度)
        110度より大きい(鈍角) = 壁から離れている
        110度より小さい(鋭角) = 壁に近づいている
        110度(≈) = 壁と平行
    """

    # センサー間の角度差
    sensor_angle_diff = angle2 - angle1  # 50度
    theta_diff = math.radians(sensor_angle_diff)

    # 正弦定理を使用
    sin_angle_at_d1 = distance2 * math.sin(theta_diff) / distance1

    # sin値が1を超えないようにクリップ
    sin_angle_at_d1 = max(-1, min(1, sin_angle_at_d1))

    angle_at_d1 = math.asin(sin_angle_at_d1)

    # 70度センサー位置での角度
    triangle_angle_rad = math.pi - theta_diff - angle_at_d1
    triangle_angle = math.degrees(triangle_angle_rad)

    return triangle_angle


def initialize_gpio():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SENSOR1_SHUTDOWN, GPIO.OUT)
    GPIO.setup(SENSOR2_SHUTDOWN, GPIO.OUT)


def initialize_sensors():
    GPIO.output(SENSOR1_SHUTDOWN, GPIO.LOW)
    GPIO.output(SENSOR2_SHUTDOWN, GPIO.LOW)
    time.sleep(0.50)

    tof = VL53L0X.VL53L0X(address=0x2B)
    tof1 = VL53L0X.VL53L0X(address=0x2D)

    GPIO.output(SENSOR1_SHUTDOWN, GPIO.HIGH)
    time.sleep(0.50)
    tof.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)

    GPIO.output(SENSOR2_SHUTDOWN, GPIO.HIGH)
    time.sleep(0.50)
    tof1.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)

    return tof, tof1


def get_timing(tof):
    timing = tof.get_timing()
    if timing < 20000:
        timing = 20000
    print("Timing %d ms" % (timing/1000))
    return timing


def read_distance(tof):
    distance = tof.get_distance()
    if distance > 0:
        return distance
    else:
        return None


def run_measurement_loop(tof, tof1, timing, iterations=100):
    for count in range(1, iterations + 1):
        distance1 = tof.get_distance()
        distance2 = tof1.get_distance()

        # センサー1の距離表示
        if distance1 > 0:
            print("sensor %d - %d mm, %d cm, iteration %d" % (tof.my_object_number, distance1, distance1/10, count))
        else:
            print("%d - Error" % tof.my_object_number)

        # センサー2の距離表示
        if distance2 > 0:
            print("sensor %d - %d mm, %d cm, iteration %d" % (tof1.my_object_number, distance2, distance2/10, count))
        else:
            print("%d - Error" % tof1.my_object_number)

        # 両方のセンサーが正常に距離を取得できた場合、壁との角度を計算
        if distance1 > 0 and distance2 > 0:
            angle = calculate_wall_approach_angle(distance1, distance2)
            print("  壁との角度: %.2f度" % angle, end="")

            if angle > PARALLEL_ANGLE + TOLERANCE:
                print(" → 壁から離れている")
            elif angle < PARALLEL_ANGLE - TOLERANCE:
                print(" → 壁に近づいている")
            else:
                print(" → 壁とほぼ平行")

        print()  # 空行を追加して見やすく
        time.sleep(timing/1000000.00)


def cleanup_sensors(tof, tof1):
    tof1.stop_ranging()
    GPIO.output(SENSOR2_SHUTDOWN, GPIO.LOW)
    tof.stop_ranging()
    GPIO.output(SENSOR1_SHUTDOWN, GPIO.LOW)


def main():
    initialize_gpio()
    tof, tof1 = initialize_sensors()
    timing = get_timing(tof)
    run_measurement_loop(tof, tof1, timing)
    cleanup_sensors(tof, tof1)


if __name__ == "__main__":
    main()

