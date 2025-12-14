"""geometry.py のテスト - Point と Line クラスの単体テスト"""

import pytest
import math
from geometry import Point, Line


class TestPoint:
    """Point クラスのテスト"""

    # ========== 正常値テスト ==========

    def test_point_creation_normal(self):
        """正常値: Point の作成"""
        p = Point(10.0, 20.0)
        assert p.x == 10.0
        assert p.y == 20.0

    def test_from_polar_0_degrees(self):
        """正常値: 0度（正面）からの座標変換"""
        p = Point.from_polar(100.0, 0.0)
        assert abs(p.x - 0.0) < 0.001  # x = 100 * sin(0) = 0
        assert abs(p.y - 100.0) < 0.001  # y = 100 * cos(0) = 100

    def test_from_polar_90_degrees(self):
        """正常値: 90度（右）からの座標変換"""
        p = Point.from_polar(100.0, 90.0)
        assert abs(p.x - 100.0) < 0.001  # x = 100 * sin(90) = 100
        assert abs(p.y - 0.0) < 0.001  # y = 100 * cos(90) = 0

    def test_from_polar_minus_90_degrees(self):
        """正常値: -90度（左）からの座標変換"""
        p = Point.from_polar(100.0, -90.0)
        assert abs(p.x - (-100.0)) < 0.001  # x = 100 * sin(-90) = -100
        assert abs(p.y - 0.0) < 0.001  # y = 100 * cos(-90) = 0

    def test_from_polar_45_degrees(self):
        """正常値: 45度からの座標変換"""
        p = Point.from_polar(100.0, 45.0)
        expected_x = 100.0 * math.sin(math.radians(45.0))
        expected_y = 100.0 * math.cos(math.radians(45.0))
        assert abs(p.x - expected_x) < 0.001
        assert abs(p.y - expected_y) < 0.001

    def test_from_polar_sensor1_angle(self):
        """正常値: センサー1の角度（-70度）"""
        p = Point.from_polar(500.0, -70.0)
        expected_x = 500.0 * math.sin(math.radians(-70.0))
        expected_y = 500.0 * math.cos(math.radians(-70.0))
        assert abs(p.x - expected_x) < 0.001
        assert abs(p.y - expected_y) < 0.001
        assert p.x < 0  # 左側なので x は負

    # ========== 境界値テスト ==========

    def test_from_polar_zero_distance(self):
        """境界値: 距離が0の場合"""
        p = Point.from_polar(0.0, 45.0)
        assert abs(p.x) < 0.001
        assert abs(p.y) < 0.001

    def test_from_polar_180_degrees(self):
        """境界値: 180度（真後ろ）"""
        p = Point.from_polar(100.0, 180.0)
        assert abs(p.x - 0.0) < 0.001
        assert abs(p.y - (-100.0)) < 0.001  # 後ろなのでyは負

    def test_from_polar_360_degrees(self):
        """境界値: 360度（0度と同じ）"""
        p = Point.from_polar(100.0, 360.0)
        assert abs(p.x - 0.0) < 0.001
        assert abs(p.y - 100.0) < 0.001

    def test_point_repr(self):
        """正常値: __repr__ メソッド"""
        p = Point(12.345, 67.89)
        assert repr(p) == "Point(12.3, 67.9)"

    # ========== 異常値テスト ==========

    def test_from_polar_negative_distance(self):
        """異常値: 負の距離（数学的には有効だが物理的には異常）"""
        p = Point.from_polar(-100.0, 0.0)
        assert abs(p.x - 0.0) < 0.001
        assert abs(p.y - (-100.0)) < 0.001  # 負の距離は反対方向

    def test_from_polar_very_large_angle(self):
        """異常値: 非常に大きな角度"""
        p = Point.from_polar(100.0, 720.0)  # 2回転
        assert abs(p.x - 0.0) < 0.001
        assert abs(p.y - 100.0) < 0.001


class TestLine:
    """Line クラスのテスト"""

    # ========== 正常値テスト ==========

    def test_line_creation_normal(self):
        """正常値: Line の作成"""
        line = Line(2.0, 5.0)  # y = 2x + 5
        assert line.slope == 2.0
        assert line.intercept == 5.0

    def test_from_two_points_horizontal(self):
        """正常値: 水平線（傾き0）"""
        p1 = Point(0.0, 10.0)
        p2 = Point(100.0, 10.0)
        line = Line.from_two_points(p1, p2)
        assert line is not None
        assert abs(line.slope - 0.0) < 0.001
        assert abs(line.intercept - 10.0) < 0.001

    def test_from_two_points_diagonal(self):
        """正常値: 斜め45度の線（傾き1）"""
        p1 = Point(0.0, 0.0)
        p2 = Point(10.0, 10.0)
        line = Line.from_two_points(p1, p2)
        assert line is not None
        assert abs(line.slope - 1.0) < 0.001
        assert abs(line.intercept - 0.0) < 0.001

    def test_from_two_points_negative_slope(self):
        """正常値: 負の傾き"""
        p1 = Point(0.0, 10.0)
        p2 = Point(10.0, 0.0)
        line = Line.from_two_points(p1, p2)
        assert line is not None
        assert abs(line.slope - (-1.0)) < 0.001
        assert abs(line.intercept - 10.0) < 0.001

    def test_from_two_points_wall_scenario(self):
        """正常値: 実際の壁検出シナリオ"""
        # センサー1(-70度, 500mm), センサー2(-20度, 400mm)
        p1 = Point.from_polar(500.0, -70.0)
        p2 = Point.from_polar(400.0, -20.0)
        line = Line.from_two_points(p1, p2)
        assert line is not None
        # 傾きと切片が計算されていることを確認
        assert line.slope is not None
        assert line.intercept is not None

    def test_intersection_with_y_axis_positive(self):
        """正常値: y軸との交点（正の値）"""
        line = Line(2.0, 100.0)  # y = 2x + 100
        y = line.intersection_with_y_axis()
        assert abs(y - 100.0) < 0.001

    def test_intersection_with_y_axis_negative(self):
        """正常値: y軸との交点（負の値）"""
        line = Line(-1.5, -50.0)  # y = -1.5x - 50
        y = line.intersection_with_y_axis()
        assert abs(y - (-50.0)) < 0.001

    def test_line_repr(self):
        """正常値: __repr__ メソッド"""
        line = Line(1.234, 56.789)
        assert repr(line) == "Line(y = 1.23x + 56.8)"

    # ========== 境界値テスト ==========

    def test_from_two_points_steep_slope(self):
        """境界値: 非常に急な傾き"""
        p1 = Point(0.0, 0.0)
        p2 = Point(0.1, 1000.0)
        line = Line.from_two_points(p1, p2)
        assert line is not None
        assert abs(line.slope - 10000.0) < 0.1

    def test_from_two_points_shallow_slope(self):
        """境界値: 非常に緩い傾き"""
        p1 = Point(0.0, 0.0)
        p2 = Point(1000.0, 0.1)
        line = Line.from_two_points(p1, p2)
        assert line is not None
        assert abs(line.slope - 0.0001) < 0.00001

    def test_intersection_with_y_axis_zero(self):
        """境界値: y軸との交点が原点"""
        line = Line(3.0, 0.0)  # y = 3x
        y = line.intersection_with_y_axis()
        assert abs(y - 0.0) < 0.001

    # ========== 異常値テスト ==========

    def test_from_two_points_vertical_line(self):
        """異常値: 垂直線（傾きが無限大）"""
        p1 = Point(10.0, 0.0)
        p2 = Point(10.0, 100.0)
        line = Line.from_two_points(p1, p2)
        assert line is None  # 垂直線は表現できない

    def test_from_two_points_identical_points(self):
        """異常値: 同一の点"""
        p1 = Point(10.0, 20.0)
        p2 = Point(10.0, 20.0)
        line = Line.from_two_points(p1, p2)
        assert line is None  # 直線を定義できない

    def test_from_two_points_almost_identical(self):
        """異常値: ほぼ同一の点（0.0005mm差）"""
        p1 = Point(10.0, 20.0)
        p2 = Point(10.0005, 20.0005)
        line = Line.from_two_points(p1, p2)
        # 0.001未満の差は同一とみなされる
        assert line is None

    def test_from_two_points_almost_vertical(self):
        """異常値: ほぼ垂直な線（0.0005mm差）"""
        p1 = Point(10.0, 0.0)
        p2 = Point(10.0005, 100.0)
        line = Line.from_two_points(p1, p2)
        # x座標の差が0.001未満なので垂直線とみなされる
        assert line is None

    def test_from_two_points_very_close_horizontal(self):
        """異常値: ほぼ同じy座標の点（水平に近い）"""
        p1 = Point(0.0, 10.0)
        p2 = Point(1000.0, 10.0005)
        line = Line.from_two_points(p1, p2)
        assert line is not None
        assert abs(line.slope - 0.0) < 0.001  # ほぼ水平


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
