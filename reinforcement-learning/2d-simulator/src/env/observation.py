"""観測空間の構築"""

import numpy as np
from typing import Dict, Optional
from .sensors import LIDAR_MAX_RANGE


class ObservationConfig:
    """観測空間の設定

    正規化係数などの設定を管理する。
    """

    def __init__(
        self,
        lidar_max_range: float = LIDAR_MAX_RANGE,
        velocity_scale: float = 3.0,
        angular_velocity_scale: float = 5.0,
    ):
        """
        Args:
            lidar_max_range: LiDARの最大距離（正規化に使用）
            velocity_scale: 速度の正規化係数
            angular_velocity_scale: 角速度の正規化係数
        """
        self.lidar_max_range = lidar_max_range
        self.velocity_scale = velocity_scale
        self.angular_velocity_scale = angular_velocity_scale


class ObservationBuilder:
    """観測空間の構築を担当するクラス

    車両状態、LiDARスキャン、前回の行動から観測ベクトルを構築する。
    Domain Randomizationのノイズ適用も担当する。
    """

    def __init__(
        self,
        config: Optional[ObservationConfig] = None,
        sensor_noise_randomizer=None,  # SensorNoiseRandomizer
    ):
        """
        Args:
            config: 観測空間の設定
            sensor_noise_randomizer: センサーノイズランダマイザー（Domain Randomization用）
        """
        self.config = config if config is not None else ObservationConfig()
        self.sensor_noise_randomizer = sensor_noise_randomizer

    def build(
        self,
        lidar_scan: np.ndarray,
        vehicle_state: Dict,
        last_action: np.ndarray,
        lidar_sensor=None,  # LiDARSensor（ノイズ適用時に必要）
    ) -> np.ndarray:
        """観測ベクトルを構築

        Args:
            lidar_scan: LiDARスキャン結果
            vehicle_state: 車両状態の辞書
            last_action: 前回の行動
            lidar_sensor: LiDARセンサー（ノイズ適用時に必要）

        Returns:
            観測ベクトル (10次元)
        """
        # LiDARスキャンをコピー
        lidar = lidar_scan.copy()

        # Domain Randomization: センサーノイズを適用
        if self.sensor_noise_randomizer is not None and lidar_sensor is not None:
            lidar = self.sensor_noise_randomizer.apply_noise(lidar_sensor, lidar)

        # LiDARの正規化
        lidar_normalized = lidar / self.config.lidar_max_range

        # 速度の正規化
        velocity = np.array(vehicle_state["velocity"]) / self.config.velocity_scale

        # 角速度の正規化
        angular_velocity = np.array([vehicle_state["angular_velocity"]]) / self.config.angular_velocity_scale

        # 観測を結合
        obs = np.concatenate([
            lidar_normalized,    # 5次元
            velocity,            # 2次元
            angular_velocity,    # 1次元
            last_action,         # 2次元
        ])

        return obs.astype(np.float32)

    def get_observation_space_shape(self) -> tuple:
        """観測空間の形状を返す

        Returns:
            観測空間の形状 (10,)
        """
        return (10,)
