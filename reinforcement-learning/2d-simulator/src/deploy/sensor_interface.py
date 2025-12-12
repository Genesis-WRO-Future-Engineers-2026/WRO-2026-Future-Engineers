"""実機センサーインターフェース

実機のLiDARセンサーとIMU/エンコーダーからデータを取得するための抽象化層。
シミュレーターと実機で同じコードを使えるようにする。
"""

from abc import ABC, abstractmethod
import numpy as np
from typing import Tuple


class SensorInterface(ABC):
    """センサーの抽象インターフェース"""

    @abstractmethod
    def get_lidar_scan(self) -> np.ndarray:
        """LiDARスキャンデータを取得

        Returns:
            distances: 距離データ (num_rays,) - 単位はメートル
        """
        pass

    @abstractmethod
    def get_velocity(self) -> Tuple[float, float]:
        """車両の速度を取得

        Returns:
            (vx, vy): x方向とy方向の速度 (m/s)
        """
        pass

    @abstractmethod
    def get_angular_velocity(self) -> float:
        """車両の角速度を取得

        Returns:
            angular_velocity: 角速度 (rad/s)
        """
        pass

    @abstractmethod
    def reset(self):
        """センサーをリセット"""
        pass


class RaspberryPiSensorInterface(SensorInterface):
    """Raspberry Pi実機用のセンサーインターフェース

    実装例:
    - LiDAR: RPLiDAR A1/A2 (USB経由)
    - IMU: MPU6050/9250 (I2C経由)
    - エンコーダー: モーターエンコーダー (GPIO経由)
    """

    def __init__(
        self,
        lidar_port: str = "/dev/ttyUSB0",
        num_rays: int = 72,
        max_range: float = 3.0,
    ):
        """
        Args:
            lidar_port: LiDARデバイスのポート
            num_rays: 使用するレイの本数（72本 = 5度刻み）
            max_range: LiDARの最大測定距離 (m)
        """
        self.lidar_port = lidar_port
        self.num_rays = num_rays
        self.max_range = max_range

        # TODO: 実機ハードウェアの初期化
        # self.lidar = RPLidar(lidar_port)
        # self.imu = MPU6050()
        # self.encoder = MotorEncoder()

        print(f"[RaspberryPiSensorInterface] 初期化完了")
        print(f"  LiDAR: {lidar_port}")
        print(f"  Rays: {num_rays}")
        print(f"  Max Range: {max_range}m")

    def get_lidar_scan(self) -> np.ndarray:
        """LiDARスキャンデータを取得

        実装メモ:
        - RPLiDAR SDKから360度のスキャンデータを取得
        - 前方120度（-60度～+60度）の範囲を72本のレイに変換
        - シミュレーターと同じフォーマットに正規化

        Returns:
            distances: 距離データ (72,) - 前方120度をカバー
        """
        # TODO: 実機LiDARからデータ取得
        # scan_data = self.lidar.get_scan()
        # distances = self._process_lidar_data(scan_data)

        # デバッグ用: ダミーデータ
        distances = np.full(self.num_rays, self.max_range)

        return distances

    def get_velocity(self) -> Tuple[float, float]:
        """車両の速度を取得

        実装メモ:
        - エンコーダーから車輪速度を取得
        - IMUの加速度データと組み合わせて推定
        - 車体座標系での速度 (vx, vy) を計算

        Returns:
            (vx, vy): 前進方向と横方向の速度 (m/s)
        """
        # TODO: 実機センサーから速度取得
        # wheel_speed = self.encoder.get_speed()
        # imu_data = self.imu.get_acceleration()
        # vx, vy = self._compute_velocity(wheel_speed, imu_data)

        # デバッグ用: ダミーデータ
        vx, vy = 0.0, 0.0

        return vx, vy

    def get_angular_velocity(self) -> float:
        """車両の角速度を取得

        実装メモ:
        - IMUのジャイロスコープからz軸角速度を取得
        - ローパスフィルタでノイズ除去

        Returns:
            angular_velocity: 角速度 (rad/s)
        """
        # TODO: 実機IMUから角速度取得
        # gyro_data = self.imu.get_gyroscope()
        # angular_velocity = gyro_data['z']

        # デバッグ用: ダミーデータ
        angular_velocity = 0.0

        return angular_velocity

    def reset(self):
        """センサーをリセット"""
        # TODO: センサーの状態をリセット
        # self.lidar.reset()
        # self.imu.calibrate()
        # self.encoder.reset()
        pass

    def close(self):
        """センサーをクリーンアップ"""
        # TODO: センサーのクリーンアップ
        # self.lidar.stop()
        # self.lidar.disconnect()
        print("[RaspberryPiSensorInterface] クリーンアップ完了")


class MockSensorInterface(SensorInterface):
    """テスト用のモックセンサーインターフェース

    実機がない環境でのテスト・デバッグ用。
    シンプルなダミーデータを返す。
    """

    def __init__(self, num_rays: int = 72, max_range: float = 3.0):
        self.num_rays = num_rays
        self.max_range = max_range
        print("[MockSensorInterface] 初期化完了（テストモード）")

    def get_lidar_scan(self) -> np.ndarray:
        """ダミーLiDARデータを返す"""
        # 全方向に障害物なし
        return np.full(self.num_rays, self.max_range)

    def get_velocity(self) -> Tuple[float, float]:
        """ダミー速度を返す"""
        return 0.0, 0.0

    def get_angular_velocity(self) -> float:
        """ダミー角速度を返す"""
        return 0.0

    def reset(self):
        """何もしない"""
        pass

    def close(self):
        """何もしない"""
        pass
