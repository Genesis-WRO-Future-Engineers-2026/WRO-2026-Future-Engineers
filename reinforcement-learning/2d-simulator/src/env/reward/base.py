"""報酬関数の基底クラス"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import numpy as np


class RewardComponent(ABC):
    """報酬成分の基底クラス

    各報酬成分は独立して計算可能であり、
    複合報酬関数で組み合わせることができる。
    """

    def __init__(self, weight: float = 1.0):
        """
        Args:
            weight: この報酬成分の重み（係数）
        """
        self.weight = weight

    @abstractmethod
    def compute(self, context: 'RewardContext') -> float:
        """報酬を計算

        Args:
            context: 報酬計算に必要なコンテキスト情報

        Returns:
            報酬値（重み適用前）
        """
        pass

    def __call__(self, context: 'RewardContext') -> float:
        """重み適用後の報酬を計算"""
        return self.weight * self.compute(context)


class RewardContext:
    """報酬計算に必要なコンテキスト情報

    報酬計算に必要なすべての情報を格納する。
    環境の内部状態を直接参照せず、必要な情報のみを渡す。
    """

    def __init__(
        self,
        # 車両状態
        position: tuple,
        velocity: tuple,
        speed: float,
        angle: float,
        angular_velocity: float,

        # センサー情報
        lidar_scan: np.ndarray,

        # 行動
        action: np.ndarray,

        # コース情報
        checkpoints: list,
        next_checkpoint_index: int,
        goal_position: tuple,
        goal_radius: float,

        # 環境状態
        step_count: int,
        max_steps: int,
        has_collision: bool,

        # その他
        deployment_mode: bool = False,
    ):
        self.position = position
        self.velocity = velocity
        self.speed = speed
        self.angle = angle
        self.angular_velocity = angular_velocity

        self.lidar_scan = lidar_scan
        self.action = action

        self.checkpoints = checkpoints
        self.next_checkpoint_index = next_checkpoint_index
        self.goal_position = goal_position
        self.goal_radius = goal_radius

        self.step_count = step_count
        self.max_steps = max_steps
        self.has_collision = has_collision

        self.deployment_mode = deployment_mode
