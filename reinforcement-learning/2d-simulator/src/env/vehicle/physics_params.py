"""Domain Randomization用の物理パラメータ管理"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PhysicsParameters:
    """Domain Randomization用の物理パラメータ

    `Vehicle.reset()`で一括設定するためのパラメータセット。
    """

    # 車両の質量
    mass: Optional[float] = None  # kg

    # Box2Dボディのパラメータ
    friction: Optional[float] = None
    linear_damping: Optional[float] = None
    angular_damping: Optional[float] = None

    # 制御力のパラメータ
    max_motor_force: Optional[float] = None  # N
    max_lateral_impulse: Optional[float] = None

    @classmethod
    def create_default(cls) -> 'PhysicsParameters':
        """デフォルトパラメータを作成"""
        return cls(
            mass=1.4,
            friction=0.7,
            linear_damping=0.5,
            angular_damping=0.8,
            max_motor_force=20.0,
            max_lateral_impulse=2.5,
        )

    @classmethod
    def create_from_dict(cls, params: dict) -> 'PhysicsParameters':
        """辞書からパラメータを作成（Domain Randomizer用）"""
        return cls(
            mass=params.get('mass'),
            friction=params.get('friction'),
            linear_damping=params.get('linear_damping'),
            angular_damping=params.get('angular_damping'),
            max_motor_force=params.get('motor_force'),
            max_lateral_impulse=params.get('max_lateral_impulse'),
        )

    def has_updates(self) -> bool:
        """更新すべきパラメータがあるか"""
        return any([
            self.mass is not None,
            self.friction is not None,
            self.linear_damping is not None,
            self.angular_damping is not None,
            self.max_motor_force is not None,
            self.max_lateral_impulse is not None,
        ])
