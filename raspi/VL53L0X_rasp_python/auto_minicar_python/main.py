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

"""
メインプログラム - 壁検出カウンターステア制御
"""

import time
import RPi.GPIO as GPIO

from config import (
    PARALLEL_ANGLE,
    ANGLE_TOLERANCE,
    TARGET_DISTANCE,
    DISTANCE_TOLERANCE,
    SPEED_PULSE,
    STOP_PULSE,
    NEUTRAL_ANGLE,
    DEFAULT_ITERATIONS
)
from sensors import initialize_sensors, get_timing, cleanup_sensors
from actuators import initialize_gpio, set_esc_speed, set_servo_angle, cleanup_actuators
from wall_tracking import (
    calculate_wall_approach_angle,
    calculate_wall_distance,
    apply_counter_steer
)


def run_measurement_loop(tof, tof1, timing, servo_pwm, esc_pwm, iterations=None):
    """
    距離センサーの測定ループを実行し、カウンターステア制御を行います。

    Parameters:
    -----------
    tof : VL53L0X
        センサー1（20度）
    tof1 : VL53L0X
        センサー2（70度）
    timing : int
        測定間隔（マイクロ秒）
    servo_pwm : GPIO.PWM
        サーボ用PWMオブジェクト
    esc_pwm : GPIO.PWM
        ESC用PWMオブジェクト
    iterations : int, optional
        測定回数（デフォルト: config.DEFAULT_ITERATIONS）
    """
    if iterations is None:
        iterations = DEFAULT_ITERATIONS

    # モーターを前進させる
    set_esc_speed(esc_pwm, SPEED_PULSE)
    print("モーター前進開始")

    for count in range(1, iterations + 1):
        distance1 = tof.get_distance()
        distance2 = tof1.get_distance()

        # センサー1の距離表示
        if distance1 > 0:
            print("sensor %d - %d mm, %d cm, iteration %d" % (
                tof.my_object_number, distance1, distance1/10, count
            ))
        else:
            print("%d - Error" % tof.my_object_number)

        # センサー2の距離表示
        if distance2 > 0:
            print("sensor %d - %d mm, %d cm, iteration %d" % (
                tof1.my_object_number, distance2, distance2/10, count
            ))
        else:
            print("%d - Error" % tof1.my_object_number)

        # 両方のセンサーが正常に距離を取得できた場合、壁との角度と距離を計算
        if distance1 > 0 and distance2 > 0:
            angle = calculate_wall_approach_angle(distance1, distance2)
            wall_distance = calculate_wall_distance(distance2, angle)

            print("  壁との角度: %.2f度, 壁までの距離: %.1f mm" % (
                angle, wall_distance
            ), end="")

            # カウンターステアを適用（角度と距離の両方を考慮）
            steer_action = apply_counter_steer(servo_pwm, angle, wall_distance)

            if wall_distance < TARGET_DISTANCE - DISTANCE_TOLERANCE:
                print(" → 壁に近い [%s]" % steer_action)
            elif wall_distance > TARGET_DISTANCE + DISTANCE_TOLERANCE:
                print(" → 壁から遠い [%s]" % steer_action)
            elif angle > PARALLEL_ANGLE + ANGLE_TOLERANCE:
                print(" → 距離OK・壁から離れている [%s]" % steer_action)
            elif angle < PARALLEL_ANGLE - ANGLE_TOLERANCE:
                print(" → 距離OK・壁に近づいている [%s]" % steer_action)
            else:
                print(" → 距離OK・壁とほぼ平行 [%s]" % steer_action)

        print()  # 空行を追加して見やすく
        time.sleep(timing/1000000.00)

    # 測定終了後、停止
    set_esc_speed(esc_pwm, STOP_PULSE)
    set_servo_angle(servo_pwm, NEUTRAL_ANGLE)
    print("モーター停止")


def cleanup_all(tof, tof1, servo_pwm, esc_pwm):
    """
    すべてのハードウェアをクリーンアップします。

    Parameters:
    -----------
    tof : VL53L0X
        センサー1
    tof1 : VL53L0X
        センサー2
    servo_pwm : GPIO.PWM
        サーボ用PWMオブジェクト
    esc_pwm : GPIO.PWM
        ESC用PWMオブジェクト
    """
    cleanup_sensors(tof, tof1)
    cleanup_actuators(servo_pwm, esc_pwm)
    GPIO.cleanup()
    print("クリーンアップ完了")


def main():
    """
    メインプログラム：距離センサーによる壁検出とカウンターステア制御
    """
    print("=" * 50)
    print("壁検出カウンターステア制御プログラム")
    print("=" * 50)

    servo_pwm, esc_pwm = initialize_gpio()
    tof, tof1 = initialize_sensors()
    timing = get_timing(tof)

    try:
        run_measurement_loop(tof, tof1, timing, servo_pwm, esc_pwm)
    except KeyboardInterrupt:
        print("\nプログラムを中断しました")
    finally:
        cleanup_all(tof, tof1, servo_pwm, esc_pwm)


if __name__ == "__main__":
    main()
