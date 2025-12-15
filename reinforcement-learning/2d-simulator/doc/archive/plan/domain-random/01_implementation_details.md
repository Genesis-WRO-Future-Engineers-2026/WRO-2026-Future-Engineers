# Domain Randomization実装計画 - 実装詳細

## 1. PhysicsRandomizer実装

### 1.1 ファイル: `src/domain_randomization/physics_randomizer.py`

```python
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
```

---

## 2. SensorNoise実装

### 2.1 ファイル: `src/domain_randomization/sensor_noise.py`

```python
"""センサーノイズの統合

既存のLiDARSensor.add_advanced_noise()を活用し、
エピソードごとにノイズレベルをランダム化する。
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass


@dataclass
class SensorNoiseConfig:
    """センサーノイズの設定

    各パラメータは (min, max) のタプルで範囲を指定。
    Noneの場合はノイズを無効化。
    """

    # ガウシアンノイズレベルの範囲（距離に対する割合）
    noise_level_range: Optional[tuple] = (0.01, 0.02)

    # ドロップアウト確率の範囲
    dropout_prob_range: Optional[tuple] = (0.02, 0.05)

    # スパイクノイズ確率の範囲
    spike_prob_range: Optional[tuple] = (0.005, 0.01)

    # 乱数シード（再現性のため、Noneで毎回変わる）
    seed: Optional[int] = None


class SensorNoiseRandomizer:
    """センサーノイズのランダム化を管理するクラス

    エピソードごとに呼び出され、ノイズパラメータをランダム化。

    Example:
        >>> config = SensorNoiseConfig()
        >>> randomizer = SensorNoiseRandomizer(config)
        >>> noise_params = randomizer.get_noise_params()
        >>> # LiDARSensor.add_advanced_noise()に渡す
    """

    def __init__(self, config: SensorNoiseConfig):
        """
        Args:
            config: ノイズ設定
        """
        self.config = config
        self._rng = np.random.default_rng(config.seed)

    def get_noise_params(self) -> dict:
        """ノイズパラメータをランダム化

        Returns:
            LiDARSensor.add_advanced_noise()に渡すパラメータ
            {
                'noise_level': 0.015,
                'dropout_prob': 0.03,
                'spike_prob': 0.008,
            }
        """
        params = {}

        # ガウシアンノイズレベル
        if self.config.noise_level_range is not None:
            params['noise_level'] = self._rng.uniform(*self.config.noise_level_range)
        else:
            params['noise_level'] = 0.0

        # ドロップアウト確率
        if self.config.dropout_prob_range is not None:
            params['dropout_prob'] = self._rng.uniform(*self.config.dropout_prob_range)
        else:
            params['dropout_prob'] = 0.0

        # スパイクノイズ確率
        if self.config.spike_prob_range is not None:
            params['spike_prob'] = self._rng.uniform(*self.config.spike_prob_range)
        else:
            params['spike_prob'] = 0.0

        return params

    def apply_noise(self, lidar_sensor, distances: np.ndarray) -> np.ndarray:
        """LiDARスキャンにノイズを適用

        Args:
            lidar_sensor: LiDARSensorインスタンス
            distances: クリーンな距離データ

        Returns:
            ノイズを加えた距離データ
        """
        params = self.get_noise_params()

        # ノイズレベルがすべて0の場合はそのまま返す
        if (params['noise_level'] == 0.0 and
            params['dropout_prob'] == 0.0 and
            params['spike_prob'] == 0.0):
            return distances

        # 既存のadd_advanced_noise()メソッドを使用
        return lidar_sensor.add_advanced_noise(
            distances,
            noise_level=params['noise_level'],
            dropout_prob=params['dropout_prob'],
            spike_prob=params['spike_prob'],
        )


# デフォルト設定のインスタンス
DEFAULT_SENSOR_NOISE_CONFIG = SensorNoiseConfig()

# 軽微なノイズ設定（最初のテスト用）
MILD_SENSOR_NOISE_CONFIG = SensorNoiseConfig(
    noise_level_range=(0.005, 0.01),
    dropout_prob_range=(0.01, 0.02),
    spike_prob_range=(0.002, 0.005),
)

# 強めのノイズ設定（実機転移用）
STRONG_SENSOR_NOISE_CONFIG = SensorNoiseConfig(
    noise_level_range=(0.01, 0.02),
    dropout_prob_range=(0.02, 0.05),
    spike_prob_range=(0.005, 0.01),
)
```

---

## 3. Vehicle クラスの拡張

### 3.1 修正: `src/env/vehicle.py`

既存の`Vehicle`クラスに、ランダム化されたパラメータを受け取る機能を追加します。

```python
class Vehicle:
    """ミニカーの物理モデル"""

    def __init__(
        self,
        world: b2World,
        start_pos: Tuple[float, float],
        start_angle: float = 0.0,
        # 以下、Domain Randomization用の追加パラメータ
        mass: float = 1.4,
        friction: float = 0.7,
        linear_damping: float = 0.5,
        angular_damping: float = 0.8,
        max_motor_force: float = 20.0,
        max_lateral_impulse: float = 2.5,
    ):
        """
        Args:
            world: Box2Dの物理世界
            start_pos: 初期位置 (x, y)
            start_angle: 初期角度 (rad)
            mass: 質量 (kg) - Domain Randomization対応
            friction: 摩擦係数 - Domain Randomization対応
            linear_damping: 線形減衰 - Domain Randomization対応
            angular_damping: 角減衰 - Domain Randomization対応
            max_motor_force: 最大モーター力 (N) - Domain Randomization対応
            max_lateral_impulse: 最大横滑りインパルス - Domain Randomization対応
        """
        self.world = world

        # 車両パラメータ（Domain Randomization対応）
        self.width = 0.188  # m (実機: 188mm)
        self.length = 0.479  # m (実機: 479mm)
        self.mass = mass  # ランダム化可能
        self.wheelbase = 0.257  # m (実機: 257mm、標準設定)

        self.max_steering_angle = 0.5  # rad (約28度)
        self.max_motor_force = max_motor_force  # ランダム化可能
        self.max_lateral_impulse = max_lateral_impulse  # ランダム化可能

        # Box2Dボディ作成
        self.body = self.world.CreateDynamicBody(
            position=b2Vec2(*start_pos),
            angle=start_angle,
            linearDamping=linear_damping,  # ランダム化可能
            angularDamping=angular_damping,  # ランダム化可能
        )

        # 車両の識別子を設定（衝突検出用）
        self.body.userData = "vehicle"

        # 車両の形状（矩形）
        self.body.CreatePolygonFixture(
            box=(self.length / 2, self.width / 2),
            density=self.mass / (self.length * self.width),
            friction=friction,  # ランダム化可能
        )

    # resetメソッドも同様に拡張
    def reset(
        self,
        position: Tuple[float, float],
        angle: float = 0.0,
        # Domain Randomization用パラメータ
        mass: Optional[float] = None,
        friction: Optional[float] = None,
        linear_damping: Optional[float] = None,
        angular_damping: Optional[float] = None,
        max_motor_force: Optional[float] = None,
        max_lateral_impulse: Optional[float] = None,
    ):
        """車両をリセット

        Args:
            position: 位置 (x, y)
            angle: 角度 (rad)
            mass: 質量（Noneの場合は現在値を維持）
            friction: 摩擦係数（Noneの場合は現在値を維持）
            ... 他のパラメータも同様
        """
        # パラメータを更新（指定された場合のみ）
        if mass is not None:
            self.mass = mass
        if max_motor_force is not None:
            self.max_motor_force = max_motor_force
        if max_lateral_impulse is not None:
            self.max_lateral_impulse = max_lateral_impulse

        # ボディの物理パラメータを更新
        if linear_damping is not None:
            self.body.linearDamping = linear_damping
        if angular_damping is not None:
            self.body.angularDamping = angular_damping

        # フィクスチャの摩擦係数を更新
        if friction is not None:
            for fixture in self.body.fixtures:
                fixture.friction = friction
            # 密度も更新（質量が変わった場合）
            if mass is not None:
                for fixture in self.body.fixtures:
                    fixture.density = self.mass / (self.length * self.width)

        # 位置と速度をリセット
        self.body.position = b2Vec2(*position)
        self.body.angle = angle
        self.body.linearVelocity = b2Vec2(0, 0)
        self.body.angularVelocity = 0.0
```

---

## 4. MinicarEnv の拡張

### 4.1 修正: `src/env/minicar_env.py`

```python
from src.domain_randomization.physics_randomizer import (
    PhysicsRandomizer,
    PhysicsRandomizationConfig,
    DEFAULT_PHYSICS_CONFIG,
)
from src.domain_randomization.sensor_noise import (
    SensorNoiseRandomizer,
    SensorNoiseConfig,
    DEFAULT_SENSOR_NOISE_CONFIG,
)


class MinicarEnv(gym.Env):
    """ミニカーレースのGym互換環境"""

    def __init__(
        self,
        course_file: str = "courses/easy/simple_oval.json",
        render_mode: Optional[str] = None,
        max_steps: int = 2000,
        deployment_mode: bool = False,
        # Domain Randomization用の追加パラメータ
        enable_domain_randomization: bool = False,
        physics_randomization_config: Optional[PhysicsRandomizationConfig] = None,
        sensor_noise_config: Optional[SensorNoiseConfig] = None,
    ):
        """
        Args:
            ... (既存の引数)
            enable_domain_randomization: Domain Randomizationを有効化
            physics_randomization_config: 物理ランダム化の設定
            sensor_noise_config: センサーノイズの設定
        """
        super().__init__()

        # ... (既存の初期化コード)

        # Domain Randomization設定
        self.enable_domain_randomization = enable_domain_randomization

        if self.enable_domain_randomization:
            # 物理ランダム化
            physics_config = physics_randomization_config or DEFAULT_PHYSICS_CONFIG
            self.physics_randomizer = PhysicsRandomizer(physics_config)

            # センサーノイズ
            sensor_config = sensor_noise_config or DEFAULT_SENSOR_NOISE_CONFIG
            self.sensor_noise_randomizer = SensorNoiseRandomizer(sensor_config)

            print("[INFO] Domain Randomization enabled")
        else:
            self.physics_randomizer = None
            self.sensor_noise_randomizer = None

    def reset(
        self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """環境をリセット"""
        super().reset(seed=seed)

        # Domain Randomization: 物理パラメータをランダム化
        if self.enable_domain_randomization and self.physics_randomizer:
            physics_params = self.physics_randomizer.randomize()
        else:
            physics_params = self.physics_randomizer.get_default_params() if self.physics_randomizer else {}

        # 車両をリセット（ランダム化されたパラメータで）
        start_pos, start_angle = self.course.get_start_pose()

        if physics_params:
            self.vehicle.reset(
                start_pos,
                start_angle,
                mass=physics_params.get('mass'),
                friction=physics_params.get('friction'),
                linear_damping=physics_params.get('linear_damping'),
                angular_damping=physics_params.get('angular_damping'),
                max_motor_force=physics_params.get('motor_force'),
                max_lateral_impulse=physics_params.get('max_lateral_impulse'),
            )
        else:
            self.vehicle.reset(start_pos, start_angle)

        # ... (既存のリセットコード)

        return obs, info

    def _get_observation(self) -> np.ndarray:
        """観測を取得（Domain Randomization対応）"""
        # キャッシュされたLiDARスキャンを使用
        lidar_distances = self._cached_lidar_scan.copy()

        # Domain Randomization: センサーノイズを適用
        if self.enable_domain_randomization and self.sensor_noise_randomizer:
            lidar_distances = self.sensor_noise_randomizer.apply_noise(
                self.lidar,
                lidar_distances
            )

        # LiDARの正規化（5次元）
        lidar_normalized = lidar_distances / LIDAR_MAX_RANGE

        # 車両状態の取得
        state = self._cached_vehicle_state
        vx, vy = state["linear_velocity"]
        angular_velocity = state["angular_velocity"]

        # 観測空間の構成: LiDAR(5) + velocity(2) + angular_velocity(1) + last_action(2) = 10
        obs = np.concatenate([
            lidar_normalized,  # 5次元
            [vx / 3.0, vy / 3.0],  # 2次元（正規化）
            [angular_velocity / 5.0],  # 1次元（正規化）
            self.last_action,  # 2次元
        ]).astype(np.float32)

        return obs
```

---

## 5. 設定ファイルの作成

### 5.1 ファイル: `src/domain_randomization/config.py`

```python
"""Domain Randomization設定のプリセット"""

from .physics_randomizer import PhysicsRandomizationConfig
from .sensor_noise import SensorNoiseConfig


# レベル1: 無効化（デフォルト）
DISABLED_CONFIG = {
    'physics': None,
    'sensor': None,
}

# レベル2: 軽微なランダム化（最初のテスト用）
MILD_CONFIG = {
    'physics': PhysicsRandomizationConfig(
        friction_range=(0.6, 0.8),
        mass_range=(1.3, 1.5),
        inertia_scale_range=(0.9, 1.1),
        motor_force_range=(19.0, 21.0),
        motor_delay_range=(0.0, 0.02),
        linear_damping_range=(0.45, 0.55),
        angular_damping_range=(0.7, 0.9),
        max_lateral_impulse_range=(2.3, 2.7),
    ),
    'sensor': SensorNoiseConfig(
        noise_level_range=(0.005, 0.01),
        dropout_prob_range=(0.01, 0.02),
        spike_prob_range=(0.002, 0.005),
    ),
}

# レベル3: 標準ランダム化（通常の学習用）
STANDARD_CONFIG = {
    'physics': PhysicsRandomizationConfig(
        friction_range=(0.5, 0.9),
        mass_range=(1.2, 1.6),
        inertia_scale_range=(0.85, 1.15),
        motor_force_range=(18.5, 21.5),
        motor_delay_range=(0.0, 0.03),
        linear_damping_range=(0.4, 0.6),
        angular_damping_range=(0.65, 0.95),
        max_lateral_impulse_range=(2.2, 2.8),
    ),
    'sensor': SensorNoiseConfig(
        noise_level_range=(0.01, 0.015),
        dropout_prob_range=(0.02, 0.04),
        spike_prob_range=(0.005, 0.008),
    ),
}

# レベル4: 強めのランダム化（実機転移用）
STRONG_CONFIG = {
    'physics': PhysicsRandomizationConfig(
        friction_range=(0.5, 1.0),
        mass_range=(1.2, 1.6),
        inertia_scale_range=(0.8, 1.2),
        motor_force_range=(18.0, 22.0),
        motor_delay_range=(0.0, 0.05),
        linear_damping_range=(0.4, 0.6),
        angular_damping_range=(0.6, 1.0),
        max_lateral_impulse_range=(2.0, 3.0),
    ),
    'sensor': SensorNoiseConfig(
        noise_level_range=(0.01, 0.02),
        dropout_prob_range=(0.02, 0.05),
        spike_prob_range=(0.005, 0.01),
    ),
}


def get_config(level: str = 'disabled'):
    """設定レベルに応じたConfigを取得

    Args:
        level: 'disabled', 'mild', 'standard', 'strong'

    Returns:
        {'physics': PhysicsRandomizationConfig, 'sensor': SensorNoiseConfig}
    """
    configs = {
        'disabled': DISABLED_CONFIG,
        'mild': MILD_CONFIG,
        'standard': STANDARD_CONFIG,
        'strong': STRONG_CONFIG,
    }

    if level not in configs:
        raise ValueError(f"Unknown config level: {level}. Choose from {list(configs.keys())}")

    return configs[level]
```

---

## 6. __init__.py の作成

### 6.1 ファイル: `src/domain_randomization/__init__.py`

```python
"""Domain Randomization モジュール

物理パラメータとセンサーノイズをランダム化し、
実機転移性能を向上させる。
"""

from .physics_randomizer import (
    PhysicsRandomizer,
    PhysicsRandomizationConfig,
    DEFAULT_PHYSICS_CONFIG,
    MILD_PHYSICS_CONFIG,
    STRONG_PHYSICS_CONFIG,
)

from .sensor_noise import (
    SensorNoiseRandomizer,
    SensorNoiseConfig,
    DEFAULT_SENSOR_NOISE_CONFIG,
    MILD_SENSOR_NOISE_CONFIG,
    STRONG_SENSOR_NOISE_CONFIG,
)

from .config import (
    get_config,
    DISABLED_CONFIG,
    MILD_CONFIG,
    STANDARD_CONFIG,
    STRONG_CONFIG,
)

__all__ = [
    # Physics Randomization
    'PhysicsRandomizer',
    'PhysicsRandomizationConfig',
    'DEFAULT_PHYSICS_CONFIG',
    'MILD_PHYSICS_CONFIG',
    'STRONG_PHYSICS_CONFIG',

    # Sensor Noise
    'SensorNoiseRandomizer',
    'SensorNoiseConfig',
    'DEFAULT_SENSOR_NOISE_CONFIG',
    'MILD_SENSOR_NOISE_CONFIG',
    'STRONG_SENSOR_NOISE_CONFIG',

    # Config
    'get_config',
    'DISABLED_CONFIG',
    'MILD_CONFIG',
    'STANDARD_CONFIG',
    'STRONG_CONFIG',
]
```

---

**次**: [02_integration_guide.md](./02_integration_guide.md)で統合手順を確認してください。
