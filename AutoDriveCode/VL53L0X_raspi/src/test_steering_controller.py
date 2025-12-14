"""steering_controller.py のテスト - SteeringController クラスの単体テスト"""

import pytest
from unittest.mock import patch
from steering_controller import SteeringController, SteeringDecision
from config import MAX_STEER_ANGLE, INTERSECTION_DIFF_GAIN, ONE_SIDE_OPEN_STEER_RATIO


class TestSteeringController:
    """SteeringController クラスのテスト"""

    @pytest.fixture
    def controller(self):
        """テスト用のコントローラーインスタンス（デバッグ無効）"""
        return SteeringController(debug=False)

    @pytest.fixture
    def sensor_angles(self):
        """テスト用のセンサー角度"""
        return {
            'sensor1': -70,
            'sensor2': -20,
            'sensor3': 0,
            'sensor4': 20,
            'sensor5': 70
        }

    # ========== 正常値テスト ==========

    def test_both_walls_detected_center(self, controller, sensor_angles):
        """正常値: 両壁検出、中央走行"""
        # 左右対称の距離（中央を走行）
        distances = {
            'sensor1': 500.0,  # -70度 左
            'sensor2': 400.0,  # -20度
            'sensor3': 800.0,  # 0度 正面
            'sensor4': 400.0,  # +20度
            'sensor5': 500.0   # +70度 右
        }
        decision = controller.calculate_steering(distances, sensor_angles)

        # 左右がほぼ対称なのでステアリングはほぼ0
        assert abs(decision.angle) < 5.0
        assert decision.direction in ["straight", "left", "right"]
        assert decision.left_intersection is not None
        assert decision.right_intersection is not None

    def test_both_walls_detected_left_bias(self, controller, sensor_angles):
        """正常値: 両壁検出、左寄り走行（右にステアリングすべき）"""
        distances = {
            'sensor1': 300.0,  # 左壁が近い
            'sensor2': 250.0,
            'sensor3': 800.0,
            'sensor4': 600.0,  # 右壁が遠い
            'sensor5': 700.0
        }
        decision = controller.calculate_steering(distances, sensor_angles)

        # 左に寄っているので右にステアリング（正の角度）
        assert decision.angle > 0
        assert decision.direction == "right"
        assert "両壁検出" in decision.reason

    def test_both_walls_detected_right_bias(self, controller, sensor_angles):
        """正常値: 両壁検出、右寄り走行（左にステアリングすべき）"""
        distances = {
            'sensor1': 700.0,  # 左壁が遠い
            'sensor2': 600.0,
            'sensor3': 800.0,
            'sensor4': 250.0,  # 右壁が近い
            'sensor5': 300.0
        }
        decision = controller.calculate_steering(distances, sensor_angles)

        # 右に寄っているので左にステアリング（負の角度）
        assert decision.angle < 0
        assert decision.direction == "left"
        assert "両壁検出" in decision.reason

    def test_only_left_wall_detected(self, controller, sensor_angles):
        """正常値: 左壁のみ検出（右側開放）"""
        distances = {
            'sensor1': 500.0,
            'sensor2': 400.0,
            'sensor3': 1500.0,  # 正面が開けている
            'sensor4': 1500.0,  # 右側が開けている
            'sensor5': 1500.0
        }
        decision = controller.calculate_steering(distances, sensor_angles)

        # 右側が開けているので右にステアリング
        assert decision.angle > 0
        expected_angle = MAX_STEER_ANGLE * ONE_SIDE_OPEN_STEER_RATIO
        assert abs(decision.angle - expected_angle) < 0.1
        assert decision.direction == "right"
        assert "右側開放" in decision.reason

    def test_only_right_wall_detected(self, controller, sensor_angles):
        """正常値: 右壁のみ検出（左側開放）"""
        distances = {
            'sensor1': 1500.0,  # 左側が開けている
            'sensor2': 1500.0,
            'sensor3': 1500.0,
            'sensor4': 400.0,  # 右壁のみ検出
            'sensor5': 500.0
        }
        decision = controller.calculate_steering(distances, sensor_angles)

        # 左側が開けているので左にステアリング
        assert decision.angle < 0
        expected_angle = -MAX_STEER_ANGLE * ONE_SIDE_OPEN_STEER_RATIO
        assert abs(decision.angle - expected_angle) < 0.1
        assert decision.direction == "left"
        assert "左側開放" in decision.reason

    def test_no_walls_detected(self, controller, sensor_angles):
        """正常値: 壁が検出されない（開けた空間）"""
        distances = {
            'sensor1': 2000.0,
            'sensor2': 2000.0,
            'sensor3': 2000.0,
            'sensor4': 2000.0,
            'sensor5': 2000.0
        }
        decision = controller.calculate_steering(distances, sensor_angles)

        # 壁がないので直進
        assert decision.angle == 0.0
        assert decision.direction == "straight"
        assert "交点なし" in decision.reason or "直進" in decision.reason

    # ========== 境界値テスト ==========

    def test_max_steering_angle_limit(self, controller, sensor_angles):
        """境界値: 最大ステアリング角度のリミット"""
        # 極端に左に寄った状態
        distances = {
            'sensor1': 100.0,  # 非常に近い左壁
            'sensor2': 150.0,
            'sensor3': 800.0,
            'sensor4': 800.0,  # 遠い右壁
            'sensor5': 900.0
        }
        decision = controller.calculate_steering(distances, sensor_angles)

        # ステアリング角度が最大値を超えない
        assert abs(decision.angle) <= MAX_STEER_ANGLE

    def test_intersection_exactly_zero(self, controller, sensor_angles):
        """境界値: 交点がちょうど0（車体位置）"""
        # センサー1,2が直線上でy軸との交点が0になる配置
        distances = {
            'sensor1': 500.0,
            'sensor2': 500.0,  # 同じ距離
            'sensor3': 800.0,
            'sensor4': 400.0,
            'sensor5': 500.0
        }
        decision = controller.calculate_steering(distances, sensor_angles)
        # 計算は実行される（エラーにならない）
        assert decision.angle is not None

    def test_very_small_angle_is_straight(self, controller, sensor_angles):
        """境界値: 非常に小さい角度は直進扱い"""
        # ほぼ対称な配置
        distances = {
            'sensor1': 500.0,
            'sensor2': 400.1,  # わずかな差
            'sensor3': 800.0,
            'sensor4': 400.0,
            'sensor5': 500.0
        }
        decision = controller.calculate_steering(distances, sensor_angles)

        # 0.1度未満なら straight 扱い
        if abs(decision.angle) < 0.1:
            assert decision.direction == "straight"

    # ========== 異常値テスト ==========

    def test_negative_intersection_ignored(self, controller, sensor_angles):
        """異常値: 負の交点（後方）は無視される"""
        # センサーの配置で交点が負になる場合
        # このケースは実装により処理が異なるが、エラーにならないこと
        distances = {
            'sensor1': 100.0,
            'sensor2': 200.0,  # 距離が増加（壁が後方に発散）
            'sensor3': 800.0,
            'sensor4': 400.0,
            'sensor5': 500.0
        }
        decision = controller.calculate_steering(distances, sensor_angles)
        # エラーにならず、何らかの判断が返される
        assert decision.angle is not None
        assert decision.direction in ["left", "right", "straight"]

    def test_vertical_line_handling(self, controller, sensor_angles):
        """異常値: 垂直線（傾きが無限大）のケース"""
        # センサー1と2のx座標がほぼ同じになる配置
        # sensor1: -70度, sensor2: -20度
        # 同じ距離なら垂直線になる可能性がある
        distances = {
            'sensor1': 500.0,
            'sensor2': 500.0,  # 同じ距離
            'sensor3': 800.0,
            'sensor4': 500.0,
            'sensor5': 500.0
        }
        decision = controller.calculate_steering(distances, sensor_angles)
        # 垂直線の場合、line is None となり適切に処理される
        assert decision.angle is not None

    def test_zero_distance_sensor(self, controller, sensor_angles):
        """異常値: 距離が0のセンサー"""
        distances = {
            'sensor1': 0.0,  # 異常値
            'sensor2': 400.0,
            'sensor3': 800.0,
            'sensor4': 400.0,
            'sensor5': 500.0
        }
        decision = controller.calculate_steering(distances, sensor_angles)
        # 0距離でも計算は実行される（原点の点として扱われる）
        assert decision.angle is not None

    def test_extremely_large_distance(self, controller, sensor_angles):
        """異常値: 非常に大きな距離"""
        distances = {
            'sensor1': 10000.0,
            'sensor2': 10000.0,
            'sensor3': 10000.0,
            'sensor4': 10000.0,
            'sensor5': 10000.0
        }
        decision = controller.calculate_steering(distances, sensor_angles)
        # 大きな距離でも計算は実行される
        assert decision.angle is not None

    def test_mixed_very_close_and_very_far(self, controller, sensor_angles):
        """異常値: 非常に近い壁と非常に遠い壁が混在"""
        distances = {
            'sensor1': 50.0,    # 非常に近い
            'sensor2': 60.0,
            'sensor3': 800.0,
            'sensor4': 5000.0,  # 非常に遠い
            'sensor5': 6000.0
        }
        decision = controller.calculate_steering(distances, sensor_angles)
        # 極端な値でも処理される
        assert decision.angle is not None
        assert abs(decision.angle) <= MAX_STEER_ANGLE

    # ========== データクラステスト ==========

    def test_steering_decision_dataclass(self):
        """正常値: SteeringDecision データクラスの作成"""
        decision = SteeringDecision(
            angle=15.5,
            direction="right",
            left_intersection=500.0,
            right_intersection=450.0,
            reason="Test reason"
        )
        assert decision.angle == 15.5
        assert decision.direction == "right"
        assert decision.left_intersection == 500.0
        assert decision.right_intersection == 450.0
        assert decision.reason == "Test reason"

    def test_steering_decision_with_none_intersections(self):
        """境界値: 交点がNoneのSteeringDecision"""
        decision = SteeringDecision(
            angle=0.0,
            direction="straight",
            left_intersection=None,
            right_intersection=None,
            reason="No walls"
        )
        assert decision.left_intersection is None
        assert decision.right_intersection is None

    # ========== デバッグ出力テスト ==========

    @patch('builtins.print')
    def test_debug_output_enabled(self, mock_print, sensor_angles):
        """正常値: デバッグ出力が有効な場合"""
        controller = SteeringController(debug=True)
        distances = {
            'sensor1': 500.0,
            'sensor2': 400.0,
            'sensor3': 800.0,
            'sensor4': 400.0,
            'sensor5': 500.0
        }
        controller.calculate_steering(distances, sensor_angles)

        # デバッグ出力が呼ばれていることを確認
        assert mock_print.call_count > 0

    def test_debug_output_disabled(self, controller, sensor_angles):
        """正常値: デバッグ出力が無効な場合"""
        distances = {
            'sensor1': 500.0,
            'sensor2': 400.0,
            'sensor3': 800.0,
            'sensor4': 400.0,
            'sensor5': 500.0
        }
        # デバッグ無効なので出力なし（エラーにならないこと）
        decision = controller.calculate_steering(distances, sensor_angles)
        assert decision is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
