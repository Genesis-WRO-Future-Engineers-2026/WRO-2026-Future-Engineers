"""sensors.py のテスト - SensorManager クラスの単体テスト（GPIO/VL53L0Xモック）"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import sys


class TestSensorManager:
    """SensorManager クラスのテスト"""

    @pytest.fixture
    def mock_gpio(self):
        """GPIO モック"""
        with patch('sensors.GPIO') as mock:
            mock.LOW = 0
            mock.HIGH = 1
            mock.BCM = 11
            mock.OUT = 1
            yield mock

    @pytest.fixture
    def mock_vl53l0x(self):
        """VL53L0X モック"""
        with patch('sensors.VL53L0X') as mock_module:
            # VL53L0X クラスのモック
            mock_sensor = MagicMock()
            mock_sensor.get_distance.return_value = 500
            mock_sensor.get_timing.return_value = 20000
            mock_sensor.start_ranging.return_value = None
            mock_sensor.stop_ranging.return_value = None

            # VL53L0X コンストラクタのモック
            mock_module.VL53L0X.return_value = mock_sensor
            mock_module.VL53L0X_BETTER_ACCURACY_MODE = 1

            yield mock_module

    @pytest.fixture
    def mock_time(self):
        """time.sleep モック"""
        with patch('sensors.time.sleep') as mock:
            yield mock

    # ========== 正常値テスト ==========

    def test_sensor_manager_initialization(self, mock_gpio, mock_vl53l0x, mock_time):
        """正常値: SensorManager の初期化"""
        from sensors import SensorManager

        manager = SensorManager()

        # 5つのセンサーが初期化されている
        assert len(manager.sensors) == 5
        assert 'sensor1' in manager.sensors
        assert 'sensor2' in manager.sensors
        assert 'sensor3' in manager.sensors
        assert 'sensor4' in manager.sensors
        assert 'sensor5' in manager.sensors

        # 角度設定が正しい
        assert manager.angles['sensor1'] == -70
        assert manager.angles['sensor2'] == -20
        assert manager.angles['sensor3'] == 0
        assert manager.angles['sensor4'] == 20
        assert manager.angles['sensor5'] == 70

    def test_gpio_shutdown_sequence(self, mock_gpio, mock_vl53l0x, mock_time):
        """正常値: GPIO シャットダウンシーケンス"""
        from sensors import SensorManager

        manager = SensorManager()

        # 全センサーが一度LOWに設定される（初期化時）
        assert mock_gpio.output.call_count >= 10  # 5センサー×2回以上

    def test_sensor_address_assignment(self, mock_gpio, mock_vl53l0x, mock_time):
        """正常値: I2Cアドレスの割り当て"""
        from sensors import SensorManager
        from config import (
            SENSOR1_ADDRESS, SENSOR2_ADDRESS, SENSOR3_ADDRESS,
            SENSOR4_ADDRESS, SENSOR5_ADDRESS
        )

        manager = SensorManager()

        # VL53L0Xが正しいアドレスで初期化されている
        calls = mock_vl53l0x.VL53L0X.call_args_list

        # 各センサーは2回作成される（0x29で起動 → アドレス変更後に再作成）
        assert len(calls) >= 10  # 5センサー×2回

        # デフォルトアドレス(0x29)と各センサーのアドレスが含まれる
        addresses = [call.kwargs.get('address') for call in calls if 'address' in call.kwargs]
        assert 0x29 in addresses
        assert SENSOR1_ADDRESS in addresses
        assert SENSOR2_ADDRESS in addresses
        assert SENSOR3_ADDRESS in addresses
        assert SENSOR4_ADDRESS in addresses
        assert SENSOR5_ADDRESS in addresses

    def test_read_all_distances_normal(self, mock_gpio, mock_vl53l0x, mock_time):
        """正常値: 全センサーの距離読み取り"""
        from sensors import SensorManager

        # 各センサーで異なる距離を返すようモック設定
        distances_mock = [500, 400, 800, 450, 550]
        mock_sensors = []
        for dist in distances_mock:
            mock_sensor = MagicMock()
            mock_sensor.get_distance.return_value = dist
            mock_sensors.append(mock_sensor)

        manager = SensorManager()
        manager.sensors = {
            'sensor1': mock_sensors[0],
            'sensor2': mock_sensors[1],
            'sensor3': mock_sensors[2],
            'sensor4': mock_sensors[3],
            'sensor5': mock_sensors[4]
        }

        distances = manager.read_all_distances()

        assert distances['sensor1'] == 500
        assert distances['sensor2'] == 400
        assert distances['sensor3'] == 800
        assert distances['sensor4'] == 450
        assert distances['sensor5'] == 550

    def test_get_sensor_angles(self, mock_gpio, mock_vl53l0x, mock_time):
        """正常値: センサー角度の取得"""
        from sensors import SensorManager

        manager = SensorManager()
        angles = manager.get_sensor_angles()

        assert angles['sensor1'] == -70
        assert angles['sensor2'] == -20
        assert angles['sensor3'] == 0
        assert angles['sensor4'] == 20
        assert angles['sensor5'] == 70

    def test_get_timing_normal(self, mock_gpio, mock_vl53l0x, mock_time):
        """正常値: タイミング取得（MIN_TIMING以上）"""
        from sensors import SensorManager
        from config import MIN_TIMING

        # タイミングがMIN_TIMING以上の値を返す
        mock_sensor = MagicMock()
        mock_sensor.get_timing.return_value = 30000  # MIN_TIMINGより大きい

        manager = SensorManager()
        manager.sensors['sensor1'] = mock_sensor

        timing = manager.get_timing()

        assert timing == 30000

    def test_cleanup_sensors(self, mock_gpio, mock_vl53l0x, mock_time):
        """正常値: センサーのクリーンアップ"""
        from sensors import SensorManager

        manager = SensorManager()
        manager.cleanup()

        # 全センサーのstop_rangingが呼ばれる
        for sensor in manager.sensors.values():
            sensor.stop_ranging.assert_called_once()

        # 全GPIOピンがLOWに設定される
        low_calls = [
            call_args for call_args in mock_gpio.output.call_args_list
            if call_args[0][1] == mock_gpio.LOW
        ]
        assert len(low_calls) >= 5  # 5つのセンサーシャットダウンピン

    # ========== 境界値テスト ==========

    def test_get_timing_below_min(self, mock_gpio, mock_vl53l0x, mock_time):
        """境界値: タイミングがMIN_TIMING未満の場合"""
        from sensors import SensorManager
        from config import MIN_TIMING

        # タイミングがMIN_TIMING未満の値を返す
        mock_sensor = MagicMock()
        mock_sensor.get_timing.return_value = 10000  # MIN_TIMINGより小さい

        manager = SensorManager()
        manager.sensors['sensor1'] = mock_sensor

        timing = manager.get_timing()

        # MIN_TIMINGが返される
        assert timing == MIN_TIMING

    def test_get_timing_exactly_min(self, mock_gpio, mock_vl53l0x, mock_time):
        """境界値: タイミングがちょうどMIN_TIMING"""
        from sensors import SensorManager
        from config import MIN_TIMING

        mock_sensor = MagicMock()
        mock_sensor.get_timing.return_value = MIN_TIMING

        manager = SensorManager()
        manager.sensors['sensor1'] = mock_sensor

        timing = manager.get_timing()

        assert timing == MIN_TIMING

    def test_read_all_distances_zero(self, mock_gpio, mock_vl53l0x, mock_time):
        """境界値: 距離が0の場合"""
        from sensors import SensorManager

        mock_sensor = MagicMock()
        mock_sensor.get_distance.return_value = 0

        manager = SensorManager()
        for key in manager.sensors:
            manager.sensors[key] = mock_sensor

        distances = manager.read_all_distances()

        # 0が返される（エラー値として扱われる）
        assert all(d == 0 for d in distances.values())

    def test_read_all_distances_max_range(self, mock_gpio, mock_vl53l0x, mock_time):
        """境界値: VL53L0Xの最大測定範囲"""
        from sensors import SensorManager

        mock_sensor = MagicMock()
        mock_sensor.get_distance.return_value = 2000  # VL53L0Xの最大範囲付近

        manager = SensorManager()
        for key in manager.sensors:
            manager.sensors[key] = mock_sensor

        distances = manager.read_all_distances()

        assert all(d == 2000 for d in distances.values())

    # ========== 異常値テスト ==========

    def test_read_all_distances_negative(self, mock_gpio, mock_vl53l0x, mock_time):
        """異常値: 負の距離（エラー）"""
        from sensors import SensorManager

        mock_sensor = MagicMock()
        mock_sensor.get_distance.return_value = -1  # エラー値

        manager = SensorManager()
        for key in manager.sensors:
            manager.sensors[key] = mock_sensor

        distances = manager.read_all_distances()

        # 負の値が返される（main.pyで処理される）
        assert all(d == -1 for d in distances.values())

    def test_sensor_read_error_handling(self, mock_gpio, mock_vl53l0x, mock_time):
        """異常値: センサー読み取りエラー"""
        from sensors import SensorManager

        mock_sensor = MagicMock()
        # 時々エラー値を返すセンサー
        mock_sensor.get_distance.side_effect = [500, -1, 600, 0, 700]

        manager = SensorManager()
        manager.sensors = {
            'sensor1': mock_sensor,
            'sensor2': mock_sensor,
            'sensor3': mock_sensor,
            'sensor4': mock_sensor,
            'sensor5': mock_sensor
        }

        distances = manager.read_all_distances()

        # エラー値も含めて返される
        assert 'sensor1' in distances
        assert 'sensor5' in distances

    def test_get_timing_zero(self, mock_gpio, mock_vl53l0x, mock_time):
        """異常値: タイミングが0"""
        from sensors import SensorManager
        from config import MIN_TIMING

        mock_sensor = MagicMock()
        mock_sensor.get_timing.return_value = 0

        manager = SensorManager()
        manager.sensors['sensor1'] = mock_sensor

        timing = manager.get_timing()

        # MIN_TIMINGが返される
        assert timing == MIN_TIMING

    def test_get_timing_negative(self, mock_gpio, mock_vl53l0x, mock_time):
        """異常値: タイミングが負"""
        from sensors import SensorManager
        from config import MIN_TIMING

        mock_sensor = MagicMock()
        mock_sensor.get_timing.return_value = -1000

        manager = SensorManager()
        manager.sensors['sensor1'] = mock_sensor

        timing = manager.get_timing()

        # MIN_TIMINGが返される
        assert timing == MIN_TIMING

    # ========== 初期化順序テスト ==========

    def test_sensor_initialization_order(self, mock_gpio, mock_vl53l0x, mock_time):
        """正常値: センサー初期化の順序"""
        from sensors import SensorManager
        from config import (
            SENSOR1_SHUTDOWN, SENSOR2_SHUTDOWN, SENSOR3_SHUTDOWN,
            SENSOR4_SHUTDOWN, SENSOR5_SHUTDOWN
        )

        manager = SensorManager()

        # GPIO出力呼び出しを確認
        output_calls = mock_gpio.output.call_args_list

        # 最初に全てがLOWに設定される
        initial_calls = output_calls[:5]
        for call_args in initial_calls:
            assert call_args[0][1] == mock_gpio.LOW

        # その後、各センサーが順にHIGHに設定される
        high_calls = [call_args for call_args in output_calls if call_args[0][1] == mock_gpio.HIGH]
        assert len(high_calls) >= 5

    def test_sleep_called_during_initialization(self, mock_gpio, mock_vl53l0x, mock_time):
        """正常値: 初期化中にsleepが呼ばれる"""
        from sensors import SensorManager

        manager = SensorManager()

        # time.sleepが複数回呼ばれている
        assert mock_time.call_count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
