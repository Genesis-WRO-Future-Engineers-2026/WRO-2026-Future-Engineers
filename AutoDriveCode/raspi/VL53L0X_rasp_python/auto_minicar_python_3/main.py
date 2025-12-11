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
メインプログラム - 5センサー距離測定表示（pigpio版）
センサー配置: -70度(左), -20度, 0度(正面), +20度, +70度(右)
"""

import time

from config import DEFAULT_ITERATIONS
from sensors import initialize_sensors, get_timing, cleanup_sensors
from actuators import initialize_pigpio, cleanup_actuators


def run_measurement_loop(tof1, tof2, tof3, tof4, tof5, timing, iterations=None):
    """
    5つの距離センサーの測定ループを実行し、距離を表示します。

    Parameters:
    -----------
    tof1 : VL53L0X
        センサー1（-70度・左）
    tof2 : VL53L0X
        センサー2（-20度）
    tof3 : VL53L0X
        センサー3（0度・正面）
    tof4 : VL53L0X
        センサー4（+20度）
    tof5 : VL53L0X
        センサー5（+70度・右）
    timing : int
        測定間隔（マイクロ秒）
    iterations : int, optional
        測定回数（デフォルト: config.DEFAULT_ITERATIONS）
    """
    if iterations is None:
        iterations = DEFAULT_ITERATIONS

    print("\nStarting distance measurements...")
    print("=" * 70)

    for count in range(1, iterations + 1):
        # 各センサーから距離を取得
        distance1 = tof1.get_distance()  # -70度（左）
        distance2 = tof2.get_distance()  # -20度
        distance3 = tof3.get_distance()  # 0度（正面）
        distance4 = tof4.get_distance()  # +20度
        distance5 = tof5.get_distance()  # +70度（右）

        print(f"\n--- Iteration {count}/{iterations} ---")

        # センサー1（-70度・左）
        if distance1 > 0:
            print(f"  Sensor 1 (-70°, Left):  {distance1:4d} mm ({distance1/10:.1f} cm)")
        else:
            print(f"  Sensor 1 (-70°, Left):  Error")

        # センサー2（-20度）
        if distance2 > 0:
            print(f"  Sensor 2 (-20°):        {distance2:4d} mm ({distance2/10:.1f} cm)")
        else:
            print(f"  Sensor 2 (-20°):        Error")

        # センサー3（0度・正面）
        if distance3 > 0:
            print(f"  Sensor 3 (  0°, Front): {distance3:4d} mm ({distance3/10:.1f} cm)")
        else:
            print(f"  Sensor 3 (  0°, Front): Error")

        # センサー4（+20度）
        if distance4 > 0:
            print(f"  Sensor 4 (+20°):        {distance4:4d} mm ({distance4/10:.1f} cm)")
        else:
            print(f"  Sensor 4 (+20°):        Error")

        # センサー5（+70度・右）
        if distance5 > 0:
            print(f"  Sensor 5 (+70°, Right): {distance5:4d} mm ({distance5/10:.1f} cm)")
        else:
            print(f"  Sensor 5 (+70°, Right): Error")

        # TODO: ここに進行方向を計算するロジックを追加
        # calculate_direction(distance1, distance2, distance3, distance4, distance5)

        time.sleep(timing/1000000.00)

    print("\n" + "=" * 70)
    print("Measurements completed")


def cleanup_all(pi, tof1, tof2, tof3, tof4, tof5):
    """
    すべてのハードウェアをクリーンアップします（pigpio版）。

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
    cleanup_sensors(pi, tof1, tof2, tof3, tof4, tof5)
    cleanup_actuators(pi)
    pi.stop()
    print("pigpio disconnected")
    print("Cleanup completed")


def main():
    """
    メインプログラム：5つの距離センサーで測定して距離を表示（pigpio版）
    """
    print("=" * 70)
    print("5-Sensor Distance Measurement System (pigpio version)")
    print("Sensor Configuration:")
    print("  Sensor 1: -70° (Left)")
    print("  Sensor 2: -20°")
    print("  Sensor 3:   0° (Front)")
    print("  Sensor 4: +20°")
    print("  Sensor 5: +70° (Right)")
    print("=" * 70)

    try:
        # pigpioとセンサーの初期化
        pi = initialize_pigpio()
        tof1, tof2, tof3, tof4, tof5 = initialize_sensors(pi)
        timing = get_timing(tof1)

        # 測定ループ実行
        run_measurement_loop(tof1, tof2, tof3, tof4, tof5, timing)

    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user")
    except RuntimeError as e:
        print(f"\nError: {e}")
        print("\nヒント: pigpiodデーモンを起動してください:")
        print("  sudo pigpiod")
    finally:
        try:
            cleanup_all(pi, tof1, tof2, tof3, tof4, tof5)
        except:
            print("Cleanup failed - pigpio may not be initialized")


if __name__ == "__main__":
    main()
