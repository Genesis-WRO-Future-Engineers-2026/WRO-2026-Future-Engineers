# `src/env/minicar_env.py` 詳細リファクタリング計画

**作成日**: 2025-12-13
**対象ファイル**: `src/env/minicar_env.py` (554行)
**目標**: 単一責任原則の適用により250行程度に削減（-55%）

---

## 📋 目次

1. [現状分析](#1-現状分析)
2. [問題点の詳細](#2-問題点の詳細)
3. [リファクタリング戦略](#3-リファクタリング戦略)
4. [新しいモジュール構成](#4-新しいモジュール構成)
5. [段階的実装計画](#5-段階的実装計画)
6. [後方互換性の維持](#6-後方互換性の維持)
7. [テスト戦略](#7-テスト戦略)
8. [実装の詳細](#8-実装の詳細)

---

## 1. 現状分析

### 1.1 ファイル構成

```
MinicarEnv (554行)
├── __init__()          : 113行 (L40-152)  ← Domain Randomization設定で肥大化
├── reset()             : 54行  (L156-209) ← Domain Randomization処理を含む
├── step()              : 46行  (L211-256)
├── _get_observation()  : 38行  (L258-295) ← Domain Randomizationノイズ適用
├── _compute_reward()   : 82行  (L297-378) ← 最大の肥大化箇所
├── _check_terminated() : 33行  (L380-412)
├── _get_info()         : 24行  (L414-437)
├── render()            : 64行  (L439-502)
├── close()             : 5行   (L504-508)
└── load_course()       : 45行  (L510-554) ← カリキュラム学習用
```

### 1.2 責務の分析

現在の`MinicarEnv`クラスは以下の責務を持っています:

| 責務 | 該当メソッド | 行数 | 問題度 |
|-----|------------|------|--------|
| **環境管理** | `__init__`, `reset`, `step`, `close` | ~200行 | ⚠️ 中 |
| **観測空間の構築** | `_get_observation` | 38行 | ⚠️ 低 |
| **報酬計算** | `_compute_reward` | 82行 | 🔴 高 |
| **終了判定** | `_check_terminated` | 33行 | ⚠️ 低 |
| **情報提供** | `_get_info` | 24行 | ✅ 問題なし |
| **レンダリング** | `render` | 64行 | ⚠️ 中 |
| **コース切り替え** | `load_course` | 45行 | ⚠️ 中 |
| **Domain Randomization** | `__init__`, `reset`, `_get_observation` | ~50行 | ⚠️ 中 |
| **Adaptive Reward** | `_compute_reward` | ~20行 | ⚠️ 低 |

**結論**: 特に**報酬計算**と**Domain Randomization**が肥大化の主要因です。

---

## 2. 問題点の詳細

### 2.1 `__init__()` の問題点 (113行)

#### 問題箇所

```python
# L73-93: Domain Randomization設定の条件分岐
if self.enable_domain_randomization:
    if physics_randomization_config is not None:
        self.physics_randomizer = PhysicsRandomizer(physics_randomization_config)
    else:
        from src.domain_randomization.physics_randomizer import DEFAULT_PHYSICS_CONFIG
        self.physics_randomizer = PhysicsRandomizer(DEFAULT_PHYSICS_CONFIG)

    if sensor_noise_config is not None:
        self.sensor_noise_randomizer = SensorNoiseRandomizer(sensor_noise_config)
    else:
        from src.domain_randomization.sensor_noise import DEFAULT_SENSOR_NOISE_CONFIG
        self.sensor_noise_randomizer = SensorNoiseRandomizer(DEFAULT_SENSOR_NOISE_CONFIG)
    # ...
else:
    self.physics_randomizer = None
    self.sensor_noise_randomizer = None
```

#### 問題点

1. **条件分岐が深い** (3レベルのネスト)
2. **デフォルト設定のインポートが遅延している** (遅延インポートは良いが、冗長)
3. **同じパターンの繰り返し** (physics/sensor で同じロジック)

---

### 2.2 `_compute_reward()` の問題点 (82行)

#### 問題箇所

```python
def _compute_reward(self) -> float:
    reward = 0.0
    state = self._cached_vehicle_state
    lidar_scan = self._cached_lidar_scan

    # 適応的報酬スケーリングが有効な場合は係数を取得
    if self.adaptive_reward_scaler is not None:
        coeffs = self.adaptive_reward_scaler.get_coefficients()
    else:
        coeffs = RewardCoefficients(
            time_penalty=0.7,
            direction_reward_scale=0.7,
            checkpoint_reward=200.0,
            goal_reward=500.0,
            collision_penalty=-100.0,
            time_bonus_scale=2.0,
        )

    # 1. 時間ペナルティ
    reward -= coeffs.time_penalty

    # 2. チェックポイント方向報酬（30行近く）
    checkpoints = self.course.get_checkpoints()
    if self.next_checkpoint_index < len(checkpoints):
        cp_pos = checkpoints[self.next_checkpoint_index]["position"]
        distance_to_cp = np.linalg.norm(...)
        max_distance = 20.0  # ハードコード
        normalized_distance = min(distance_to_cp, max_distance)
        reward += (max_distance - normalized_distance) / max_distance * coeffs.direction_reward_scale

        # 2.1. チェックポイント通過報酬
        if self.course.check_checkpoint(state["position"], self.next_checkpoint_index):
            reward += coeffs.checkpoint_reward
            self.next_checkpoint_index += 1
    else:
        # ゴール方向報酬（10行）
        goal_pos, _ = self.course.get_goal_info()
        distance_to_goal = np.linalg.norm(...)
        # ...

    # 3. ゴール到達報酬
    if self.course.check_goal(state["position"]):
        if self.next_checkpoint_index == len(checkpoints):
            reward += coeffs.goal_reward
            remaining_steps = self.max_steps - self.step_count
            time_bonus = remaining_steps * coeffs.time_bonus_scale
            reward += time_bonus

    # 4. 衝突ペナルティ
    if self.world.has_collision():
        reward += coeffs.collision_penalty

    return reward
```

#### 問題点

1. **複数の報酬成分が1つのメソッドに混在**
   - 時間ペナルティ
   - 方向報酬
   - チェックポイント報酬
   - ゴール報酬
   - 衝突ペナルティ

2. **状態管理の混在**
   - `self.next_checkpoint_index`の更新が報酬計算内で行われている
   - 副作用がある（純粋関数でない）

3. **マジックナンバー**
   - `max_distance = 20.0`がハードコード

4. **デフォルト係数のハードコード**
   - `RewardCoefficients`の直接生成がメソッド内にある

---

### 2.3 `_get_observation()` の問題点 (38行)

#### 問題箇所

```python
def _get_observation(self) -> np.ndarray:
    lidar_scan = self._cached_lidar_scan.copy()

    # Domain Randomization: センサーノイズを適用
    if self.enable_domain_randomization and self.sensor_noise_randomizer:
        lidar_scan = self.sensor_noise_randomizer.apply_noise(
            self.lidar,
            lidar_scan
        )

    # LiDARの正規化
    lidar_normalized = lidar_scan / LIDAR_MAX_RANGE

    velocity = np.array(self._cached_vehicle_state["velocity"])
    angular_velocity = np.array([self._cached_vehicle_state["angular_velocity"]])

    # 観測を結合
    obs = np.concatenate([
        lidar_normalized,        # 5
        velocity / 3.0,          # 2（正規化）
        angular_velocity / 5.0,  # 1（正規化）
        self.last_action,        # 2
    ])

    return obs.astype(np.float32)
```

#### 問題点

1. **観測構築ロジックとノイズ適用が混在**
2. **正規化係数のハードコード** (`/ 3.0`, `/ 5.0`)
3. **観測空間の構成がコメントのみで表現** (自己説明的でない)

---

### 2.4 `render()` の問題点 (64行)

#### 問題箇所

レンダリングロジックが環境クラスに直接記述されており、以下の問題があります:

1. **環境管理とレンダリングの密結合**
2. **デバッグ情報の構築がrender内にある**
3. **チェックポイントの描画判定が環境状態に依存**

---

## 3. リファクタリング戦略

### 3.1 基本方針

1. **単一責任原則の適用**
   - 各クラスは1つの責務のみを持つ
   - メソッドは1つの機能のみを実行

2. **依存性の注入 (Dependency Injection)**
   - 報酬関数、観測ビルダーを外部から注入可能にする
   - テスト容易性の向上

3. **Strategy Pattern の適用**
   - 報酬計算をStrategyパターンで実装
   - 複数の報酬関数を組み合わせ可能にする

4. **Factory Pattern の適用**
   - Domain Randomization設定のファクトリー化
   - 初期化ロジックの簡素化

---

### 3.2 分離すべき責務

| 責務 | 新しいクラス/モジュール | 推定行数 |
|-----|----------------------|---------|
| **報酬計算** | `src/env/reward/` | 150行 |
| **観測空間構築** | `src/env/observation.py` | 80行 |
| **終了条件判定** | `src/env/termination.py` | 60行 |
| **Domain Randomization管理** | `src/env/randomization.py` | 100行 |
| **環境コア** | `src/env/minicar_env.py` | 250行 |

---

## 4. 新しいモジュール構成

### 4.1 ディレクトリ構造

```
src/env/
├── minicar_env.py              # リファクタリング後: 250行
├── observation.py              # 観測空間の構築 (NEW)
├── termination.py              # 終了条件の判定 (NEW)
├── randomization.py            # Domain Randomization管理 (NEW)
├── reward/                     # 報酬関数モジュール (NEW)
│   ├── __init__.py
│   ├── base.py                 # 基底クラス
│   ├── components.py           # 個別の報酬成分
│   ├── composite.py            # 複合報酬関数
│   └── factory.py              # 報酬関数のファクトリー
├── vehicle.py                  # 既存
├── sensors.py                  # 既存
├── course.py                   # 既存
└── renderer.py                 # 既存
```

---

## 5. 段階的実装計画

### Phase 1: 報酬関数の分離 (優先度: 🔴 最高)

**期間**: 2-3日
**目標**: 報酬計算ロジックを独立したモジュールに分離

#### ステップ 1.1: 基底クラスの作成

**ファイル**: `src/env/reward/base.py`

```python
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
```

#### ステップ 1.2: 個別報酬成分の実装

**ファイル**: `src/env/reward/components.py`

```python
"""個別の報酬成分の実装"""

import numpy as np
from .base import RewardComponent, RewardContext


class TimePenaltyReward(RewardComponent):
    """時間ペナルティ報酬

    早くゴールするインセンティブを与える。
    """

    def __init__(self, penalty_per_step: float = 0.7):
        """
        Args:
            penalty_per_step: 1ステップあたりのペナルティ
        """
        super().__init__(weight=1.0)
        self.penalty_per_step = penalty_per_step

    def compute(self, context: RewardContext) -> float:
        return -self.penalty_per_step


class DirectionReward(RewardComponent):
    """方向報酬（チェックポイント/ゴールへの誘導）

    次の目標地点（チェックポイントまたはゴール）への距離に基づいて報酬を与える。
    """

    def __init__(
        self,
        max_distance: float = 20.0,
        reward_scale: float = 0.7,
    ):
        """
        Args:
            max_distance: 距離の正規化に使う最大値（m）
            reward_scale: 報酬のスケール係数
        """
        super().__init__(weight=1.0)
        self.max_distance = max_distance
        self.reward_scale = reward_scale

    def compute(self, context: RewardContext) -> float:
        # 次のチェックポイントまたはゴールの位置を取得
        if context.next_checkpoint_index < len(context.checkpoints):
            target_pos = context.checkpoints[context.next_checkpoint_index]["position"]
        else:
            target_pos = context.goal_position

        # 目標までの距離
        distance = np.linalg.norm(
            np.array(context.position) - np.array(target_pos)
        )

        # 正規化（近いほど高報酬）
        normalized_distance = min(distance, self.max_distance)
        proximity = (self.max_distance - normalized_distance) / self.max_distance

        return proximity * self.reward_scale


class CheckpointReward(RewardComponent):
    """チェックポイント通過報酬

    注意: この報酬成分は副作用（next_checkpoint_indexの更新）を持つため、
    特別な扱いが必要。CompositeRewardで最後に計算されるべき。
    """

    def __init__(self, checkpoint_bonus: float = 200.0):
        """
        Args:
            checkpoint_bonus: チェックポイント通過時のボーナス
        """
        super().__init__(weight=1.0)
        self.checkpoint_bonus = checkpoint_bonus
        self._checkpoint_passed = False  # 通過フラグ

    def compute(self, context: RewardContext) -> float:
        # チェックポイント通過判定は外部で行う
        # ここでは通過したかどうかのフラグを受け取る
        self._checkpoint_passed = False
        return 0.0

    def check_and_reward(
        self,
        context: RewardContext,
        course,  # Courseオブジェクト
    ) -> tuple[float, bool]:
        """チェックポイント通過をチェックし、報酬と通過フラグを返す

        Args:
            context: 報酬コンテキスト
            course: Courseオブジェクト

        Returns:
            (reward, passed): 報酬値と通過フラグ
        """
        if context.next_checkpoint_index < len(context.checkpoints):
            if course.check_checkpoint(
                context.position,
                context.next_checkpoint_index
            ):
                return self.checkpoint_bonus, True

        return 0.0, False


class GoalReward(RewardComponent):
    """ゴール到達報酬

    全チェックポイントを通過してゴールに到達した場合の報酬。
    時間ボーナスも含む。
    """

    def __init__(
        self,
        goal_bonus: float = 500.0,
        time_bonus_scale: float = 2.0,
    ):
        """
        Args:
            goal_bonus: ゴール到達時の基本ボーナス
            time_bonus_scale: 時間ボーナスのスケール（remaining_steps * scale）
        """
        super().__init__(weight=1.0)
        self.goal_bonus = goal_bonus
        self.time_bonus_scale = time_bonus_scale

    def compute(self, context: RewardContext) -> float:
        # ゴール到達判定は外部で行う
        return 0.0

    def check_and_reward(
        self,
        context: RewardContext,
        course,  # Courseオブジェクト
    ) -> float:
        """ゴール到達をチェックし、報酬を返す

        Args:
            context: 報酬コンテキスト
            course: Courseオブジェクト

        Returns:
            報酬値
        """
        # 全チェックポイント通過済みか
        all_checkpoints_passed = (
            context.next_checkpoint_index == len(context.checkpoints)
        )

        # ゴール到達判定
        if all_checkpoints_passed and course.check_goal(context.position):
            # 基本ゴール報酬
            reward = self.goal_bonus

            # 時間ボーナス
            remaining_steps = context.max_steps - context.step_count
            time_bonus = remaining_steps * self.time_bonus_scale
            reward += time_bonus

            return reward

        return 0.0


class CollisionPenalty(RewardComponent):
    """衝突ペナルティ"""

    def __init__(self, penalty: float = -100.0):
        """
        Args:
            penalty: 衝突時のペナルティ（負の値）
        """
        super().__init__(weight=1.0)
        self.penalty = penalty

    def compute(self, context: RewardContext) -> float:
        if context.has_collision:
            return self.penalty
        return 0.0
```

#### ステップ 1.3: 複合報酬関数の実装

**ファイル**: `src/env/reward/composite.py`

```python
"""複合報酬関数の実装"""

from typing import List, Optional
from .base import RewardComponent, RewardContext
from .components import CheckpointReward, GoalReward


class CompositeReward:
    """複数の報酬成分を組み合わせた報酬関数

    Strategy Patternを使用し、報酬成分を柔軟に組み合わせることができる。
    """

    def __init__(
        self,
        components: List[RewardComponent],
        checkpoint_reward: Optional[CheckpointReward] = None,
        goal_reward: Optional[GoalReward] = None,
    ):
        """
        Args:
            components: 基本的な報酬成分のリスト
            checkpoint_reward: チェックポイント報酬（副作用あり）
            goal_reward: ゴール報酬（副作用あり）
        """
        self.components = components
        self.checkpoint_reward = checkpoint_reward
        self.goal_reward = goal_reward

    def compute(
        self,
        context: RewardContext,
        course,  # Courseオブジェクト
    ) -> tuple[float, bool]:
        """報酬を計算

        Args:
            context: 報酬コンテキスト
            course: Courseオブジェクト

        Returns:
            (total_reward, checkpoint_passed): 総報酬とチェックポイント通過フラグ
        """
        total_reward = 0.0
        checkpoint_passed = False

        # 基本的な報酬成分を計算
        for component in self.components:
            total_reward += component(context)

        # チェックポイント報酬（副作用: next_checkpoint_indexの更新）
        if self.checkpoint_reward is not None:
            cp_reward, checkpoint_passed = self.checkpoint_reward.check_and_reward(
                context, course
            )
            total_reward += cp_reward

        # ゴール報酬
        if self.goal_reward is not None:
            goal_reward_value = self.goal_reward.check_and_reward(context, course)
            total_reward += goal_reward_value

        return total_reward, checkpoint_passed


class AdaptiveCompositeReward(CompositeReward):
    """適応的報酬スケーリング対応の複合報酬関数

    AdaptiveRewardScalerと連携し、学習の進捗に応じて
    報酬係数を自動調整する。
    """

    def __init__(
        self,
        components: List[RewardComponent],
        checkpoint_reward: Optional[CheckpointReward] = None,
        goal_reward: Optional[GoalReward] = None,
        adaptive_scaler=None,  # AdaptiveRewardScaler
    ):
        """
        Args:
            components: 基本的な報酬成分のリスト
            checkpoint_reward: チェックポイント報酬
            goal_reward: ゴール報酬
            adaptive_scaler: 適応的報酬スケーラー（Noneの場合は固定係数）
        """
        super().__init__(components, checkpoint_reward, goal_reward)
        self.adaptive_scaler = adaptive_scaler

    def update_coefficients(self):
        """適応的スケーラーから係数を取得し、各報酬成分を更新"""
        if self.adaptive_scaler is None:
            return

        coeffs = self.adaptive_scaler.get_coefficients()

        # 各報酬成分の係数を更新
        for component in self.components:
            component_name = type(component).__name__

            if component_name == "TimePenaltyReward":
                component.penalty_per_step = coeffs.time_penalty
            elif component_name == "DirectionReward":
                component.reward_scale = coeffs.direction_reward_scale

        if self.checkpoint_reward is not None:
            self.checkpoint_reward.checkpoint_bonus = coeffs.checkpoint_reward

        if self.goal_reward is not None:
            self.goal_reward.goal_bonus = coeffs.goal_reward
            self.goal_reward.time_bonus_scale = coeffs.time_bonus_scale
```

#### ステップ 1.4: ファクトリーパターンの実装

**ファイル**: `src/env/reward/factory.py`

```python
"""報酬関数のファクトリー"""

from typing import Optional
from .composite import CompositeReward, AdaptiveCompositeReward
from .components import (
    TimePenaltyReward,
    DirectionReward,
    CheckpointReward,
    GoalReward,
    CollisionPenalty,
)


class RewardFactory:
    """報酬関数のファクトリークラス

    標準的な報酬関数の組み合わせを簡単に生成できる。
    """

    @staticmethod
    def create_default_reward(
        adaptive_scaler=None,
    ) -> CompositeReward:
        """デフォルトの報酬関数を作成

        Args:
            adaptive_scaler: 適応的報酬スケーラー（Noneの場合は固定係数）

        Returns:
            複合報酬関数
        """
        # 基本的な報酬成分
        components = [
            TimePenaltyReward(penalty_per_step=0.7),
            DirectionReward(max_distance=20.0, reward_scale=0.7),
            CollisionPenalty(penalty=-100.0),
        ]

        # チェックポイント報酬とゴール報酬
        checkpoint_reward = CheckpointReward(checkpoint_bonus=200.0)
        goal_reward = GoalReward(goal_bonus=500.0, time_bonus_scale=2.0)

        # 適応的スケーラーの有無で切り替え
        if adaptive_scaler is not None:
            reward_fn = AdaptiveCompositeReward(
                components=components,
                checkpoint_reward=checkpoint_reward,
                goal_reward=goal_reward,
                adaptive_scaler=adaptive_scaler,
            )
            # 初期係数を適用
            reward_fn.update_coefficients()
        else:
            reward_fn = CompositeReward(
                components=components,
                checkpoint_reward=checkpoint_reward,
                goal_reward=goal_reward,
            )

        return reward_fn

    @staticmethod
    def create_simple_reward() -> CompositeReward:
        """シンプルな報酬関数を作成（デバッグ用）

        Returns:
            複合報酬関数
        """
        components = [
            GoalReward(goal_bonus=100.0, time_bonus_scale=0.0),
            CollisionPenalty(penalty=-10.0),
        ]

        return CompositeReward(components=components)
```

---

### Phase 2: 観測空間の分離 (優先度: ⚠️ 高)

**期間**: 1-2日
**目標**: 観測空間の構築ロジックを独立したモジュールに分離

#### ステップ 2.1: ObservationBuilderの実装

**ファイル**: `src/env/observation.py`

```python
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
```

---

### Phase 3: 終了条件の分離 (優先度: ⚠️ 中)

**期間**: 1日
**目標**: 終了条件の判定ロジックを独立したモジュールに分離

#### ステップ 3.1: TerminationCheckerの実装

**ファイル**: `src/env/termination.py`

```python
"""終了条件の判定"""

from typing import Dict


class TerminationChecker:
    """終了条件のチェックを担当するクラス

    学習モードと本番モードで異なる終了条件を適用する。
    """

    def __init__(self, deployment_mode: bool = False):
        """
        Args:
            deployment_mode: 本番環境モード
                - False（学習モード）: ゴール到達・衝突で終了
                - True（本番モード）: 衝突のみ終了、ゴール到達は継続
        """
        self.deployment_mode = deployment_mode

    def check(
        self,
        vehicle_position: tuple,
        has_collision: bool,
        next_checkpoint_index: int,
        total_checkpoints: int,
        course,  # Courseオブジェクト
    ) -> tuple[bool, bool]:
        """終了条件をチェック

        Args:
            vehicle_position: 車両位置
            has_collision: 衝突フラグ
            next_checkpoint_index: 次のチェックポイントインデックス
            total_checkpoints: 総チェックポイント数
            course: Courseオブジェクト

        Returns:
            (terminated, is_collision): 終了フラグと衝突フラグ
        """
        # 本番環境モード: 衝突のみ終了判定
        if self.deployment_mode:
            if has_collision:
                return True, True
            return False, False

        # 学習モード: ゴール到達で終了
        all_checkpoints_passed = (next_checkpoint_index == total_checkpoints)
        if all_checkpoints_passed and course.check_goal(vehicle_position):
            return True, False

        # 壁衝突
        if has_collision:
            return True, True

        return False, False
```

---

### Phase 4: Domain Randomization管理の分離 (優先度: ⚠️ 中)

**期間**: 1日
**目標**: Domain Randomization設定のファクトリー化

#### ステップ 4.1: RandomizationManagerの実装

**ファイル**: `src/env/randomization.py`

```python
"""Domain Randomization管理"""

from typing import Optional, Dict
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


class RandomizationManager:
    """Domain Randomizationの管理を担当するクラス

    物理パラメータのランダム化とセンサーノイズの適用を管理する。
    """

    def __init__(
        self,
        enabled: bool = False,
        physics_config: Optional[PhysicsRandomizationConfig] = None,
        sensor_noise_config: Optional[SensorNoiseConfig] = None,
    ):
        """
        Args:
            enabled: Domain Randomizationを有効化
            physics_config: 物理ランダム化の設定（Noneの場合はデフォルト）
            sensor_noise_config: センサーノイズの設定（Noneの場合はデフォルト）
        """
        self.enabled = enabled

        if self.enabled:
            # 物理ランダム化
            self.physics_randomizer = PhysicsRandomizer(
                physics_config if physics_config is not None else DEFAULT_PHYSICS_CONFIG
            )

            # センサーノイズ
            self.sensor_noise_randomizer = SensorNoiseRandomizer(
                sensor_noise_config if sensor_noise_config is not None else DEFAULT_SENSOR_NOISE_CONFIG
            )

            print("[INFO] Domain Randomization enabled")
        else:
            self.physics_randomizer = None
            self.sensor_noise_randomizer = None

    def randomize_physics(self) -> Dict:
        """物理パラメータをランダム化

        Returns:
            ランダム化された物理パラメータの辞書
            Domain Randomizationが無効な場合は空辞書
        """
        if self.enabled and self.physics_randomizer is not None:
            return self.physics_randomizer.randomize()
        return {}

    def get_sensor_noise_randomizer(self):
        """センサーノイズランダマイザーを取得

        Returns:
            SensorNoiseRandomizer（無効な場合はNone）
        """
        if self.enabled:
            return self.sensor_noise_randomizer
        return None
```

---

### Phase 5: MinicarEnvのリファクタリング (優先度: 🔴 最高)

**期間**: 2-3日
**目標**: 上記のモジュールを使用して`MinicarEnv`を簡素化

#### ステップ 5.1: リファクタリング後のMinicarEnv

**ファイル**: `src/env/minicar_env.py`（リファクタリング後）

```python
"""Gym互換のミニカー環境（リファクタリング版）"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Tuple, Dict, Optional, Any

from src.physics.box2d_wrapper import PhysicsWorld
from src.physics.collision_listener import CollisionListener
from src.env.vehicle import Vehicle
from src.env.sensors import LiDARSensor, LIDAR_MAX_RANGE
from src.env.course import Course
from src.env.renderer import Renderer

# リファクタリング後のモジュール
from src.env.observation import ObservationBuilder, ObservationConfig
from src.env.termination import TerminationChecker
from src.env.randomization import RandomizationManager
from src.env.reward.factory import RewardFactory
from src.env.reward.base import RewardContext


class MinicarEnv(gym.Env):
    """ミニカーレースのGym互換環境（リファクタリング版）

    単一責任原則に基づき、各責務を専用モジュールに委譲:
    - 報酬計算: RewardFactory + CompositeReward
    - 観測構築: ObservationBuilder
    - 終了判定: TerminationChecker
    - Domain Randomization: RandomizationManager
    """

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    def __init__(
        self,
        course_file: str = "courses/easy/simple_oval.json",
        render_mode: Optional[str] = None,
        max_steps: int = 2000,
        deployment_mode: bool = False,
        # Domain Randomization
        enable_domain_randomization: bool = False,
        physics_randomization_config=None,
        sensor_noise_config=None,
        # Adaptive Reward Scaling
        adaptive_reward_scaler=None,
        # リファクタリング後の依存性注入（オプション）
        observation_builder: Optional[ObservationBuilder] = None,
        termination_checker: Optional[TerminationChecker] = None,
        randomization_manager: Optional[RandomizationManager] = None,
        reward_function=None,  # CompositeReward
    ):
        """
        Args:
            course_file: コース定義ファイル
            render_mode: 描画モード
            max_steps: 最大ステップ数
            deployment_mode: 本番環境モード
            enable_domain_randomization: Domain Randomization有効化
            physics_randomization_config: 物理ランダム化設定
            sensor_noise_config: センサーノイズ設定
            adaptive_reward_scaler: 適応的報酬スケーラー
            observation_builder: 観測ビルダー（Noneの場合はデフォルト作成）
            termination_checker: 終了条件チェッカー（Noneの場合はデフォルト作成）
            randomization_manager: ランダム化マネージャー（Noneの場合は設定から作成）
            reward_function: 報酬関数（Noneの場合はデフォルト作成）
        """
        super().__init__()

        self.render_mode = render_mode
        self.max_steps = max_steps
        self.deployment_mode = deployment_mode

        # Domain Randomization管理
        if randomization_manager is not None:
            self.randomization_manager = randomization_manager
        else:
            self.randomization_manager = RandomizationManager(
                enabled=enable_domain_randomization,
                physics_config=physics_randomization_config,
                sensor_noise_config=sensor_noise_config,
            )

        # 観測ビルダー
        if observation_builder is not None:
            self.obs_builder = observation_builder
        else:
            self.obs_builder = ObservationBuilder(
                config=ObservationConfig(),
                sensor_noise_randomizer=self.randomization_manager.get_sensor_noise_randomizer(),
            )

        # 終了条件チェッカー
        if termination_checker is not None:
            self.termination_checker = termination_checker
        else:
            self.termination_checker = TerminationChecker(deployment_mode=deployment_mode)

        # 報酬関数
        if reward_function is not None:
            self.reward_fn = reward_function
        else:
            self.reward_fn = RewardFactory.create_default_reward(
                adaptive_scaler=adaptive_reward_scaler
            )

        # コースのロード
        self.course = Course(course_file)

        # 衝突検出リスナー
        self.collision_listener = CollisionListener()

        # 物理世界
        self.world = PhysicsWorld(collision_listener=self.collision_listener)

        # 壁の作成
        self.course.create_walls(self.world.world)

        # 車両
        start_pos, start_angle = self.course.get_start_pose()
        self.vehicle = Vehicle(self.world.world, start_pos, start_angle)

        # LiDARセンサー
        self.lidar = LiDARSensor(
            self.world.world,
            num_rays=5,
            max_range=LIDAR_MAX_RANGE,
            angle_min=-np.pi/3,
            angle_max=np.pi/3
        )

        # レンダラー
        self.renderer = None
        if render_mode == "human":
            self.renderer = Renderer()

        # 行動空間
        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0]),
            high=np.array([1.0, 1.0]),
            dtype=np.float32,
        )

        # 観測空間
        obs_shape = self.obs_builder.get_observation_space_shape()
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=obs_shape, dtype=np.float32
        )

        # 状態
        self.step_count = 0
        self.last_action = np.zeros(2)
        self.total_reward = 0.0
        self.next_checkpoint_index = 0
        self.is_collision = False

        # キャッシュ
        self._cached_lidar_scan = None
        self._cached_vehicle_state = None

    def reset(
        self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """環境をリセット"""
        super().reset(seed=seed)

        # Domain Randomization: 物理パラメータをランダム化
        physics_params = self.randomization_manager.randomize_physics()

        # 車両をリセット
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

        # 状態をリセット
        self.step_count = 0
        self.last_action = np.zeros(2)
        self.total_reward = 0.0
        self.next_checkpoint_index = 0
        self.is_collision = False

        # 衝突検出リスナーをリセット
        self.world.reset_collision()

        # キャッシュを初期化
        state = self.vehicle.get_state()
        self._cached_vehicle_state = state
        self._cached_lidar_scan = self.lidar.scan(state["position"], state["angle"])

        # 初期観測
        obs = self._get_observation()
        info = self._get_info()

        return obs, info

    def step(
        self, action: np.ndarray
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """1ステップ実行"""
        # 行動を適用
        steering = float(action[0])
        throttle = float(action[1])
        self.vehicle.apply_control(steering, throttle)

        # 物理シミュレーション
        self.world.step()

        # 車両状態とLiDARスキャンをキャッシュ
        self._cached_vehicle_state = self.vehicle.get_state()
        self._cached_lidar_scan = self.lidar.scan(
            self._cached_vehicle_state["position"],
            self._cached_vehicle_state["angle"]
        )

        # 観測
        obs = self._get_observation()

        # 報酬計算
        reward, checkpoint_passed = self._compute_reward()
        self.total_reward += reward

        # チェックポイント通過時のインデックス更新
        if checkpoint_passed:
            self.next_checkpoint_index += 1

        # 終了判定
        terminated, collision = self._check_terminated()
        if collision:
            self.is_collision = True

        truncated = self.step_count >= self.max_steps

        # 情報
        info = self._get_info()

        # 状態更新
        self.last_action = action
        self.step_count += 1

        return obs, reward, terminated, truncated, info

    def _get_observation(self) -> np.ndarray:
        """観測を取得（ObservationBuilderに委譲）"""
        return self.obs_builder.build(
            lidar_scan=self._cached_lidar_scan,
            vehicle_state=self._cached_vehicle_state,
            last_action=self.last_action,
            lidar_sensor=self.lidar,
        )

    def _compute_reward(self) -> Tuple[float, bool]:
        """報酬を計算（CompositeRewardに委譲）"""
        # 報酬コンテキストを構築
        context = RewardContext(
            position=self._cached_vehicle_state["position"],
            velocity=self._cached_vehicle_state["velocity"],
            speed=self._cached_vehicle_state["speed"],
            angle=self._cached_vehicle_state["angle"],
            angular_velocity=self._cached_vehicle_state["angular_velocity"],
            lidar_scan=self._cached_lidar_scan,
            action=self.last_action,
            checkpoints=self.course.get_checkpoints(),
            next_checkpoint_index=self.next_checkpoint_index,
            goal_position=self.course.get_goal_info()[0],
            goal_radius=self.course.get_goal_info()[1],
            step_count=self.step_count,
            max_steps=self.max_steps,
            has_collision=self.world.has_collision(),
            deployment_mode=self.deployment_mode,
        )

        # 報酬を計算（checkpoint_passedフラグも取得）
        reward, checkpoint_passed = self.reward_fn.compute(context, self.course)

        return reward, checkpoint_passed

    def _check_terminated(self) -> Tuple[bool, bool]:
        """終了条件をチェック（TerminationCheckerに委譲）"""
        return self.termination_checker.check(
            vehicle_position=self._cached_vehicle_state["position"],
            has_collision=self.world.has_collision(),
            next_checkpoint_index=self.next_checkpoint_index,
            total_checkpoints=len(self.course.get_checkpoints()),
            course=self.course,
        )

    def _get_info(self) -> Dict[str, Any]:
        """追加情報を取得"""
        checkpoints = self.course.get_checkpoints()
        return {
            "position": self._cached_vehicle_state["position"],
            "speed": self._cached_vehicle_state["speed"],
            "angle": self._cached_vehicle_state["angle"],
            "step_count": self.step_count,
            "total_reward": self.total_reward,
            "next_checkpoint_index": self.next_checkpoint_index,
            "total_checkpoints": len(checkpoints),
            "checkpoints_remaining": len(checkpoints) - self.next_checkpoint_index,
            "min_distance": np.min(self._cached_lidar_scan),
            "is_collision": self.is_collision,
        }

    def render(self):
        """環境を描画（変更なし）"""
        if self.render_mode != "human":
            return

        if self.renderer is None:
            self.renderer = Renderer()

        # （既存のレンダリング処理）
        # ...

    def close(self):
        """リソースを解放"""
        if self.renderer is not None:
            self.renderer.close()
            self.renderer = None

    def load_course(self, course_file: str):
        """新しいコースをロード（変更なし）"""
        # （既存のコース切り替え処理）
        # ...
```

---

## 6. 後方互換性の維持

### 6.1 既存コードとの互換性

リファクタリング後も、既存の使用方法をサポートします:

```python
# 既存の使用方法（そのまま動作）
env = MinicarEnv(
    course_file="courses/easy/simple_oval.json",
    render_mode="human",
    max_steps=2000,
    enable_domain_randomization=True,
    adaptive_reward_scaler=scaler,
)

# 新しい使用方法（依存性注入）
from src.env.reward.factory import RewardFactory
from src.env.observation import ObservationBuilder
from src.env.termination import TerminationChecker

env = MinicarEnv(
    course_file="courses/easy/simple_oval.json",
    reward_function=RewardFactory.create_default_reward(),
    observation_builder=ObservationBuilder(),
    termination_checker=TerminationChecker(),
)
```

### 6.2 チェックポイントの互換性

既存の`.pth`ファイルはそのまま使用可能です（観測空間・行動空間は変更なし）。

---

## 7. テスト戦略

### 7.1 単体テストの追加

各モジュールに対して単体テストを追加します:

```
tests/
├── test_env/
│   ├── test_reward_components.py       # 各報酬成分のテスト
│   ├── test_composite_reward.py        # 複合報酬関数のテスト
│   ├── test_observation_builder.py     # 観測ビルダーのテスト
│   ├── test_termination_checker.py     # 終了条件チェッカーのテスト
│   └── test_randomization_manager.py   # ランダム化マネージャーのテスト
└── test_minicar_env_refactored.py      # リファクタリング後の統合テスト
```

#### 例: 報酬成分のテスト

**ファイル**: `tests/test_env/test_reward_components.py`

```python
"""報酬成分の単体テスト"""

import pytest
import numpy as np
from src.env.reward.base import RewardContext
from src.env.reward.components import (
    TimePenaltyReward,
    DirectionReward,
    CollisionPenalty,
)


def test_time_penalty_reward():
    """時間ペナルティ報酬のテスト"""
    reward_component = TimePenaltyReward(penalty_per_step=0.7)

    # ダミーのコンテキスト
    context = RewardContext(
        position=(0, 0),
        velocity=(0, 0),
        speed=0,
        angle=0,
        angular_velocity=0,
        lidar_scan=np.zeros(5),
        action=np.zeros(2),
        checkpoints=[],
        next_checkpoint_index=0,
        goal_position=(10, 10),
        goal_radius=1.0,
        step_count=0,
        max_steps=1000,
        has_collision=False,
    )

    # 報酬を計算
    reward = reward_component.compute(context)

    # ペナルティが正しいか確認
    assert reward == -0.7


def test_direction_reward():
    """方向報酬のテスト"""
    reward_component = DirectionReward(max_distance=20.0, reward_scale=1.0)

    # チェックポイントが近い場合
    context_near = RewardContext(
        position=(0, 0),
        velocity=(0, 0),
        speed=0,
        angle=0,
        angular_velocity=0,
        lidar_scan=np.zeros(5),
        action=np.zeros(2),
        checkpoints=[{"position": (5, 0), "radius": 1.0}],
        next_checkpoint_index=0,
        goal_position=(10, 10),
        goal_radius=1.0,
        step_count=0,
        max_steps=1000,
        has_collision=False,
    )

    reward_near = reward_component.compute(context_near)

    # チェックポイントが遠い場合
    context_far = RewardContext(
        position=(0, 0),
        velocity=(0, 0),
        speed=0,
        angle=0,
        angular_velocity=0,
        lidar_scan=np.zeros(5),
        action=np.zeros(2),
        checkpoints=[{"position": (20, 0), "radius": 1.0}],
        next_checkpoint_index=0,
        goal_position=(10, 10),
        goal_radius=1.0,
        step_count=0,
        max_steps=1000,
        has_collision=False,
    )

    reward_far = reward_component.compute(context_far)

    # 近い方が報酬が高い
    assert reward_near > reward_far


def test_collision_penalty():
    """衝突ペナルティのテスト"""
    reward_component = CollisionPenalty(penalty=-100.0)

    # 衝突なしの場合
    context_no_collision = RewardContext(
        position=(0, 0),
        velocity=(0, 0),
        speed=0,
        angle=0,
        angular_velocity=0,
        lidar_scan=np.zeros(5),
        action=np.zeros(2),
        checkpoints=[],
        next_checkpoint_index=0,
        goal_position=(10, 10),
        goal_radius=1.0,
        step_count=0,
        max_steps=1000,
        has_collision=False,
    )

    reward_no_collision = reward_component.compute(context_no_collision)
    assert reward_no_collision == 0.0

    # 衝突ありの場合
    context_collision = RewardContext(
        position=(0, 0),
        velocity=(0, 0),
        speed=0,
        angle=0,
        angular_velocity=0,
        lidar_scan=np.zeros(5),
        action=np.zeros(2),
        checkpoints=[],
        next_checkpoint_index=0,
        goal_position=(10, 10),
        goal_radius=1.0,
        step_count=0,
        max_steps=1000,
        has_collision=True,
    )

    reward_collision = reward_component.compute(context_collision)
    assert reward_collision == -100.0
```

### 7.2 統合テスト

リファクタリング前後で同じ挙動をすることを検証します:

```python
"""リファクタリング前後の挙動比較テスト"""

import pytest
import numpy as np
from src.env.minicar_env import MinicarEnv


def test_backward_compatibility():
    """後方互換性のテスト"""
    # リファクタリング後の環境を作成
    env = MinicarEnv(
        course_file="courses/easy/simple_oval.json",
        max_steps=100,
    )

    # 既存のインターフェースが動作することを確認
    obs, info = env.reset()

    assert obs.shape == (10,)
    assert "position" in info
    assert "total_reward" in info

    # ステップ実行
    action = np.array([0.0, 0.5])
    obs, reward, terminated, truncated, info = env.step(action)

    assert obs.shape == (10,)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
```

---

## 8. 実装の詳細

### 8.1 マイグレーションガイド

既存のコードを新しいアーキテクチャに移行する手順:

#### ステップ1: 報酬関数のカスタマイズ

**Before (リファクタリング前)**:

```python
# minicar_env.pyを直接編集
def _compute_reward(self) -> float:
    reward = 0.0
    # ... 報酬計算ロジックを直接編集
    return reward
```

**After (リファクタリング後)**:

```python
# 新しい報酬成分を作成
from src.env.reward.base import RewardComponent, RewardContext

class SpeedReward(RewardComponent):
    """速度報酬（カスタム）"""
    def compute(self, context: RewardContext) -> float:
        return context.speed * 0.1

# 報酬関数に追加
from src.env.reward.factory import RewardFactory
from src.env.reward.composite import CompositeReward

components = [
    TimePenaltyReward(),
    DirectionReward(),
    SpeedReward(),  # カスタム報酬を追加
    CollisionPenalty(),
]

reward_fn = CompositeReward(components=components)

# 環境に注入
env = MinicarEnv(reward_function=reward_fn)
```

#### ステップ2: 観測空間のカスタマイズ

**Before (リファクタリング前)**:

```python
# minicar_env.pyを直接編集
def _get_observation(self) -> np.ndarray:
    # ... 観測構築ロジックを直接編集
    return obs
```

**After (リファクタリング後)**:

```python
# カスタム観測ビルダーを作成
from src.env.observation import ObservationBuilder, ObservationConfig

class CustomObservationBuilder(ObservationBuilder):
    def build(self, lidar_scan, vehicle_state, last_action, lidar_sensor=None):
        # カスタム観測構築ロジック
        obs = super().build(lidar_scan, vehicle_state, last_action, lidar_sensor)
        # 追加の観測要素を結合
        # ...
        return obs

# 環境に注入
obs_builder = CustomObservationBuilder()
env = MinicarEnv(observation_builder=obs_builder)
```

---

### 8.2 パフォーマンス最適化

リファクタリング後もパフォーマンスを維持するための工夫:

1. **RewardContextのプリアロケーション**
   ```python
   # 毎ステップRewardContextを新規作成するとオーバーヘッドが大きい
   # 解決策: キャッシュ済みのコンテキストを更新する
   ```

2. **報酬成分の計算順序の最適化**
   ```python
   # 早期終了可能な報酬成分を先に計算
   # 例: 衝突ペナルティは最初に計算し、衝突時は他の計算をスキップ
   ```

---

### 8.3 デバッグ・ログ機能

リファクタリング後のデバッグを容易にするための機能:

```python
# 報酬成分ごとの内訳をログに出力
from src.env.reward.composite import CompositeReward

class DebugCompositeReward(CompositeReward):
    def compute(self, context, course):
        total_reward = 0.0

        print("=== Reward Breakdown ===")
        for component in self.components:
            reward_value = component(context)
            total_reward += reward_value
            print(f"{type(component).__name__}: {reward_value:.3f}")

        # ... チェックポイント、ゴール報酬の計算

        print(f"Total Reward: {total_reward:.3f}")
        print("=" * 24)

        return total_reward, checkpoint_passed
```

---

## 9. まとめ

### 9.1 期待される効果

| 指標 | リファクタリング前 | リファクタリング後 | 改善率 |
|-----|----------------|----------------|--------|
| `minicar_env.py`の行数 | 554行 | ~250行 | -55% |
| 報酬関数の変更コスト | 高（環境クラスを直接編集） | 低（新しい成分を追加） | -70% |
| 単体テスト可能性 | 低（環境全体のテストが必要） | 高（各モジュール独立） | +200% |
| 新規メンバーの理解時間 | 3-4時間 | 1-2時間 | -50% |

### 9.2 次のステップ

1. ✅ **Phase 1を実装** (報酬関数の分離)
2. ✅ **Phase 2を実装** (観測空間の分離)
3. ✅ **Phase 3を実装** (終了条件の分離)
4. ✅ **Phase 4を実装** (Domain Randomization管理の分離)
5. ✅ **Phase 5を実装** (MinicarEnvのリファクタリング)
6. ✅ **単体テストの追加**
7. ✅ **統合テストの実行**
8. ✅ **パフォーマンステスト**
9. ✅ **ドキュメントの更新**

---

**このリファクタリング計画は、段階的に実施することで、リスクを最小限に抑えながら、コードベースの保守性を大幅に向上させます。**
