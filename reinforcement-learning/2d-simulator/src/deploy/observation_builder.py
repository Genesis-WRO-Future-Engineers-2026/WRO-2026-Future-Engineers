"""観測空間の構築

実機のセンサーデータから学習済みモデルが期待する10次元観測空間を構築する。
"""

import numpy as np
from typing import Tuple

from .sensor_interface import SensorInterface


class ObservationBuilder:
    """観測空間構築クラス

    センサーインターフェースから取得したデータを、
    学習済みPPOモデルが期待する10次元観測空間に変換する。

    観測空間（10次元）:
    - LiDAR: 5次元（前方120度を5方向でカバー: -60° ~ +60°）
    - 速度: 2次元（vx, vy）
    - 角速度: 1次元
    - 前回の行動: 2次元（steering, throttle）
    """

    def __init__(
        self,
        sensor: SensorInterface,
        lidar_angles: np.ndarray = None,
        max_range: float = 3.0,
    ):
        """
        Args:
            sensor: センサーインターフェース
            lidar_angles: LiDARの角度（rad）、5方向を指定
            max_range: LiDARの最大測定距離（正規化用）
        """
        self.sensor = sensor
        self.max_range = max_range

        # デフォルト: 前方120度を5方向でカバー（-60° ~ +60°）
        if lidar_angles is None:
            self.lidar_angles = np.deg2rad([-60, -30, 0, 30, 60])
        else:
            assert len(lidar_angles) == 5, "LiDARは5方向である必要があります"
            self.lidar_angles = lidar_angles

        # 前回の行動（初期値）
        self.prev_action = np.array([0.0, 0.0])

        print(f"[ObservationBuilder] 初期化完了")
        print(f"  LiDAR angles: {np.rad2deg(self.lidar_angles)} degrees")
        print(f"  Max range: {max_range}m")

    def build_observation(self) -> np.ndarray:
        """センサーデータから10次元観測空間を構築

        Returns:
            observation: 10次元観測ベクトル
                [lidar_0, lidar_1, lidar_2, lidar_3, lidar_4,
                 vx, vy, angular_velocity,
                 prev_steering, prev_throttle]
        """
        # LiDARスキャン取得（72方向のフルスキャン）
        full_lidar_scan = self.sensor.get_lidar_scan()

        # 前方120度の5方向に絞り込み
        lidar_5_directions = self._extract_5_directions(full_lidar_scan)

        # LiDARを正規化 [0, max_range] → [0, 1]
        lidar_normalized = lidar_5_directions / self.max_range

        # 速度取得
        vx, vy = self.sensor.get_velocity()

        # 角速度取得
        angular_velocity = self.sensor.get_angular_velocity()

        # 観測ベクトルを構築（10次元）
        observation = np.concatenate([
            lidar_normalized,  # 5次元
            [vx, vy],  # 2次元
            [angular_velocity],  # 1次元
            self.prev_action,  # 2次元
        ])

        assert observation.shape == (10,), f"観測空間は10次元である必要があります: {observation.shape}"

        return observation

    def update_prev_action(self, action: np.ndarray):
        """前回の行動を更新

        Args:
            action: [steering, throttle]
        """
        self.prev_action = action.copy()

    def reset(self):
        """前回の行動をリセット"""
        self.prev_action = np.array([0.0, 0.0])

    def _extract_5_directions(self, full_scan: np.ndarray) -> np.ndarray:
        """72方向のLiDARスキャンから前方120度の5方向を抽出

        full_scanは72方向（0度 ~ 360度を5度刻み）を想定。
        前方120度（-60度 ~ +60度）の5方向を抽出する。

        Args:
            full_scan: 72方向のLiDARスキャン (72,)

        Returns:
            lidar_5: 5方向のLiDARデータ
        """
        num_rays = len(full_scan)

        # 72方向の場合、各レイの角度間隔は5度
        angle_per_ray = 360.0 / num_rays

        # 各ターゲット角度に最も近いレイのインデックスを取得
        target_angles_deg = np.rad2deg(self.lidar_angles)  # [-60, -30, 0, 30, 60]

        # 0度を前方として、-60度～+60度に対応するインデックスを計算
        # 0度 = index 0, 5度 = index 1, ... 355度 = index 71
        # -60度 = 300度 = index 60
        # -30度 = 330度 = index 66
        # 0度 = 0度 = index 0
        # 30度 = 30度 = index 6
        # 60度 = 60度 = index 12

        indices = []
        for angle_deg in target_angles_deg:
            # 負の角度を正規化（-60度 → 300度）
            normalized_angle = angle_deg % 360
            index = int(round(normalized_angle / angle_per_ray)) % num_rays
            indices.append(index)

        lidar_5 = full_scan[indices]

        return lidar_5
