"""幾何計算モジュール - 座標、直線、交点計算"""

import math
from typing import Optional


class Point:
    """2D座標点を表すクラス"""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    @staticmethod
    def from_polar(distance: float, angle_deg: float) -> 'Point':
        """
        極座標から直交座標に変換

        Parameters:
            distance: 距離（mm）
            angle_deg: 角度（度）、正面=0、右=正、左=負

        Returns:
            Point: 直交座標の点
        """
        angle_rad = math.radians(angle_deg)
        x = distance * math.sin(angle_rad)
        y = distance * math.cos(angle_rad)
        return Point(x, y)

    def __repr__(self) -> str:
        return f"Point({self.x:.1f}, {self.y:.1f})"


class Line:
    """直線を表すクラス（y = mx + b）"""

    def __init__(self, slope: float, intercept: float):
        self.slope = slope          # 傾き m
        self.intercept = intercept  # 切片 b

    @staticmethod
    def from_two_points(p1: Point, p2: Point) -> Optional['Line']:
        """
        2点から直線を生成

        Parameters:
            p1, p2: 2つの点

        Returns:
            Line: 直線、または垂直線・同一点の場合はNone
        """
        # 2点が同一
        if abs(p1.x - p2.x) < 0.001 and abs(p1.y - p2.y) < 0.001:
            return None

        # 垂直線（x座標が同じ）
        if abs(p1.x - p2.x) < 0.001:
            return None

        # 傾きと切片を計算
        slope = (p2.y - p1.y) / (p2.x - p1.x)
        intercept = p1.y - slope * p1.x

        return Line(slope, intercept)

    def intersection_with_y_axis(self) -> float:
        """
        y軸（x=0）との交点のy座標を返す

        Returns:
            float: 交点のy座標
        """
        # x=0を代入: y = m*0 + b = b
        return self.intercept

    def __repr__(self) -> str:
        return f"Line(y = {self.slope:.2f}x + {self.intercept:.1f})"
