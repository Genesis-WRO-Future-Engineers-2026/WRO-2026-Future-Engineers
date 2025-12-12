"""物理パラメータのランダム化

エピソードごとに物理パラメータをランダム化し、ロバストなポリシーを学習する。
"""

import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class PhysicsRandomizationConfig:
    """物理ランダム化の設定

    各パラメータは (min, max) のタプルで範囲を指定。
    Noneの場合はランダム化を無効化。
    """

    # 摩擦係数のランダム化範囲
    friction_range: Optional[tuple] = (0.5, 1.0)

    # 質量のランダム化範囲 (kg)
    mass_range: Optional[tuple] = (1.2, 1.6)

    # 慣性の倍率ランダム化範囲
    inertia_scale_range: Optional[tuple] = (0.8, 1.2)

    # モーター力のランダム化範囲 (N)
    motor_force_range: Optional[tuple] = (18.0, 22.0)

    # モーター応答遅延のランダム化範囲 (秒)
    motor_delay_range: Optional[tuple] = (0.0, 0.05)

    # 線形減衰のランダム化範囲
    linear_damping_range: Optional[tuple] = (0.4, 0.6)

    # 角減衰のランダム化範囲
    angular_damping_range: Optional[tuple] = (0.6, 1.0)

    # 最大横滑りインパルスのランダム化範囲 (N·s)
    max_lateral_impulse_range: Optional[tuple] = (2.0, 3.0)

    # 乱数シード（再現性のため、Noneで毎回変わる）
    seed: Optional[int] = None


class PhysicsRandomizer:
    """物理パラメータのランダム化を管理するクラス

    エピソードごとに呼び出され、物理パラメータをランダム化した
    辞書を返す。

    Example:
        >>> config = PhysicsRandomizationConfig()
        >>> randomizer = PhysicsRandomizer(config)
        >>> params = randomizer.randomize()
        >>> print(params['mass'])  # 1.2 ~ 1.6 kg
    """

    def __init__(self, config: PhysicsRandomizationConfig):
        """
        Args:
            config: ランダム化の設定
        """
        self.config = config
        self._rng = np.random.default_rng(config.seed)

    def randomize(self) -> Dict[str, float]:
        """物理パラメータをランダム化

        Returns:
            ランダム化されたパラメータの辞書
            {
                'friction': 0.7,
                'mass': 1.4,
                'inertia_scale': 1.0,
                'motor_force': 20.0,
                'motor_delay': 0.02,
                'linear_damping': 0.5,
                'angular_damping': 0.8,
                'max_lateral_impulse': 2.5,
            }
        """
        params = {}

        # 摩擦係数
        if self.config.friction_range is not None:
            params['friction'] = self._rng.uniform(*self.config.friction_range)
        else:
            params['friction'] = 0.7  # デフォルト値

        # 質量
        if self.config.mass_range is not None:
            params['mass'] = self._rng.uniform(*self.config.mass_range)
        else:
            params['mass'] = 1.4  # デフォルト値

        # 慣性スケール
        if self.config.inertia_scale_range is not None:
            params['inertia_scale'] = self._rng.uniform(*self.config.inertia_scale_range)
        else:
            params['inertia_scale'] = 1.0

        # モーター力
        if self.config.motor_force_range is not None:
            params['motor_force'] = self._rng.uniform(*self.config.motor_force_range)
        else:
            params['motor_force'] = 20.0  # デフォルト値

        # モーター応答遅延
        if self.config.motor_delay_range is not None:
            params['motor_delay'] = self._rng.uniform(*self.config.motor_delay_range)
        else:
            params['motor_delay'] = 0.0

        # 線形減衰
        if self.config.linear_damping_range is not None:
            params['linear_damping'] = self._rng.uniform(*self.config.linear_damping_range)
        else:
            params['linear_damping'] = 0.5  # デフォルト値

        # 角減衰
        if self.config.angular_damping_range is not None:
            params['angular_damping'] = self._rng.uniform(*self.config.angular_damping_range)
        else:
            params['angular_damping'] = 0.8  # デフォルト値

        # 最大横滑りインパルス
        if self.config.max_lateral_impulse_range is not None:
            params['max_lateral_impulse'] = self._rng.uniform(*self.config.max_lateral_impulse_range)
        else:
            params['max_lateral_impulse'] = 2.5  # デフォルト値

        return params

    def get_default_params(self) -> Dict[str, float]:
        """デフォルトの物理パラメータを返す

        Returns:
            デフォルトパラメータの辞書
        """
        return {
            'friction': 0.7,
            'mass': 1.4,
            'inertia_scale': 1.0,
            'motor_force': 20.0,
            'motor_delay': 0.0,
            'linear_damping': 0.5,
            'angular_damping': 0.8,
            'max_lateral_impulse': 2.5,
        }


# デフォルト設定のインスタンス
DEFAULT_PHYSICS_CONFIG = PhysicsRandomizationConfig()

# 軽微なランダム化設定（最初のテスト用）
MILD_PHYSICS_CONFIG = PhysicsRandomizationConfig(
    friction_range=(0.6, 0.8),
    mass_range=(1.3, 1.5),
    inertia_scale_range=(0.9, 1.1),
    motor_force_range=(19.0, 21.0),
    motor_delay_range=(0.0, 0.02),
    linear_damping_range=(0.45, 0.55),
    angular_damping_range=(0.7, 0.9),
    max_lateral_impulse_range=(2.3, 2.7),
)

# 強めのランダム化設定（実機転移用）
STRONG_PHYSICS_CONFIG = PhysicsRandomizationConfig(
    friction_range=(0.5, 1.0),
    mass_range=(1.2, 1.6),
    inertia_scale_range=(0.8, 1.2),
    motor_force_range=(18.0, 22.0),
    motor_delay_range=(0.0, 0.05),
    linear_damping_range=(0.4, 0.6),
    angular_damping_range=(0.6, 1.0),
    max_lateral_impulse_range=(2.0, 3.0),
)
