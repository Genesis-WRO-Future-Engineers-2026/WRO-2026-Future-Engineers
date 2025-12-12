"""actuators.py のテスト - Actuator クラスの単体テスト（GPIOモック）"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call


class TestActuator:
    """Actuator クラスのテスト"""

    @pytest.fixture
    def mock_gpio(self):
        """GPIO モック"""
        with patch('actuators.GPIO') as mock:
            mock.LOW = 0
            mock.HIGH = 1
            mock.BCM = 11
            mock.OUT = 1

            # PWMオブジェクトのモック
            mock_pwm = MagicMock()
            mock.PWM.return_value = mock_pwm

            yield mock

    @pytest.fixture
    def mock_time(self):
        """time.sleep モック"""
        with patch('actuators.time.sleep') as mock:
            yield mock

    # ========== 正常値テスト ==========

    def test_actuator_initialization(self, mock_gpio, mock_time):
        """正常値: Actuator の初期化"""
        from actuators import Actuator
        from config import SERVO_PIN, ESC_PIN, PWM_FREQUENCY

        actuator = Actuator()

        # GPIOセットアップが呼ばれている
        assert mock_gpio.setmode.called
        assert mock_gpio.setup.call_count >= 7  # 5センサー + サーボ + ESC

        # PWMが初期化されている
        assert mock_gpio.PWM.call_count == 2  # サーボとESC
        mock_gpio.PWM.assert_any_call(SERVO_PIN, PWM_FREQUENCY)
        mock_gpio.PWM.assert_any_call(ESC_PIN, PWM_FREQUENCY)

        # PWMがスタートされている
        assert actuator.servo_pwm.start.called
        assert actuator.esc_pwm.start.called

    def test_set_steering_angle_center(self, mock_gpio, mock_time):
        """正常値: ステアリング角度を中央（0度）に設定"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.set_steering_angle(0.0)

        # デューティサイクルが設定されている
        assert actuator.servo_pwm.ChangeDutyCycle.called

        # 0度の場合、中間のパルス幅になる
        call_args = actuator.servo_pwm.ChangeDutyCycle.call_args_list[-1]
        duty_cycle = call_args[0][0]

        # パルス幅1.45ms（中間）→ デューティサイクル7.25%
        expected_pulse_width = 1.45  # (0.5 + 2.4) / 2
        expected_duty = (expected_pulse_width / 20.0) * 100
        assert abs(duty_cycle - expected_duty) < 0.5

    def test_set_steering_angle_right(self, mock_gpio, mock_time):
        """正常値: ステアリング角度を右（+90度）に設定"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.set_steering_angle(90.0)

        call_args = actuator.servo_pwm.ChangeDutyCycle.call_args_list[-1]
        duty_cycle = call_args[0][0]

        # +90度の場合、最大パルス幅（2.4ms）
        expected_duty = (2.4 / 20.0) * 100
        assert abs(duty_cycle - expected_duty) < 0.1

    def test_set_steering_angle_left(self, mock_gpio, mock_time):
        """正常値: ステアリング角度を左（-90度）に設定"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.set_steering_angle(-90.0)

        call_args = actuator.servo_pwm.ChangeDutyCycle.call_args_list[-1]
        duty_cycle = call_args[0][0]

        # -90度の場合、最小パルス幅（0.5ms）
        expected_duty = (0.5 / 20.0) * 100
        assert abs(duty_cycle - expected_duty) < 0.1

    def test_set_steering_angle_small_positive(self, mock_gpio, mock_time):
        """正常値: 小さい正の角度（+15度）"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.set_steering_angle(15.0)

        call_args = actuator.servo_pwm.ChangeDutyCycle.call_args_list[-1]
        duty_cycle = call_args[0][0]

        # 15度のパルス幅を計算
        pulse_width_ms = ((15.0 + 90) / 180) * (2.4 - 0.5) + 0.5
        expected_duty = (pulse_width_ms / 20.0) * 100
        assert abs(duty_cycle - expected_duty) < 0.1

    def test_set_speed_stop(self, mock_gpio, mock_time):
        """正常値: モーター停止"""
        from actuators import Actuator
        from config import STOP_PULSE

        actuator = Actuator()
        actuator.set_speed(STOP_PULSE)

        call_args = actuator.esc_pwm.ChangeDutyCycle.call_args_list[-1]
        duty_cycle = call_args[0][0]

        expected_duty = (STOP_PULSE / 20.0) * 100
        assert abs(duty_cycle - expected_duty) < 0.1

    def test_set_speed_forward(self, mock_gpio, mock_time):
        """正常値: 前進速度設定"""
        from actuators import Actuator
        from config import SPEED_PULSE

        actuator = Actuator()
        actuator.set_speed(SPEED_PULSE)

        call_args = actuator.esc_pwm.ChangeDutyCycle.call_args_list[-1]
        duty_cycle = call_args[0][0]

        expected_duty = (SPEED_PULSE / 20.0) * 100
        assert abs(duty_cycle - expected_duty) < 0.1

    def test_stop_method(self, mock_gpio, mock_time):
        """正常値: stop() メソッド"""
        from actuators import Actuator
        from config import NEUTRAL_ANGLE, STOP_PULSE

        actuator = Actuator()
        actuator.stop()

        # ニュートラル角度とストップパルスが設定される
        # ChangeDutyCycleが呼ばれたことを確認（初期化 + stop呼び出し）
        assert actuator.servo_pwm.ChangeDutyCycle.call_count >= 2
        assert actuator.esc_pwm.ChangeDutyCycle.call_count >= 2

    def test_cleanup(self, mock_gpio, mock_time):
        """正常値: cleanup() メソッド"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.cleanup()

        # stop()が呼ばれる（ChangeDutyCycleが呼ばれる）
        assert actuator.servo_pwm.ChangeDutyCycle.call_count >= 2
        assert actuator.esc_pwm.ChangeDutyCycle.call_count >= 2

        # PWMが停止される
        assert actuator.servo_pwm.stop.called
        assert actuator.esc_pwm.stop.called

        # sleepが呼ばれる
        assert mock_time.call_count > 0

    # ========== 境界値テスト ==========

    def test_set_steering_angle_max_positive(self, mock_gpio, mock_time):
        """境界値: 最大正ステアリング角度"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.set_steering_angle(90.0)  # 最大

        # エラーにならずに設定される
        assert actuator.servo_pwm.ChangeDutyCycle.called

    def test_set_steering_angle_max_negative(self, mock_gpio, mock_time):
        """境界値: 最大負ステアリング角度"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.set_steering_angle(-90.0)  # 最小

        # エラーにならずに設定される
        assert actuator.servo_pwm.ChangeDutyCycle.called

    def test_set_steering_angle_zero(self, mock_gpio, mock_time):
        """境界値: ステアリング角度0度"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.set_steering_angle(0.0)

        call_args = actuator.servo_pwm.ChangeDutyCycle.call_args_list[-1]
        duty_cycle = call_args[0][0]

        # 0度は中央
        pulse_width_ms = 1.45  # (0.5 + 2.4) / 2
        expected_duty = (pulse_width_ms / 20.0) * 100
        assert abs(duty_cycle - expected_duty) < 0.5

    def test_set_speed_min_pulse(self, mock_gpio, mock_time):
        """境界値: 最小パルス幅"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.set_speed(0.5)  # サーボの最小パルス幅と同じ

        # エラーにならずに設定される
        assert actuator.esc_pwm.ChangeDutyCycle.called

    def test_set_speed_max_pulse(self, mock_gpio, mock_time):
        """境界値: 最大パルス幅"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.set_speed(2.4)  # サーボの最大パルス幅と同じ

        # エラーにならずに設定される
        assert actuator.esc_pwm.ChangeDutyCycle.called

    # ========== 異常値テスト ==========

    def test_set_steering_angle_over_max(self, mock_gpio, mock_time):
        """異常値: 最大角度を超える（+120度）"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.set_steering_angle(120.0)

        # エラーにならずに設定される（範囲外だがサーボが物理的に制限する）
        assert actuator.servo_pwm.ChangeDutyCycle.called

        call_args = actuator.servo_pwm.ChangeDutyCycle.call_args_list[-1]
        duty_cycle = call_args[0][0]

        # パルス幅が最大値を超える
        pulse_width_ms = ((120.0 + 90) / 180) * (2.4 - 0.5) + 0.5
        expected_duty = (pulse_width_ms / 20.0) * 100
        assert duty_cycle > 0  # 何らかの値が設定される

    def test_set_steering_angle_under_min(self, mock_gpio, mock_time):
        """異常値: 最小角度を下回る（-120度）"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.set_steering_angle(-120.0)

        # エラーにならずに設定される
        assert actuator.servo_pwm.ChangeDutyCycle.called

    def test_set_speed_zero(self, mock_gpio, mock_time):
        """異常値: 速度0（パルス幅0ms）"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.set_speed(0.0)

        # エラーにならずに設定される
        assert actuator.esc_pwm.ChangeDutyCycle.called

        call_args = actuator.esc_pwm.ChangeDutyCycle.call_args_list[-1]
        duty_cycle = call_args[0][0]
        assert duty_cycle == 0.0

    def test_set_speed_negative(self, mock_gpio, mock_time):
        """異常値: 負のパルス幅"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.set_speed(-1.0)

        # エラーにならずに設定される（負のデューティサイクル）
        assert actuator.esc_pwm.ChangeDutyCycle.called

    def test_set_speed_very_large(self, mock_gpio, mock_time):
        """異常値: 非常に大きなパルス幅（100ms）"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.set_speed(100.0)

        # エラーにならずに設定される
        assert actuator.esc_pwm.ChangeDutyCycle.called

        call_args = actuator.esc_pwm.ChangeDutyCycle.call_args_list[-1]
        duty_cycle = call_args[0][0]

        # デューティサイクルが100%を超える（物理的には無意味）
        expected_duty = (100.0 / 20.0) * 100
        assert duty_cycle == expected_duty

    def test_set_steering_angle_fractional(self, mock_gpio, mock_time):
        """境界値: 小数点以下の角度（15.5度）"""
        from actuators import Actuator

        actuator = Actuator()
        actuator.set_steering_angle(15.5)

        # 小数点以下も正しく計算される
        assert actuator.servo_pwm.ChangeDutyCycle.called

        call_args = actuator.servo_pwm.ChangeDutyCycle.call_args_list[-1]
        duty_cycle = call_args[0][0]

        pulse_width_ms = ((15.5 + 90) / 180) * (2.4 - 0.5) + 0.5
        expected_duty = (pulse_width_ms / 20.0) * 100
        assert abs(duty_cycle - expected_duty) < 0.1

    # ========== PWM周波数テスト ==========

    def test_pwm_frequency_50hz(self, mock_gpio, mock_time):
        """正常値: PWM周波数が50Hzで設定される"""
        from actuators import Actuator
        from config import PWM_FREQUENCY

        actuator = Actuator()

        # PWMが50Hzで初期化されている
        calls = mock_gpio.PWM.call_args_list
        for call_args in calls:
            assert call_args[0][1] == PWM_FREQUENCY
            assert call_args[0][1] == 50

    # ========== GPIO設定テスト ==========

    def test_gpio_mode_bcm(self, mock_gpio, mock_time):
        """正常値: GPIOモードがBCMに設定される"""
        from actuators import Actuator

        actuator = Actuator()

        mock_gpio.setmode.assert_called_with(mock_gpio.BCM)

    def test_gpio_warnings_disabled(self, mock_gpio, mock_time):
        """正常値: GPIO警告が無効化される"""
        from actuators import Actuator

        actuator = Actuator()

        mock_gpio.setwarnings.assert_called_with(False)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
