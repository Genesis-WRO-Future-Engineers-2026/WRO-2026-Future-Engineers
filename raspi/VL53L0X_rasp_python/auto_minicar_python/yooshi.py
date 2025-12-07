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

# サーボとESCのGPIOピン設定
SERVO_PIN = 12  # サーボ用GPIO 12
ESC_PIN = 13    # ESC用GPIO 13

# 壁と平行時の基準角度と許容誤差
PARALLEL_ANGLE = 110.0
TOLERANCE = 2.0

# 壁までの目標距離と許容誤差
TARGET_DISTANCE = 200.0    # 目標距離 200mm
DISTANCE_TOLERANCE = 20.0  # 距離の許容誤差

# カウンターステアの設定
COUNTER_STEER_ANGLE = 30   # 壁に近づいている時のカウンターステア角度（右に切る）
NEUTRAL_ANGLE = 0          # ニュートラル（直進）
SPEED_PULSE = 1.52         # 前進速度（パルス幅ms）
STOP_PULSE = 1.5           # 停止（パルス幅ms）


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


def calculate_wall_distance(distance2, angle, sensor_angle=70):
    """
    70度センサーの距離と角度から壁までの垂直距離を計算

    Parameters:
    -----------
    distance2 : float
        センサー2(70度)で測定した壁までの距離
    angle : float
        calculate_wall_approach_angleで計算された角度
    sensor_angle : float
        センサー2の角度(デフォルト: 70度)

    Returns:
    --------
    wall_distance : float
        壁までの垂直距離（mm）
    """
    # センサー角度をラジアンに変換
    sensor_angle_rad = math.radians(sensor_angle)

    # 壁までの垂直距離を計算（センサー距離 × sin(センサー角度)）
    wall_distance = distance2 * math.sin(sensor_angle_rad)

    return wall_distance


def set_servo_angle(servo_pwm, angle):
    """
    サーボの角度を設定します。角度は-90度から90度の範囲です。

    Parameters:
    -----------
    servo_pwm : GPIO.PWM
        サーボ用PWMオブジェクト
    angle : float
        設定する角度（-90～90度）
    """
    # 角度をパルス幅に変換（0.5ms～2.4ms）
    min_pulse_width_ms = 0.5
    max_pulse_width_ms = 2.4

    # 角度からパルス幅を計算
    pulse_width_ms = ((angle + 90) / 180) * (max_pulse_width_ms - min_pulse_width_ms) + min_pulse_width_ms

    # パルス幅をデューティサイクルに変換（50Hzの場合、1周期は20ms）
    duty_cycle = (pulse_width_ms / 20.0) * 100
    servo_pwm.ChangeDutyCycle(duty_cycle)


def set_esc_speed(esc_pwm, pulse_width_ms):
    """
    ESCの速度を設定します。パルス幅はミリ秒単位で指定します。

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


def apply_counter_steer(servo_pwm, angle, wall_distance):
    """
    壁との角度と距離に基づいてカウンターステアを適用します。
    ※センサーは車体の左側を向いています

    Parameters:
    -----------
    servo_pwm : GPIO.PWM
        サーボ用PWMオブジェクト
    angle : float
        壁との角度（度）
    wall_distance : float
        壁までの垂直距離（mm）

    Returns:
    --------
    steer_action : str
        実行したステアリング動作の説明
    """
    # まず距離を優先して判断
    if wall_distance < TARGET_DISTANCE - DISTANCE_TOLERANCE:
        # 壁に近すぎる（200mm未満）→ 右に切って壁から離れる
        set_servo_angle(servo_pwm, COUNTER_STEER_ANGLE)
        return "距離制御（右・離れる）"
    elif wall_distance > TARGET_DISTANCE + DISTANCE_TOLERANCE:
        # 壁から遠すぎる（200mmより遠い）→ 左に切って壁に近づく
        set_servo_angle(servo_pwm, -COUNTER_STEER_ANGLE)
        return "距離制御（左・近づく）"
    else:
        # 距離が適切（200mm付近）→ 角度に基づいて判断
        if angle < PARALLEL_ANGLE - TOLERANCE:
            # 壁に近づいている → 右に切って壁から離れる
            set_servo_angle(servo_pwm, COUNTER_STEER_ANGLE)
            return "角度制御（右）"
        elif angle > PARALLEL_ANGLE + TOLERANCE:
            # 壁から離れている → 左に切って壁に近づく
            set_servo_angle(servo_pwm, -COUNTER_STEER_ANGLE)
            return "角度制御（左）"
        else:
            # 壁とほぼ平行 → 直進
            set_servo_angle(servo_pwm, NEUTRAL_ANGLE)
            return "角度制御（直進）"


def initialize_gpio():
    """
    GPIOピンを初期化します（センサー、サーボ、ESC）

    Returns:
    --------
    servo_pwm, esc_pwm : GPIO.PWM
        サーボとESC用のPWMオブジェクト
    """
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SENSOR1_SHUTDOWN, GPIO.OUT)
    GPIO.setup(SENSOR2_SHUTDOWN, GPIO.OUT)

    # サーボとESCのピンを設定
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    GPIO.setup(ESC_PIN, GPIO.OUT)

    # PWM初期化（50Hz）
    servo_pwm = GPIO.PWM(SERVO_PIN, 50)
    esc_pwm = GPIO.PWM(ESC_PIN, 50)
    servo_pwm.start(0)
    esc_pwm.start(0)

    # 初期状態に設定
    set_servo_angle(servo_pwm, NEUTRAL_ANGLE)
    set_esc_speed(esc_pwm, STOP_PULSE)
    time.sleep(1)

    return servo_pwm, esc_pwm


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


def run_measurement_loop(tof, tof1, timing, servo_pwm, esc_pwm, iterations=100):
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
    iterations : int
        測定回数（デフォルト: 100）
    """
    # モーターを前進させる
    set_esc_speed(esc_pwm, SPEED_PULSE)
    print("モーター前進開始")

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

        # 両方のセンサーが正常に距離を取得できた場合、壁との角度と距離を計算
        if distance1 > 0 and distance2 > 0:
            angle = calculate_wall_approach_angle(distance1, distance2)
            wall_distance = calculate_wall_distance(distance2, angle)

            print("  壁との角度: %.2f度, 壁までの距離: %.1f mm" % (angle, wall_distance), end="")

            # カウンターステアを適用（角度と距離の両方を考慮）
            steer_action = apply_counter_steer(servo_pwm, angle, wall_distance)

            if wall_distance < TARGET_DISTANCE - DISTANCE_TOLERANCE:
                print(" → 壁に近い [%s]" % steer_action)
            elif wall_distance > TARGET_DISTANCE + DISTANCE_TOLERANCE:
                print(" → 壁から遠い [%s]" % steer_action)
            elif angle > PARALLEL_ANGLE + TOLERANCE:
                print(" → 距離OK・壁から離れている [%s]" % steer_action)
            elif angle < PARALLEL_ANGLE - TOLERANCE:
                print(" → 距離OK・壁に近づいている [%s]" % steer_action)
            else:
                print(" → 距離OK・壁とほぼ平行 [%s]" % steer_action)

        print()  # 空行を追加して見やすく
        time.sleep(timing/1000000.00)

    # 測定終了後、停止
    set_esc_speed(esc_pwm, STOP_PULSE)
    set_servo_angle(servo_pwm, NEUTRAL_ANGLE)
    print("モーター停止")


def cleanup_sensors(tof, tof1, servo_pwm=None, esc_pwm=None):
    """
    センサー、サーボ、ESCをクリーンアップします。

    Parameters:
    -----------
    tof : VL53L0X
        センサー1
    tof1 : VL53L0X
        センサー2
    servo_pwm : GPIO.PWM (optional)
        サーボ用PWMオブジェクト
    esc_pwm : GPIO.PWM (optional)
        ESC用PWMオブジェクト
    """
    # センサーのクリーンアップ
    tof1.stop_ranging()
    GPIO.output(SENSOR2_SHUTDOWN, GPIO.LOW)
    tof.stop_ranging()
    GPIO.output(SENSOR1_SHUTDOWN, GPIO.LOW)

    # サーボとESCのクリーンアップ
    if servo_pwm is not None and esc_pwm is not None:
        set_servo_angle(servo_pwm, NEUTRAL_ANGLE)
        set_esc_speed(esc_pwm, STOP_PULSE)
        time.sleep(0.5)
        servo_pwm.stop()
        esc_pwm.stop()

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
        cleanup_sensors(tof, tof1, servo_pwm, esc_pwm)


if __name__ == "__main__":
    main()

