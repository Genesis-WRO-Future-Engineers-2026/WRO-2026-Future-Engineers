"""
壁追従制御モジュール - 壁検出計算とステアリング制御ロジック
"""

import math
from actuators import set_servo_angle
from config import (
    SENSOR1_ANGLE,
    SENSOR2_ANGLE,
    SENSOR3_ANGLE,
    PARALLEL_ANGLE,
    TARGET_DISTANCE,
    DISTANCE_GAIN,
    ANGLE_GAIN,
    DISTANCE_WEIGHT,
    ANGLE_WEIGHT,
    MAX_STEER_ANGLE,
    MIN_STEER_ANGLE,
    DISTANCE_DEADZONE,
    ANGLE_DEADZONE,
    STRAIGHT_PATH_THRESHOLD,
    TURN_TO_STRAIGHT_ANGLE,
    STEERING_SMOOTHING_ENABLED,
    STEERING_ALPHA
)

# 前回のステアリング角度を保持（スムージング用）
_previous_steering_angle = 0.0


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
    global _previous_steering_angle

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

    # 7. スムージング適用（急激な変化を防ぐ）
    if STEERING_SMOOTHING_ENABLED:
        steering_angle = _apply_steering_smoothing(steering_angle)

    # 8. サーボに適用
    set_servo_angle(servo_pwm, steering_angle)

    # 9. 詳細ログを返す
    return _format_steer_action(
        steering_angle, distance_error, angle_error,
        distance_steering, angle_steering
    )


def _apply_steering_smoothing(target_angle):
    """
    ステアリング角度にローパスフィルタを適用して滑らかにします。

    Parameters:
    -----------
    target_angle : float
        目標ステアリング角度（度）

    Returns:
    --------
    float : スムージング適用後のステアリング角度（度）
    """
    global _previous_steering_angle

    # ローパスフィルタ（指数移動平均）
    smoothed_angle = (STEERING_ALPHA * target_angle +
                     (1 - STEERING_ALPHA) * _previous_steering_angle)

    # 次回のために保存
    _previous_steering_angle = smoothed_angle

    return smoothed_angle


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


def detect_straight_path(distance1, distance2):
    """
    20度または70度のセンサーで直線（開けた空間）を検出します。

    Parameters:
    -----------
    distance1 : float
        センサー2（20度）で測定した距離（mm）
    distance2 : float
        センサー3（70度）で測定した距離（mm）

    Returns:
    --------
    tuple (bool, str, float)
        (直線検出フラグ, 検出したセンサーの方向, 検出した距離)
        検出したセンサーの方向: "20deg" または "70deg"
        直線が検出されなかった場合: (False, "", 0)
    """
    # 20度センサーで直線検出
    if distance1 > STRAIGHT_PATH_THRESHOLD:
        return (True, "20deg", distance1)

    # 70度センサーで直線検出
    if distance2 > STRAIGHT_PATH_THRESHOLD:
        return (True, "70deg", distance2)

    return (False, "", 0)


def turn_to_straight_path(servo_pwm, detected_direction, distance0, distance1, distance2):
    """
    検出された直線方向に向けて、0度センサーの距離が最大になるように旋回します。

    Parameters:
    -----------
    servo_pwm : GPIO.PWM
        サーボ用PWMオブジェクト
    detected_direction : str
        直線を検出したセンサーの方向（"20deg" または "70deg"）
    distance0 : float
        センサー1（0度）の距離（mm）
    distance1 : float
        センサー2（20度）の距離（mm）
    distance2 : float
        センサー3（70度）の距離（mm）

    Returns:
    --------
    tuple (bool, str)
        (旋回継続フラグ, ステアリング動作の説明)
        旋回継続フラグ: 0度センサーが最大を向いたらFalse
    """
    # 0度センサーの距離が20度と70度の両方より大きければ、正面を向いている
    if distance0 > distance1 and distance0 > distance2:
        set_servo_angle(servo_pwm, 0)  # 直進
        return (False, f"Front sensor maximized ({distance0:.0f}mm) - straight ahead")

    # まだ旋回が必要な場合、検出した方向に旋回
    if detected_direction == "20deg":
        # 20度方向に旋回（右寄りなので、やや右にステアリング）
        steering_angle = -TURN_TO_STRAIGHT_ANGLE * 0.5
    else:  # 70deg
        # 70度方向に旋回（左にステアリング）
        steering_angle = -TURN_TO_STRAIGHT_ANGLE

    set_servo_angle(servo_pwm, steering_angle)

    direction = "left" if steering_angle < 0 else "right" if steering_angle > 0 else "straight"
    return (True, f"Turning to {detected_direction} path: {steering_angle:+.1f}° ({direction}) | Front:{distance0:.0f}mm, 20deg:{distance1:.0f}mm, 70deg:{distance2:.0f}mm")


# ============================================================================
# 5センサー壁追従ハンドリング機能
# ============================================================================

def calculate_point_from_sensor(distance, angle_deg):
    """
    センサーの測定値から壁上の点の座標を計算します。

    座標系：
    - 原点: 車体位置 (0, 0)
    - x軸: 右が正(+)、左が負(-)
    - y軸: 正面方向が正(+)

    Parameters:
    -----------
    distance : float
        センサーで測定した距離（mm）
    angle_deg : float
        センサーの角度（度）、正面=0、右=正、左=負

    Returns:
    --------
    tuple (x, y) : 壁上の点の座標（mm）

    例:
    --------
    >>> calculate_point_from_sensor(100, -70)  # 左側センサー
    (-94.0, 34.2)  # 左前方の点
    """
    angle_rad = math.radians(angle_deg)
    x = distance * math.sin(angle_rad)
    y = distance * math.cos(angle_rad)
    return (x, y)


def calculate_line_from_two_points(p1, p2):
    """
    2点から直線の方程式を求めます（y = mx + b の形式）。

    Parameters:
    -----------
    p1 : tuple (x1, y1)
        点1の座標
    p2 : tuple (x2, y2)
        点2の座標

    Returns:
    --------
    tuple (m, b) or None
        直線の傾きm と切片b、または垂直線の場合はNone
        y = mx + b の形式

    注意:
    --------
    - 2点が同一の場合、Noneを返す
    - 直線が垂直（x1 == x2）の場合、Noneを返す
    """
    x1, y1 = p1
    x2, y2 = p2

    # 2点が同一の場合
    if abs(x1 - x2) < 0.001 and abs(y1 - y2) < 0.001:
        return None

    # 垂直線の場合（x座標が同じ）
    if abs(x1 - x2) < 0.001:
        return None

    # 傾きを計算
    m = (y2 - y1) / (x2 - x1)

    # 切片を計算 (b = y - mx)
    b = y1 - m * x1

    return (m, b)


def find_intersection_with_y_axis(line):
    """
    直線とy軸（x=0）の交点を求めます。

    Parameters:
    -----------
    line : tuple (m, b) or None
        直線の傾きと切片（y = mx + b）

    Returns:
    --------
    float or None
        交点のy座標、交点がない場合（垂直線）はNone

    計算:
    --------
    x = 0 を代入して y = m*0 + b = b
    """
    if line is None:
        return None

    m, b = line
    # x = 0 を代入
    y = b

    return y


def determine_steering_angle(left_y, right_y, front_distance):
    """
    左右の壁の交点と正面距離からステアリング角度を決定します。

    Parameters:
    -----------
    left_y : float or None
        左側の壁の交点y座標（mm）
    right_y : float or None
        右側の壁の交点y座標（mm）
    front_distance : float
        正面センサーの距離（mm）

    Returns:
    --------
    float : ステアリング角度（度）、-MAX_STEER_ANGLE～MAX_STEER_ANGLE

    ロジック:
    --------
    1. 両方の交点が存在する場合:
       - 中間点を目指すように計算
       - 左右の交点の差から角度を決定
    2. 左のみ存在する場合:
       - 右にステア（正の角度）
    3. 右のみ存在する場合:
       - 左にステア（負の角度）
    4. どちらも存在しない場合:
       - 正面を維持（0度）
    """
    # 両方の交点が存在する場合
    if left_y is not None and right_y is not None:
        # 左右の交点の中間点を目指す
        # 交点が前方にあり、左右で差がある場合
        if left_y > 0 and right_y > 0:
            # 左右の差を基にステアリング角度を計算
            # 左が近い（小さい）場合は右にステア、右が近い場合は左にステア
            y_diff = left_y - right_y
            # ゲインを適用（1mm差で0.1度の調整）
            steering = y_diff * 0.1
            # リミット適用
            steering = max(-MAX_STEER_ANGLE, min(MAX_STEER_ANGLE, steering))
            return steering
        else:
            # 交点が後方の場合は正面を維持
            return 0.0

    # 左のみ存在する場合（右側が開けている）
    elif left_y is not None and left_y > 0:
        # 右にステア（正の角度）
        return MAX_STEER_ANGLE * 0.5

    # 右のみ存在する場合（左側が開けている）
    elif right_y is not None and right_y > 0:
        # 左にステア（負の角度）
        return -MAX_STEER_ANGLE * 0.5

    # どちらも存在しない場合
    else:
        # 正面を維持
        return 0.0


def calculate_steering_from_five_sensors(servo_pwm, d1, d2, d3, d4, d5):
    """
    5つのセンサーの測定値から最適なステアリング角度を計算して適用します。

    Parameters:
    -----------
    servo_pwm : GPIO.PWM
        サーボ用PWMオブジェクト
    d1 : float
        センサー1（-70度・左）の距離（mm）
    d2 : float
        センサー2（-20度）の距離（mm）
    d3 : float
        センサー3（0度・正面）の距離（mm）
    d4 : float
        センサー4（+20度）の距離（mm）
    d5 : float
        センサー5（+70度・右）の距離（mm）

    Returns:
    --------
    str : ステアリング動作の説明

    処理フロー:
    --------
    1. 各センサーから壁上の点を計算
    2. 左側の直線（P1-P2）を計算
    3. 右側の直線（P4-P5）を計算
    4. 各直線とy軸の交点を計算
    5. 交点の位置関係からステアリング角度を決定
    6. サーボに適用
    """
    # 1. 各センサーから壁上の点を計算
    from config import SENSOR1_ANGLE, SENSOR2_ANGLE, SENSOR4_ANGLE, SENSOR5_ANGLE

    p1 = calculate_point_from_sensor(d1, SENSOR1_ANGLE)  # -70度・左
    p2 = calculate_point_from_sensor(d2, SENSOR2_ANGLE)  # -20度
    # p3 = (0, d3)  # 0度・正面（y軸上なので使用しない）
    p4 = calculate_point_from_sensor(d4, SENSOR4_ANGLE)  # +20度
    p5 = calculate_point_from_sensor(d5, SENSOR5_ANGLE)  # +70度・右

    # デバッグ出力: 壁上の点
    print(f"  [Points] P1:{p1[0]:.0f},{p1[1]:.0f} P2:{p2[0]:.0f},{p2[1]:.0f} P4:{p4[0]:.0f},{p4[1]:.0f} P5:{p5[0]:.0f},{p5[1]:.0f}")

    # 2. 左側の直線を計算（P1-P2）
    left_line = calculate_line_from_two_points(p1, p2)

    # 3. 右側の直線を計算（P4-P5）
    right_line = calculate_line_from_two_points(p4, p5)

    # デバッグ出力: 直線の方程式
    if left_line:
        print(f"  [Left Wall] y = {left_line[0]:.2f}x + {left_line[1]:.0f}")
    else:
        print(f"  [Left Wall] vertical line (cannot calculate)")

    if right_line:
        print(f"  [Right Wall] y = {right_line[0]:.2f}x + {right_line[1]:.0f}")
    else:
        print(f"  [Right Wall] vertical line (cannot calculate)")

    # 4. 各直線とy軸（x=0）の交点を計算
    left_y = find_intersection_with_y_axis(left_line)
    right_y = find_intersection_with_y_axis(right_line)

    # デバッグ出力: 交点
    if left_y is not None:
        print(f"  [Left Intersection] y = {left_y:.0f} mm")
    else:
        print(f"  [Left Intersection] None")

    if right_y is not None:
        print(f"  [Right Intersection] y = {right_y:.0f} mm")
    else:
        print(f"  [Right Intersection] None")

    # 5. 交点の位置関係からステアリング角度を決定
    steering_angle = determine_steering_angle(left_y, right_y, d3)

    # 6. サーボに適用
    set_servo_angle(servo_pwm, steering_angle)

    # 7. ステアリング動作の説明を返す
    direction = "straight" if abs(steering_angle) < 0.1 else ("right" if steering_angle > 0 else "left")
    return f"5-Sensor Steer: {steering_angle:+.1f}° ({direction}) | Front:{d3:.0f}mm"
