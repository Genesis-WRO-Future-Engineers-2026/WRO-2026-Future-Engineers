"""
壁追従制御モジュール - 壁検出計算とステアリング制御ロジック
"""

import math
from actuators import set_servo_angle
from config import (
    SENSOR1_ANGLE,
    SENSOR2_ANGLE,
    PARALLEL_ANGLE,
    TARGET_DISTANCE,
    DISTANCE_GAIN,
    ANGLE_GAIN,
    DISTANCE_WEIGHT,
    ANGLE_WEIGHT,
    MAX_STEER_ANGLE,
    MIN_STEER_ANGLE,
    DISTANCE_DEADZONE,
    ANGLE_DEADZONE
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
    壁との角度と距離に基づいて動的ステアリングを適用します（比例制御）。
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
        実行したステアリング動作の説明（角度を含む）
    """
    # 1. 誤差を計算
    distance_error = wall_distance - TARGET_DISTANCE
    angle_error = angle - PARALLEL_ANGLE

    # 2. デッドゾーン適用
    if abs(distance_error) < DISTANCE_DEADZONE:
        distance_error = 0.0
    if abs(angle_error) < ANGLE_DEADZONE:
        angle_error = 0.0

    # 3. 各補正量を計算
    distance_steering = -distance_error * DISTANCE_GAIN
    angle_steering = -angle_error * ANGLE_GAIN

    # 4. 重み付け合成
    total_weight = DISTANCE_WEIGHT + ANGLE_WEIGHT
    steering_angle = (
        distance_steering * DISTANCE_WEIGHT +
        angle_steering * ANGLE_WEIGHT
    ) / total_weight

    # 5. リミット適用
    steering_angle = max(-MAX_STEER_ANGLE, min(MAX_STEER_ANGLE, steering_angle))

    # 6. 最小閾値
    if abs(steering_angle) < MIN_STEER_ANGLE:
        steering_angle = 0.0

    # 7. サーボに適用
    set_servo_angle(servo_pwm, steering_angle)

    # 8. 詳細ログを返す
    return _format_steer_action(
        steering_angle, distance_error, angle_error,
        distance_steering, angle_steering
    )


def _format_steer_action(steering_angle, distance_error, angle_error,
                         distance_steering, angle_steering):
    """
    ステアリング動作の説明文を生成します。

    Parameters:
    -----------
    steering_angle : float
        適用されたステアリング角度
    distance_error : float
        距離誤差（mm）
    angle_error : float
        角度誤差（度）
    distance_steering : float
        距離補正による操舵角
    angle_steering : float
        角度補正による操舵角

    Returns:
    --------
    str : 詳細な動作説明
    """
    direction = "straight"
    if steering_angle > 0:
        direction = "right"
    elif steering_angle < 0:
        direction = "left"

    return (
        f"Steer {steering_angle:+.1f}° ({direction}) | "
        f"Dist:{distance_error:+.1f}mm→{distance_steering:+.1f}° | "
        f"Ang:{angle_error:+.1f}°→{angle_steering:+.1f}°"
    )
