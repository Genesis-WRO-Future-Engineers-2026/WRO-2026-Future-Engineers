"""
壁追従制御モジュール - 壁検出計算とステアリング制御ロジック
"""

import math
from actuators import set_servo_angle
from config import (
    SENSOR1_ANGLE,
    SENSOR2_ANGLE,
    PARALLEL_ANGLE,
    ANGLE_TOLERANCE,
    TARGET_DISTANCE,
    DISTANCE_TOLERANCE,
    COUNTER_STEER_ANGLE,
    NEUTRAL_ANGLE
)


def calculate_wall_approach_angle(distance1, distance2, angle1=None, angle2=None):
    """
    2つのセンサーの距離測定値から、70度センサー位置での三角形の角度を計算

    Parameters:
    -----------
    distance1 : float
        センサー1(20度)で測定した壁までの距離
    distance2 : float
        センサー2(70度)で測定した壁までの距離
    angle1 : float, optional
        センサー1の角度(デフォルト: config.SENSOR1_ANGLE)
    angle2 : float, optional
        センサー2の角度(デフォルト: config.SENSOR2_ANGLE)

    Returns:
    --------
    triangle_angle : float
        70度センサー位置での三角形の内角(度)
        110度より大きい(鈍角) = 壁から離れている
        110度より小さい(鋭角) = 壁に近づいている
        110度(≈) = 壁と平行
    """
    if angle1 is None:
        angle1 = SENSOR1_ANGLE
    if angle2 is None:
        angle2 = SENSOR2_ANGLE

    # センサー間の角度差
    sensor_angle_diff = angle2 - angle1
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


def calculate_wall_distance(distance2, angle, sensor_angle=None):
    """
    70度センサーの距離と角度から壁までの垂直距離を計算

    Parameters:
    -----------
    distance2 : float
        センサー2(70度)で測定した壁までの距離
    angle : float
        calculate_wall_approach_angleで計算された角度
    sensor_angle : float, optional
        センサー2の角度(デフォルト: config.SENSOR2_ANGLE)

    Returns:
    --------
    wall_distance : float
        壁までの垂直距離（mm）
    """
    if sensor_angle is None:
        sensor_angle = SENSOR2_ANGLE

    # センサー角度をラジアンに変換
    sensor_angle_rad = math.radians(sensor_angle)

    # 壁までの垂直距離を計算（センサー距離 × sin(センサー角度)）
    wall_distance = distance2 * math.sin(sensor_angle_rad)

    return wall_distance


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
        return "Distance control (right/away)"
    elif wall_distance > TARGET_DISTANCE + DISTANCE_TOLERANCE:
        # 壁から遠すぎる（200mmより遠い）→ 左に切って壁に近づく
        set_servo_angle(servo_pwm, -COUNTER_STEER_ANGLE)
        return "Distance control (left/closer)"
    else:
        # 距離が適切（200mm付近）→ 角度に基づいて判断
        if angle < PARALLEL_ANGLE - ANGLE_TOLERANCE:
            # 壁に近づいている → 右に切って壁から離れる
            set_servo_angle(servo_pwm, COUNTER_STEER_ANGLE)
            return "Angle control (right)"
        elif angle > PARALLEL_ANGLE + ANGLE_TOLERANCE:
            # 壁から離れている → 左に切って壁に近づく
            set_servo_angle(servo_pwm, -COUNTER_STEER_ANGLE)
            return "Angle control (left)"
        else:
            # 壁とほぼ平行 → 直進
            set_servo_angle(servo_pwm, NEUTRAL_ANGLE)
            return "Angle control (straight)"
