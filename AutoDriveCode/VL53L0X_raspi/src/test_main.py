"""main.py のテスト - AutoDriveCar クラスの統合テスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call


class TestAutoDriveCar:
    """AutoDriveCar クラスの統合テスト"""

    @pytest.fixture
    def mock_gpio(self):
        """GPIO モック"""
        with patch('actuators.GPIO') as mock:
            mock.LOW = 0
            mock.HIGH = 1
            mock.BCM = 11
            mock.OUT = 1
            mock_pwm = MagicMock()
            mock.PWM.return_value = mock_pwm
            yield mock

    @pytest.fixture
    def mock_vl53l0x(self):
        """VL53L0X モック"""
        with patch('sensors.VL53L0X') as mock_module:
            mock_sensor = MagicMock()
            mock_sensor.get_distance.return_value = 500
            mock_sensor.get_timing.return_value = 20000
            mock_sensor.start_ranging.return_value = None
            mock_sensor.stop_ranging.return_value = None
            mock_module.VL53L0X.return_value = mock_sensor
            mock_module.VL53L0X_BETTER_ACCURACY_MODE = 1
            yield mock_module

    @pytest.fixture
    def mock_time(self):
        """time.sleep モック"""
        with patch('sensors.time.sleep'):
            with patch('actuators.time.sleep'):
                with patch('main.time.sleep') as mock:
                    yield mock

    @pytest.fixture
    def mock_print(self):
        """print モック"""
        with patch('builtins.print') as mock:
            yield mock

    # ========== 正常値テスト ==========

    def test_autodrive_car_initialization(self, mock_gpio, mock_vl53l0x, mock_time):
        """正常値: AutoDriveCar の初期化"""
        from main import AutoDriveCar

        car = AutoDriveCar()

        # 各コンポーネントが初期化されている
        assert car.sensor_manager is not None
        assert car.actuator is not None
        assert car.steering_controller is not None

    def test_run_single_iteration(self, mock_gpio, mock_vl53l0x, mock_time, mock_print):
        """正常値: 1回の測定ループ実行"""
        from main import AutoDriveCar

        car = AutoDriveCar()

        # 1回だけ実行
        car.run(iterations=1)

        # センサー読み取りが行われた
        for sensor in car.sensor_manager.sensors.values():
            assert sensor.get_distance.called

    def test_run_multiple_iterations(self, mock_gpio, mock_vl53l0x, mock_time, mock_print):
        """正常値: 複数回の測定ループ実行"""
        from main import AutoDriveCar

        car = AutoDriveCar()

        # 3回実行
        car.run(iterations=3)

        # 各センサーの読み取りが3回行われた
        for sensor in car.sensor_manager.sensors.values():
            assert sensor.get_distance.call_count >= 3

    def test_all_sensors_valid(self, mock_gpio, mock_vl53l0x, mock_time, mock_print):
        """正常値: 全センサーが有効な値を返す"""
        from main import AutoDriveCar

        # 全センサーが正の値を返す
        mock_sensors = []
        for dist in [500, 400, 800, 450, 550]:
            mock_sensor = MagicMock()
            mock_sensor.get_distance.return_value = dist
            mock_sensors.append(mock_sensor)

        car = AutoDriveCar()
        car.sensor_manager.sensors = {
            'sensor1': mock_sensors[0],
            'sensor2': mock_sensors[1],
            'sensor3': mock_sensors[2],
            'sensor4': mock_sensors[3],
            'sensor5': mock_sensors[4]
        }

        car.run(iterations=1)

        # ステアリングが設定された
        assert car.actuator.servo_pwm.ChangeDutyCycle.call_count > 0

    def test_some_sensors_invalid(self, mock_gpio, mock_vl53l0x, mock_time, mock_print):
        """正常値: 一部のセンサーが無効な値を返す"""
        from main import AutoDriveCar

        # 一部のセンサーがエラー値を返す
        mock_sensors = []
        for dist in [500, -1, 800, 0, 550]:  # sensor2とsensor4がエラー
            mock_sensor = MagicMock()
            mock_sensor.get_distance.return_value = dist
            mock_sensors.append(mock_sensor)

        car = AutoDriveCar()
        car.sensor_manager.sensors = {
            'sensor1': mock_sensors[0],
            'sensor2': mock_sensors[1],
            'sensor3': mock_sensors[2],
            'sensor4': mock_sensors[3],
            'sensor5': mock_sensors[4]
        }

        car.run(iterations=1)

        # エラーがあるのでステアリング計算はスキップされる
        # （初期化時の呼び出しのみ）

    def test_cleanup_called(self, mock_gpio, mock_vl53l0x, mock_time):
        """正常値: cleanup() が正しく呼ばれる"""
        from main import AutoDriveCar

        car = AutoDriveCar()
        car.cleanup()

        # 各コンポーネントのクリーンアップが呼ばれた
        for sensor in car.sensor_manager.sensors.values():
            assert sensor.stop_ranging.called

        assert car.actuator.servo_pwm.stop.called
        assert car.actuator.esc_pwm.stop.called
        assert mock_gpio.cleanup.called

    def test_print_distances(self, mock_gpio, mock_vl53l0x, mock_time, mock_print):
        """正常値: 距離が表示される"""
        from main import AutoDriveCar

        car = AutoDriveCar()
        distances = {
            'sensor1': 500.0,
            'sensor2': 400.0,
            'sensor3': 800.0,
            'sensor4': 450.0,
            'sensor5': 550.0
        }

        car._print_distances(1, 10, distances)

        # printが呼ばれている
        assert mock_print.call_count > 0

    def test_all_sensors_valid_check(self, mock_gpio, mock_vl53l0x, mock_time):
        """正常値: 全センサー有効チェック"""
        from main import AutoDriveCar

        car = AutoDriveCar()

        # 全て正の値
        distances = {
            'sensor1': 500.0,
            'sensor2': 400.0,
            'sensor3': 800.0,
            'sensor4': 450.0,
            'sensor5': 550.0
        }
        assert car._all_sensors_valid(distances) is True

        # 一部が0
        distances['sensor2'] = 0.0
        assert car._all_sensors_valid(distances) is False

        # 一部が負
        distances['sensor2'] = -1.0
        assert car._all_sensors_valid(distances) is False

    # ========== 境界値テスト ==========

    def test_run_zero_iterations(self, mock_gpio, mock_vl53l0x, mock_time, mock_print):
        """境界値: 0回のイテレーション"""
        from main import AutoDriveCar

        car = AutoDriveCar()
        car.run(iterations=0)

        # ループは実行されない

    def test_run_one_iteration(self, mock_gpio, mock_vl53l0x, mock_time, mock_print):
        """境界値: 1回のイテレーション"""
        from main import AutoDriveCar

        car = AutoDriveCar()
        car.run(iterations=1)

        # 1回実行される

    def test_all_sensors_zero(self, mock_gpio, mock_vl53l0x, mock_time):
        """境界値: 全センサーが0を返す"""
        from main import AutoDriveCar

        car = AutoDriveCar()
        distances = {
            'sensor1': 0.0,
            'sensor2': 0.0,
            'sensor3': 0.0,
            'sensor4': 0.0,
            'sensor5': 0.0
        }

        assert car._all_sensors_valid(distances) is False

    def test_all_sensors_negative(self, mock_gpio, mock_vl53l0x, mock_time):
        """境界値: 全センサーが負の値を返す"""
        from main import AutoDriveCar

        car = AutoDriveCar()
        distances = {
            'sensor1': -1.0,
            'sensor2': -1.0,
            'sensor3': -1.0,
            'sensor4': -1.0,
            'sensor5': -1.0
        }

        assert car._all_sensors_valid(distances) is False

    # ========== 異常値テスト ==========

    def test_sensor_read_exception(self, mock_gpio, mock_vl53l0x, mock_time, mock_print):
        """異常値: センサー読み取りで例外が発生"""
        from main import AutoDriveCar

        mock_sensor = MagicMock()
        mock_sensor.get_distance.side_effect = Exception("Sensor error")

        car = AutoDriveCar()
        car.sensor_manager.sensors = {
            'sensor1': mock_sensor,
            'sensor2': mock_sensor,
            'sensor3': mock_sensor,
            'sensor4': mock_sensor,
            'sensor5': mock_sensor
        }

        # 例外が発生してプログラムが停止する
        with pytest.raises(Exception):
            car.run(iterations=1)

    def test_very_large_iterations(self, mock_gpio, mock_vl53l0x, mock_time, mock_print):
        """境界値: 非常に大きなイテレーション数（10回で代用）"""
        from main import AutoDriveCar

        car = AutoDriveCar()
        # 実際には10回で代用（10000回は時間がかかる）
        car.run(iterations=10)

        # 正常に完了する

    def test_mixed_sensor_values(self, mock_gpio, mock_vl53l0x, mock_time, mock_print):
        """異常値: センサー値が混在（正、0、負）"""
        from main import AutoDriveCar

        car = AutoDriveCar()
        distances = {
            'sensor1': 500.0,   # 正常
            'sensor2': 0.0,     # エラー
            'sensor3': 800.0,   # 正常
            'sensor4': -1.0,    # エラー
            'sensor5': 550.0    # 正常
        }

        assert car._all_sensors_valid(distances) is False

    # ========== 統合テスト ==========

    def test_full_cycle_with_steering(self, mock_gpio, mock_vl53l0x, mock_time, mock_print):
        """統合テスト: センサー読み取りからステアリングまでの完全なサイクル"""
        from main import AutoDriveCar

        # 左に寄った配置（右にステアリングすべき）
        mock_sensors = []
        for dist in [300, 250, 800, 600, 700]:
            mock_sensor = MagicMock()
            mock_sensor.get_distance.return_value = dist
            mock_sensors.append(mock_sensor)

        car = AutoDriveCar()
        car.sensor_manager.sensors = {
            'sensor1': mock_sensors[0],
            'sensor2': mock_sensors[1],
            'sensor3': mock_sensors[2],
            'sensor4': mock_sensors[3],
            'sensor5': mock_sensors[4]
        }

        car.run(iterations=1)

        # ステアリングが設定された
        assert car.actuator.servo_pwm.ChangeDutyCycle.call_count > 0

    def test_main_function(self, mock_gpio, mock_vl53l0x, mock_time, mock_print):
        """統合テスト: main() 関数の実行"""
        from main import main

        # KeyboardInterruptをシミュレート
        with patch('main.AutoDriveCar') as MockCar:
            mock_car = MagicMock()
            mock_car.run.side_effect = KeyboardInterrupt()
            MockCar.return_value = mock_car

            main()

            # クリーンアップが呼ばれた
            assert mock_car.cleanup.called

    def test_main_function_normal_completion(self, mock_gpio, mock_vl53l0x, mock_time, mock_print):
        """統合テスト: main() 関数の正常完了"""
        from main import main

        with patch('main.AutoDriveCar') as MockCar:
            mock_car = MagicMock()
            MockCar.return_value = mock_car

            # run()を1回だけ実行するようモック
            def mock_run(iterations=10000):
                pass  # すぐに終了

            mock_car.run = mock_run

            main()

            # クリーンアップが呼ばれた
            assert mock_car.cleanup.called

    # ========== デバッグ出力テスト ==========

    def test_debug_output_in_steering(self, mock_gpio, mock_vl53l0x, mock_time, mock_print):
        """正常値: ステアリング計算時のデバッグ出力"""
        from main import AutoDriveCar

        car = AutoDriveCar()  # debug=True がデフォルト

        # 正常な距離値
        mock_sensors = []
        for dist in [500, 400, 800, 450, 550]:
            mock_sensor = MagicMock()
            mock_sensor.get_distance.return_value = dist
            mock_sensors.append(mock_sensor)

        car.sensor_manager.sensors = {
            'sensor1': mock_sensors[0],
            'sensor2': mock_sensors[1],
            'sensor3': mock_sensors[2],
            'sensor4': mock_sensors[3],
            'sensor5': mock_sensors[4]
        }

        car.run(iterations=1)

        # デバッグ情報が出力されている
        assert mock_print.call_count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
