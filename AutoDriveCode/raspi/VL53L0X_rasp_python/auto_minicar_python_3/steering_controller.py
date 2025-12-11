"""ステアリング制御モジュール - 5センサーベースのハンドリング判断"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from geometry import Point, Line
from config import MAX_STEER_ANGLE, INTERSECTION_DIFF_GAIN, ONE_SIDE_OPEN_STEER_RATIO


@dataclass
class SteeringDecision:
    """ステアリング判断結果を保持するデータクラス"""
    angle: float                              # ステアリング角度
    direction: str                            # "left", "right", "straight"
    left_intersection: Optional[float]        # 左壁の交点y座標
    right_intersection: Optional[float]       # 右壁の交点y座標
    reason: str                               # 判断理由


class SteeringController:
    """5センサーベースのステアリング制御クラス"""

    def __init__(self, debug: bool = True):
        self.debug = debug

    def calculate_steering(self,
                          distances: Dict[str, float],
                          sensor_angles: Dict[str, float]) -> SteeringDecision:
        """
        5センサーの測定値からステアリング判断を計算

        Parameters:
            distances: {"sensor1": d1, "sensor2": d2, ...}
            sensor_angles: {"sensor1": -70, "sensor2": -20, ...}

        Returns:
            SteeringDecision: ステアリング判断結果
        """
        # 1. 壁上の点を計算
        points = self._calculate_wall_points(distances, sensor_angles)

        # 2. 左右の壁の直線を計算
        left_line, right_line = self._calculate_wall_lines(points)

        # 3. 交点を計算
        left_y = left_line.intersection_with_y_axis() if left_line else None
        right_y = right_line.intersection_with_y_axis() if right_line else None

        # 4. ステアリング角度を決定
        angle, reason = self._determine_angle(left_y, right_y, distances['sensor3'])

        # 5. デバッグ出力
        if self.debug:
            self._print_debug(points, left_line, right_line, left_y, right_y)

        return SteeringDecision(
            angle=angle,
            direction=self._angle_to_direction(angle),
            left_intersection=left_y,
            right_intersection=right_y,
            reason=reason
        )

    def _calculate_wall_points(self,
                               distances: Dict[str, float],
                               angles: Dict[str, float]) -> Dict[str, Point]:
        """センサーから壁上の点を計算"""
        return {
            sensor_id: Point.from_polar(distances[sensor_id], angles[sensor_id])
            for sensor_id in distances.keys()
        }

    def _calculate_wall_lines(self, points: Dict[str, Point]) -> Tuple[Optional[Line], Optional[Line]]:
        """左右の壁の直線を計算"""
        left_line = Line.from_two_points(points['sensor1'], points['sensor2'])
        right_line = Line.from_two_points(points['sensor4'], points['sensor5'])
        return left_line, right_line

    def _determine_angle(self,
                        left_y: Optional[float],
                        right_y: Optional[float],
                        front_dist: float) -> Tuple[float, str]:
        """交点からステアリング角度を決定"""
        # 壁検出の閾値（この距離より遠い交点は無視）
        MAX_WALL_DISTANCE = 1500.0

        # 有効な壁の判定
        left_valid = left_y is not None and 0 < left_y < MAX_WALL_DISTANCE
        right_valid = right_y is not None and 0 < right_y < MAX_WALL_DISTANCE

        # 両方の壁が有効
        if left_valid and right_valid:
            y_diff = left_y - right_y
            # left_y > right_y = 左壁が遠い = 右寄り = 左にステアリング（負）
            steering = -y_diff * INTERSECTION_DIFF_GAIN
            steering = max(-MAX_STEER_ANGLE, min(MAX_STEER_ANGLE, steering))
            return steering, f"両壁検出: 左{left_y:.0f}mm, 右{right_y:.0f}mm"

        # 左のみ有効（右側が開けている）
        elif left_valid and not right_valid:
            steering = MAX_STEER_ANGLE * ONE_SIDE_OPEN_STEER_RATIO
            return steering, f"右側開放: 左壁{left_y:.0f}mm"

        # 右のみ有効（左側が開けている）
        elif right_valid and not left_valid:
            steering = -MAX_STEER_ANGLE * ONE_SIDE_OPEN_STEER_RATIO
            return steering, f"左側開放: 右壁{right_y:.0f}mm"

        # どちらも無効
        else:
            return 0.0, "交点なし: 直進"

    def _angle_to_direction(self, angle: float) -> str:
        """角度から方向文字列を生成"""
        if abs(angle) < 0.1:
            return "straight"
        return "right" if angle > 0 else "left"

    def _print_debug(self,
                    points: Dict[str, Point],
                    left_line: Optional[Line],
                    right_line: Optional[Line],
                    left_y: Optional[float],
                    right_y: Optional[float]):
        """デバッグ情報を出力"""
        p1, p2, p4, p5 = points['sensor1'], points['sensor2'], points['sensor4'], points['sensor5']
        print(f"  [Points] P1:{p1.x:.0f},{p1.y:.0f} P2:{p2.x:.0f},{p2.y:.0f} "
              f"P4:{p4.x:.0f},{p4.y:.0f} P5:{p5.x:.0f},{p5.y:.0f}")

        if left_line:
            print(f"  [Left Wall] {left_line}")
        else:
            print(f"  [Left Wall] vertical line (cannot calculate)")

        if right_line:
            print(f"  [Right Wall] {right_line}")
        else:
            print(f"  [Right Wall] vertical line (cannot calculate)")

        if left_y is not None:
            print(f"  [Left Intersection] y = {left_y:.0f} mm")
        else:
            print(f"  [Left Intersection] None")

        if right_y is not None:
            print(f"  [Right Intersection] y = {right_y:.0f} mm")
        else:
            print(f"  [Right Intersection] None")
