"""実機モーター制御インターフェース

実機のステアリングとスロットルを制御するための抽象化層。
シミュレーターと実機で同じコードを使えるようにする。
"""

from abc import ABC, abstractmethod
import numpy as np
from typing import Tuple


class MotorInterface(ABC):
    """モーター制御の抽象インターフェース"""

    @abstractmethod
    def set_control(self, steering: float, throttle: float):
        """ステアリングとスロットルを設定

        Args:
            steering: ステアリング角度 [-1.0, 1.0] (左/右)
            throttle: スロットル [-1.0, 1.0] (後退/前進)
        """
        pass

    @abstractmethod
    def stop(self):
        """モーターを停止（緊急停止）"""
        pass

    @abstractmethod
    def reset(self):
        """モーターをニュートラル状態にリセット"""
        pass


class RaspberryPiMotorInterface(MotorInterface):
    """Raspberry Pi実機用のモーター制御インターフェース

    実装例:
    - ステアリングサーボ: PWM制御（GPIO経由）
    - 駆動モーター: ESC（Electronic Speed Controller）経由でPWM制御
    """

    def __init__(
        self,
        steering_pin: int = 17,
        throttle_pin: int = 18,
        steering_range: Tuple[float, float] = (1000, 2000),  # PWMパルス幅（μs）
        throttle_range: Tuple[float, float] = (1000, 2000),
    ):
        """
        Args:
            steering_pin: ステアリングサーボのGPIOピン番号
            throttle_pin: スロットルESCのGPIOピン番号
            steering_range: ステアリングのPWMパルス幅範囲（μs）
            throttle_range: スロットルのPWMパルス幅範囲（μs）
        """
        self.steering_pin = steering_pin
        self.throttle_pin = throttle_pin
        self.steering_range = steering_range
        self.throttle_range = throttle_range

        # TODO: 実機ハードウェアの初期化
        # import RPi.GPIO as GPIO
        # GPIO.setmode(GPIO.BCM)
        # self.steering_servo = GPIO.PWM(steering_pin, 50)  # 50Hz
        # self.throttle_esc = GPIO.PWM(throttle_pin, 50)
        # self.steering_servo.start(0)
        # self.throttle_esc.start(0)

        print(f"[RaspberryPiMotorInterface] 初期化完了")
        print(f"  Steering Pin: GPIO{steering_pin}")
        print(f"  Throttle Pin: GPIO{throttle_pin}")

    def set_control(self, steering: float, throttle: float):
        """ステアリングとスロットルを設定

        Args:
            steering: ステアリング角度 [-1.0, 1.0]
                     -1.0 = 最大左、0.0 = 直進、+1.0 = 最大右
            throttle: スロットル [-1.0, 1.0]
                     -1.0 = 最大後退、0.0 = 停止、+1.0 = 最大前進
        """
        # 入力値を [-1.0, 1.0] にクリップ
        steering = np.clip(steering, -1.0, 1.0)
        throttle = np.clip(throttle, -1.0, 1.0)

        # [-1.0, 1.0] → PWMパルス幅（μs）に変換
        steering_pulse = self._map_to_pwm(steering, self.steering_range)
        throttle_pulse = self._map_to_pwm(throttle, self.throttle_range)

        # TODO: 実機モーターに指令送信
        # self._set_pwm(self.steering_servo, steering_pulse)
        # self._set_pwm(self.throttle_esc, throttle_pulse)

        # デバッグ出力
        # print(f"[Motor] Steering: {steering:.2f} ({steering_pulse:.0f}μs), "
        #       f"Throttle: {throttle:.2f} ({throttle_pulse:.0f}μs)")

    def stop(self):
        """モーターを停止（緊急停止）"""
        print("[RaspberryPiMotorInterface] 緊急停止")
        self.set_control(steering=0.0, throttle=0.0)

    def reset(self):
        """モーターをニュートラル状態にリセット"""
        print("[RaspberryPiMotorInterface] リセット")
        self.set_control(steering=0.0, throttle=0.0)

    def close(self):
        """モーター制御をクリーンアップ"""
        self.stop()
        # TODO: GPIOのクリーンアップ
        # self.steering_servo.stop()
        # self.throttle_esc.stop()
        # GPIO.cleanup()
        print("[RaspberryPiMotorInterface] クリーンアップ完了")

    def _map_to_pwm(
        self, value: float, pwm_range: Tuple[float, float]
    ) -> float:
        """[-1.0, 1.0] をPWMパルス幅（μs）にマッピング

        Args:
            value: 入力値 [-1.0, 1.0]
            pwm_range: PWMパルス幅の範囲（μs）

        Returns:
            PWMパルス幅（μs）
        """
        min_pulse, max_pulse = pwm_range
        # [-1.0, 1.0] → [min_pulse, max_pulse]
        pulse = min_pulse + (value + 1.0) / 2.0 * (max_pulse - min_pulse)
        return pulse

    def _set_pwm(self, pwm_channel, pulse_width_us: float):
        """PWMチャンネルにパルス幅を設定

        Args:
            pwm_channel: PWMチャンネル
            pulse_width_us: パルス幅（μs）
        """
        # 50Hz PWM (20ms周期) でのデューティサイクル計算
        # duty_cycle = (pulse_width_us / 20000) * 100
        # pwm_channel.ChangeDutyCycle(duty_cycle)
        pass


class MockMotorInterface(MotorInterface):
    """テスト用のモックモーターインターフェース

    実機がない環境でのテスト・デバッグ用。
    制御コマンドをログ出力するのみ。
    """

    def __init__(self):
        print("[MockMotorInterface] 初期化完了（テストモード）")
        self.last_steering = 0.0
        self.last_throttle = 0.0

    def set_control(self, steering: float, throttle: float):
        """制御コマンドをログ出力"""
        self.last_steering = steering
        self.last_throttle = throttle
        # デバッグ用に出力（実機では無効化）
        # print(f"[MockMotor] Steering: {steering:+.2f}, Throttle: {throttle:+.2f}")

    def stop(self):
        """停止をログ出力"""
        print("[MockMotor] 停止")
        self.set_control(0.0, 0.0)

    def reset(self):
        """リセットをログ出力"""
        print("[MockMotor] リセット")
        self.set_control(0.0, 0.0)

    def close(self):
        """何もしない"""
        pass
