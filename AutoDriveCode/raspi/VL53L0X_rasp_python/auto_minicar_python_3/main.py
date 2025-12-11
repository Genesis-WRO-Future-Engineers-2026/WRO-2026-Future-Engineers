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

"""メインプログラム - 5センサー自動運転システム"""

import time
import RPi.GPIO as GPIO
from typing import Dict

from config import DEFAULT_ITERATIONS
from sensors import SensorManager
from actuators import Actuator
from steering_controller import SteeringController


class AutoDriveCar:
    """自動運転ミニカーのメインクラス"""

    def __init__(self):
        self.sensor_manager = SensorManager()
        self.actuator = Actuator()
        self.steering_controller = SteeringController(debug=True)

    def run(self, iterations: int = DEFAULT_ITERATIONS):
        """メインループを実行"""
        timing = self.sensor_manager.get_timing()

        print("\nStarting distance measurements...")
        print("=" * 70)

        for count in range(1, iterations + 1):
            # 1. センサー読み取り
            distances = self.sensor_manager.read_all_distances()

            # 2. 距離表示
            self._print_distances(count, iterations, distances)

            # 3. 全センサーが有効な場合、ステアリング計算
            if self._all_sensors_valid(distances):
                decision = self.steering_controller.calculate_steering(
                    distances,
                    self.sensor_manager.get_sensor_angles()
                )

                # 4. アクチュエーターに適用
                self.actuator.set_steering_angle(decision.angle)

                # 5. 結果表示
                print(f"  >> Steer: {decision.angle:+.1f}° ({decision.direction}) - {decision.reason}")

            time.sleep(timing / 1000000.0)

        print("\n" + "=" * 70)
        print("Measurements completed")

    def _print_distances(self, count: int, total: int, distances: Dict[str, float]):
        """距離を表示"""
        print(f"\n--- Iteration {count}/{total} ---")
        for sensor_id, distance in distances.items():
            angle = self.sensor_manager.get_sensor_angles()[sensor_id]
            if distance > 0:
                print(f"  {sensor_id} ({angle:+3d}°): {distance:4d} mm ({distance/10:.1f} cm)")
            else:
                print(f"  {sensor_id} ({angle:+3d}°): Error")

    def _all_sensors_valid(self, distances: Dict[str, float]) -> bool:
        """全センサーが有効な値を返しているか確認"""
        return all(d > 0 for d in distances.values())

    def cleanup(self):
        """クリーンアップ"""
        self.sensor_manager.cleanup()
        self.actuator.cleanup()
        GPIO.cleanup()
        print("Cleanup completed")


def main():
    print("=" * 70)
    print("5-Sensor Auto Drive System")
    print("Sensor Configuration:")
    print("  Sensor 1: -70° (Left)")
    print("  Sensor 2: -20°")
    print("  Sensor 3:   0° (Front)")
    print("  Sensor 4: +20°")
    print("  Sensor 5: +70° (Right)")
    print("=" * 70)

    car = AutoDriveCar()
    try:
        car.run()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user")
    finally:
        car.cleanup()


if __name__ == "__main__":
    main()
