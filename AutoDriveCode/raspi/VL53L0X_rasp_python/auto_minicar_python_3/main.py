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
    apply_counter_steer,
    detect_straight_path,
    turn_to_straight_path
)


def run_measurement_loop(tof, tof1, tof2, timing, servo_pwm, esc_pwm, iterations=None):
    """
    距離センサーの測定ループを実行し、直線検出と壁追従制御を行います。

    Parameters:
    -----------
    tof : VL53L0X
        センサー1（0度）
    tof1 : VL53L0X
        センサー2（20度）
    tof2 : VL53L0X
        センサー3（70度）
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
    print("Motor forward started")

    # 直線検出モードの状態管理
    straight_path_mode = False
    detected_direction = ""

    for count in range(1, iterations + 1):
        distance0 = tof.get_distance()    # 0度センサー
        distance1 = tof1.get_distance()   # 20度センサー
        distance2 = tof2.get_distance()   # 70度センサー

        # センサー0の距離表示
        if distance0 > 0:
            print("sensor 0deg - %d mm, %d cm, iteration %d" % (
                distance0, distance0/10, count
            ))
        else:
            print("sensor 0deg - Error")

        # センサー1の距離表示
        if distance1 > 0:
            print("sensor 20deg - %d mm, %d cm, iteration %d" % (
                distance1, distance1/10, count
            ))
        else:
            print("sensor 20deg - Error")

        # センサー2の距離表示
        if distance2 > 0:
            print("sensor 70deg - %d mm, %d cm, iteration %d" % (
                distance2, distance2/10, count
            ))
        else:
            print("sensor 70deg - Error")

        # 3つのセンサーが正常に距離を取得できた場合
        if distance0 > 0 and distance1 > 0 and distance2 > 0:
            # 直線検出モードでない場合、直線を検出
            if not straight_path_mode:
                straight_detected, direction, detected_dist = detect_straight_path(distance1, distance2)
                if straight_detected:
                    straight_path_mode = True
                    detected_direction = direction
                    print(f"  >>> STRAIGHT PATH DETECTED at {direction} ({detected_dist:.0f}mm) - entering turn mode")

            # 直線検出モード：0度センサーが最大になるまで旋回
            if straight_path_mode:
                continue_turning, turn_action = turn_to_straight_path(
                    servo_pwm, detected_direction, distance0, distance1, distance2
                )
                print(f"  [TURN MODE] {turn_action}")

                if not continue_turning:
                    # 0度センサーが最大を向いたので、通常の壁追従モードに戻る
                    straight_path_mode = False
                    print("  >>> Front sensor maximized - returning to wall tracking mode")

            # 通常の壁追従モード（20度と70度で壁追従）
            else:
                angle = calculate_wall_approach_angle(distance1, distance2)
                wall_distance = calculate_wall_distance(distance2, angle)

                print("  Wall angle: %.2f deg, Wall distance: %.1f mm" % (
                    angle, wall_distance
                ), end="")

                # カウンターステアを適用（角度と距離の両方を考慮）
                steer_action = apply_counter_steer(servo_pwm, angle, wall_distance)

                if wall_distance < TARGET_DISTANCE - DISTANCE_TOLERANCE:
                    print(" -> Too close to wall [%s]" % steer_action)
                elif wall_distance > TARGET_DISTANCE + DISTANCE_TOLERANCE:
                    print(" -> Too far from wall [%s]" % steer_action)
                elif angle > PARALLEL_ANGLE + ANGLE_TOLERANCE:
                    print(" -> Distance OK, moving away from wall [%s]" % steer_action)
                elif angle < PARALLEL_ANGLE - ANGLE_TOLERANCE:
                    print(" -> Distance OK, approaching wall [%s]" % steer_action)
                else:
                    print(" -> Distance OK, parallel to wall [%s]" % steer_action)

        print()  # 空行を追加して見やすく
        time.sleep(timing/1000000.00)

    # 測定終了後、停止
    set_esc_speed(esc_pwm, STOP_PULSE)
    set_servo_angle(servo_pwm, NEUTRAL_ANGLE)
    print("Motor stopped")


def cleanup_all(tof, tof1, tof2, servo_pwm, esc_pwm):
    """
    すべてのハードウェアをクリーンアップします。

    Parameters:
    -----------
    tof : VL53L0X
        センサー1
    tof1 : VL53L0X
        センサー2
    tof2 : VL53L0X
        センサー3
    servo_pwm : GPIO.PWM
        サーボ用PWMオブジェクト
    esc_pwm : GPIO.PWM
        ESC用PWMオブジェクト
    """
    cleanup_sensors(tof, tof1, tof2)
    cleanup_actuators(servo_pwm, esc_pwm)
    GPIO.cleanup()
    print("Cleanup completed")


def main():
    """
    メインプログラム：距離センサーによる壁追従と直線検出制御
    """
    print("=" * 50)
    print("3-Sensor Wall Tracking & Straight Path Detection")
    print("Sensors: 0deg (front), 20deg, 70deg (left)")
    print("=" * 50)

    servo_pwm, esc_pwm = initialize_gpio()
    tof, tof1, tof2 = initialize_sensors()
    timing = get_timing(tof)

    try:
        run_measurement_loop(tof, tof1, tof2, timing, servo_pwm, esc_pwm)
    except KeyboardInterrupt:
        print("\nProgram interrupted")
    finally:
        cleanup_all(tof, tof1, tof2, servo_pwm, esc_pwm)


if __name__ == "__main__":
    main()
