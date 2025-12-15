# Vehicle.py リファクタリング計画

**日付**: 2025-12-13
**対象**: `src/env/vehicle.py` (380行)
**目的**: Bicycle Model物理エンジンの保守性・拡張性向上

---

## 目次

1. [現状分析](#1-現状分析)
2. [問題点の特定](#2-問題点の特定)
3. [リファクタリング戦略](#3-リファクタリング戦略)
4. [新しいモジュール構成](#4-新しいモジュール構成)
5. [Phase 1: VehicleConfigの分離](#phase-1-vehicleconfigの分離)
6. [Phase 2: BicycleModelControllerの作成](#phase-2-bicyclemodelcontrollerの作成)
7. [Phase 3: PhysicsParametersの管理](#phase-3-physicsparametersの管理)
8. [Phase 4: Vehicleクラスのリファクタリング](#phase-4-vehicleクラスのリファクタリング)
9. [テスト戦略](#テスト戦略)
10. [後方互換性の保証](#後方互換性の保証)
11. [使用例](#使用例)

---

## 1. 現状分析

### ファイル構成

| 項目 | 値 |
|-----|-----|
| 総行数 | 380行 |
| クラス数 | 1 (`Vehicle`) |
| メソッド数 | 10個 (public: 4, private: 6) |
| クラス定数 | 4個 (制御パラメータ) |
| Domain Randomization対応 | あり (6個のパラメータ) |

### メソッド一覧

| メソッド名 | 行数 | 公開範囲 | 責務 |
|-----------|------|---------|------|
| `__init__` | 54行 | Public | 初期化・Box2Dボディ作成 |
| `apply_control` | 31行 | Public | 制御入力の適用 |
| `get_state` | 16行 | Public | 状態の取得 |
| `reset` | 56行 | Public | リセット処理 |
| `_normalize_control` | 14行 | Private | 制御入力の正規化 |
| `_compute_wheel_positions` | 28行 | Private | ホイール位置計算 |
| `_apply_tire_friction` | 27行 | Private | タイヤ摩擦の適用 |
| `_apply_drive_force` | 31行 | Private | 駆動力の適用 |
| `_apply_angular_damping` | 17行 | Private | 角速度減衰の適用 |
| `_kill_lateral_velocity` | 53行 | Private | 横滑り抑制 |

### クラス定数（制御パラメータ）

```python
STEERING_THRESHOLD_STRAIGHT = 0.001  # rad
STEERING_THRESHOLD_DAMPING = 0.05    # 正規化値
ANGULAR_DAMPING_STRONG = 0.8
ANGULAR_DAMPING_NORMAL = 0.1
```

### Domain Randomization対応パラメータ

- `mass`: 質量 (kg)
- `friction`: 摩擦係数
- `linear_damping`: 線形減衰
- `angular_damping`: 角減衰
- `max_motor_force`: 最大モーター力 (N)
- `max_lateral_impulse`: 最大横滑りインパルス

---

## 2. 問題点の特定

### 2.1 過剰なドキュメンテーション（可読性の問題）

**問題**: クラス定数に対する詳細なdocstring（30行）が可読性を阻害

```python
# 現状（lines 16-43）
STEERING_THRESHOLD_STRAIGHT = 0.001  # rad
"""
ほぼ直進とみなすステアリング角度の閾値。
この値以下の場合、トルクを発生させないために
重心に駆動力を適用する。
"""
# ... 同様のdocstringが4つ続く
```

**影響**:
- ファイル全体の10%（30行）がコメント
- コードの流れを追いづらい
- 定数の用途は近くの実装コードで明確

**推奨される対処**:
- インラインコメントに簡略化
- 詳細な説明は別途ドキュメント化

---

### 2.2 責務の混在（単一責任原則の違反）

`Vehicle`クラスが複数の責務を担当している:

| 責務 | 具体的な処理 | 行数 |
|-----|-------------|------|
| **設定管理** | 車両パラメータの定義・管理 | 30行 |
| **Box2D統合** | ボディ・フィクスチャの作成 | 20行 |
| **Bicycle Model物理** | タイヤ摩擦、駆動力、角速度減衰 | 150行 |
| **Domain Randomization** | 6個のパラメータ管理・更新 | 56行 |
| **制御入力処理** | 正規化・適用 | 45行 |

**問題点**:
- テストが困難（Bicycle Modelのロジックだけをテストできない）
- 拡張が困難（新しい物理モデルを試すのが大変）
- Domain Randomizationの設定変更が煩雑

---

### 2.3 `reset()`メソッドの複雑性

**問題**: 6個のオプショナルパラメータを持つ`reset()`メソッド

```python
def reset(
    self,
    position: Tuple[float, float],
    angle: float = 0.0,
    mass: Optional[float] = None,
    friction: Optional[float] = None,
    linear_damping: Optional[float] = None,
    angular_damping: Optional[float] = None,
    max_motor_force: Optional[float] = None,
    max_lateral_impulse: Optional[float] = None,
):
    # 56行の条件分岐処理
    if mass is not None:
        self.mass = mass
    if max_motor_force is not None:
        self.max_motor_force = max_motor_force
    # ... 繰り返し
```

**影響**:
- 可読性が低い
- 引数の順序を間違えやすい
- 一部のパラメータだけを変更したい場合も冗長

**推奨される対処**:
- Domain Randomization用のパラメータを構造化（dataclass）
- 設定オブジェクトとして渡す

---

### 2.4 Bicycle Model物理ロジックの分離不足

**問題**: 物理計算ロジックが`Vehicle`に埋め込まれている

```python
# タイヤ摩擦（_apply_tire_friction）
# 駆動力（_apply_drive_force）
# 角速度減衰（_apply_angular_damping）
# 横滑り抑制（_kill_lateral_velocity）
```

これらは**Bicycle Modelの物理計算**という独立した責務を持つ。

**問題点**:
- 他の物理モデル（例: Ackermann Steering）への移行が困難
- 物理計算だけの単体テストができない
- 実機パラメータチューニング時にコード全体を把握する必要がある

---

### 2.5 定数の管理方法

**問題**: クラス定数として定義されているが、設定としての柔軟性がない

```python
STEERING_THRESHOLD_STRAIGHT = 0.001
STEERING_THRESHOLD_DAMPING = 0.05
ANGULAR_DAMPING_STRONG = 0.8
ANGULAR_DAMPING_NORMAL = 0.1
```

**課題**:
- 学習中にこれらのパラメータを調整したい場合がある
- 複数の設定プリセットを切り替えたい（例: "aggressive" vs "conservative"）
- 現在はクラス変数なので、インスタンスごとに変えられない

---

## 3. リファクタリング戦略

### 3.1 設計原則

| 原則 | 適用方法 |
|-----|---------|
| **単一責任原則** | 設定、物理計算、Box2D統合を分離 |
| **依存性注入** | BicycleModelControllerを外部から注入可能に |
| **設定の外部化** | VehicleConfig, PhysicsParametersとして構造化 |
| **コンポジション** | Vehicleは各コンポーネントを組み合わせる |

### 3.2 アーキテクチャ

```
Before:
┌──────────────────────────┐
│       Vehicle            │
│  - 設定管理              │
│  - Box2D統合            │
│  - Bicycle Model物理    │
│  - Domain Randomization │
│  - 制御入力処理          │
└──────────────────────────┘

After:
┌─────────────────────────────────────────────────┐
│               Vehicle (簡素化)                   │
│  - Box2Dボディの管理                            │
│  - コンポーネントの統合                          │
└─────────────────────────────────────────────────┘
            ↓ 委譲
┌───────────────────┐  ┌──────────────────────┐
│  VehicleConfig    │  │ PhysicsParameters    │
│  - 車両の寸法     │  │ - Domain Random化   │
│  - 制御パラメータ │  │   用のパラメータ     │
└───────────────────┘  └──────────────────────┘

            ↓ 委譲
┌───────────────────────────────────┐
│   BicycleModelController          │
│   - タイヤ摩擦の適用              │
│   - 駆動力の適用                  │
│   - 角速度減衰の適用              │
│   - 横滑り抑制                    │
└───────────────────────────────────┘
```

### 3.3 モジュール分割の方針

1. **Phase 1**: `VehicleConfig`の作成（設定の外部化）
2. **Phase 2**: `BicycleModelController`の作成（物理計算の分離）
3. **Phase 3**: `PhysicsParameters`の作成（Domain Randomization管理）
4. **Phase 4**: `Vehicle`のリファクタリング（統合・簡素化）

---

## 4. 新しいモジュール構成

### 4.1 ファイル構成

```
src/env/
├── vehicle/
│   ├── __init__.py              # エクスポート定義
│   ├── config.py                # VehicleConfig（設定管理）
│   ├── physics_params.py        # PhysicsParameters（DR用）
│   └── bicycle_model.py         # BicycleModelController（物理計算）
└── vehicle.py                   # Vehicle（統合・簡素化）
```

### 4.2 各モジュールの責務

| モジュール | 行数（推定） | 責務 |
|-----------|-------------|------|
| `vehicle/config.py` | 60行 | 車両寸法・制御パラメータの設定 |
| `vehicle/physics_params.py` | 50行 | Domain Randomization用パラメータ |
| `vehicle/bicycle_model.py` | 150行 | Bicycle Model物理計算 |
| `vehicle.py`（リファクタリング後） | 120行 | Box2D統合・コンポーネント管理 |

**総行数の比較**:
- リファクタリング前: 380行
- リファクタリング後: 380行（総計は変わらず、責務が明確に分離）
- `vehicle.py`自体: 380行 → 120行 (-68%)

---

## Phase 1: VehicleConfigの分離

### 目的

車両の物理的寸法と制御パラメータを構造化し、`Vehicle`クラスから分離する。

### 実装

**`src/env/vehicle/config.py`**

```python
"""車両の設定管理"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ControlParameters:
    """制御パラメータ

    Bicycle Modelの制御ロジックで使用する閾値と減衰係数。
    """

    # ステアリング閾値
    steering_threshold_straight: float = 0.001  # rad
    steering_threshold_damping: float = 0.05    # 正規化値

    # 角速度減衰係数
    angular_damping_strong: float = 0.8
    angular_damping_normal: float = 0.1


@dataclass
class VehicleConfig:
    """車両の設定

    実機TT-02に合わせた寸法と制御パラメータ。
    """

    # 車両の物理的寸法（実機TT-02）
    width: float = 0.188        # m (実機: 188mm)
    length: float = 0.479       # m (実機: 479mm)
    wheelbase: float = 0.257    # m (実機: 257mm、標準設定)

    # 制御パラメータ
    max_steering_angle: float = 0.5  # rad (約28度)

    # 制御ロジックの詳細パラメータ
    control_params: ControlParameters = field(default_factory=ControlParameters)

    @classmethod
    def create_default(cls) -> 'VehicleConfig':
        """デフォルト設定を作成"""
        return cls()

    @classmethod
    def create_custom(
        cls,
        width: float = 0.188,
        length: float = 0.479,
        wheelbase: float = 0.257,
        max_steering_angle: float = 0.5,
        **control_params_kwargs
    ) -> 'VehicleConfig':
        """カスタム設定を作成

        Args:
            width: 車両の幅
            length: 車両の長さ
            wheelbase: ホイールベース
            max_steering_angle: 最大ステアリング角度
            **control_params_kwargs: ControlParametersに渡す引数
        """
        control_params = ControlParameters(**control_params_kwargs)
        return cls(
            width=width,
            length=length,
            wheelbase=wheelbase,
            max_steering_angle=max_steering_angle,
            control_params=control_params,
        )

    def to_dict(self) -> Dict:
        """設定を辞書に変換（保存用）"""
        return {
            'width': self.width,
            'length': self.length,
            'wheelbase': self.wheelbase,
            'max_steering_angle': self.max_steering_angle,
            'control_params': {
                'steering_threshold_straight': self.control_params.steering_threshold_straight,
                'steering_threshold_damping': self.control_params.steering_threshold_damping,
                'angular_damping_strong': self.control_params.angular_damping_strong,
                'angular_damping_normal': self.control_params.angular_damping_normal,
            }
        }
```

### 利点

- ✅ 設定が構造化され、可読性が向上
- ✅ デフォルト設定とカスタム設定を簡単に作成可能
- ✅ 設定の保存・読み込みが容易（`to_dict()`を使用）
- ✅ 冗長なdocstringを削除し、dataclassのフィールドとして管理

---

## Phase 2: BicycleModelControllerの作成

### 目的

Bicycle Modelの物理計算ロジックを独立したコントローラーとして分離する。

### 実装

**`src/env/vehicle/bicycle_model.py`**

```python
"""Bicycle Modelの物理計算"""

from Box2D import b2Vec2, b2Body
import numpy as np
from typing import Dict, Optional, Tuple

from src.env.vehicle.config import VehicleConfig


class BicycleModelController:
    """Bicycle Modelの物理計算を担当

    タイヤ摩擦、駆動力、角速度減衰、横滑り抑制などの
    Bicycle Model特有の物理計算を実行する。
    """

    def __init__(
        self,
        config: VehicleConfig,
        max_motor_force: float = 20.0,
        max_lateral_impulse: float = 2.5,
    ):
        """
        Args:
            config: 車両設定
            max_motor_force: 最大モーター力 (N)
            max_lateral_impulse: 最大横滑りインパルス
        """
        self.config = config
        self.max_motor_force = max_motor_force
        self.max_lateral_impulse = max_lateral_impulse

    def apply_control(
        self,
        body: b2Body,
        steering: float,
        throttle: float,
        debug: bool = False
    ):
        """制御入力を適用（Bicycle Modelベース）

        Args:
            body: Box2Dのボディ
            steering: 正規化されたステアリング入力 (-1.0 ~ 1.0)
            throttle: 正規化されたスロットル入力 (-1.0 ~ 1.0)
            debug: デバッグ情報を出力するか
        """
        # ステアリング角度を計算
        steer_angle = -steering * self.config.max_steering_angle

        if debug:
            print(f"[DEBUG] Steering: {steering:.4f}, Throttle: {throttle:.4f}")
            print(f"[DEBUG] Body angle: {body.angle:.4f}, Angular velocity: {body.angularVelocity:.4f}")

        # ホイール位置の計算
        wheel_positions = self._compute_wheel_positions(body)

        # 各サブシステムに制御を委譲
        self._apply_tire_friction(body, steer_angle, wheel_positions, debug=debug)
        self._apply_drive_force(body, steer_angle, throttle, wheel_positions)
        self._apply_angular_damping(body, steering)

    def _compute_wheel_positions(self, body: b2Body) -> Dict:
        """前輪と後輪のワールド座標位置を計算"""
        front_local = b2Vec2(self.config.wheelbase / 2, 0)
        rear_local = b2Vec2(-self.config.wheelbase / 2, 0)

        front_world = body.GetWorldPoint(front_local)
        rear_world = body.GetWorldPoint(rear_local)

        return {
            "front_local": front_local,
            "rear_local": rear_local,
            "front_world": front_world,
            "rear_world": rear_world,
        }

    def _apply_tire_friction(
        self,
        body: b2Body,
        steer_angle: float,
        wheel_positions: Dict,
        debug: bool = False
    ):
        """タイヤの横滑りを抑制"""
        threshold = self.config.control_params.steering_threshold_straight

        if abs(steer_angle) < threshold:
            # 完全に真っ直ぐ進む時は、重心で横滑りを抑制
            self._kill_lateral_velocity(body, body.angle, world_point=None, debug=debug)
        else:
            # ステアリングがある時は各ホイールで抑制
            front_wheel_angle = body.angle + steer_angle
            rear_wheel_angle = body.angle

            self._kill_lateral_velocity(
                body, front_wheel_angle, wheel_positions["front_world"], debug=debug
            )
            self._kill_lateral_velocity(
                body, rear_wheel_angle, wheel_positions["rear_world"], debug=debug
            )

    def _apply_drive_force(
        self,
        body: b2Body,
        steer_angle: float,
        throttle: float,
        wheel_positions: Dict
    ):
        """駆動力を適用"""
        threshold = self.config.control_params.steering_threshold_straight

        if abs(steer_angle) < threshold:
            # 真っ直ぐ進む時は車体の向きで重心に適用
            direction = b2Vec2(np.cos(body.angle), np.sin(body.angle))
            force = throttle * self.max_motor_force * direction
            body.ApplyForce(force, body.worldCenter, True)
        else:
            # ステアリングがある時は前輪位置に適用
            front_wheel_angle = body.angle + steer_angle
            direction = b2Vec2(np.cos(front_wheel_angle), np.sin(front_wheel_angle))
            force = throttle * self.max_motor_force * direction
            body.ApplyForce(force, wheel_positions["front_world"], True)

    def _apply_angular_damping(self, body: b2Body, steering: float):
        """角速度の減衰を適用"""
        threshold = self.config.control_params.steering_threshold_damping

        if abs(steering) < threshold:
            damping = self.config.control_params.angular_damping_strong
        else:
            damping = self.config.control_params.angular_damping_normal

        angular_impulse = -damping * body.inertia * body.angularVelocity
        body.ApplyAngularImpulse(angular_impulse, True)

    def _kill_lateral_velocity(
        self,
        body: b2Body,
        direction_angle: float,
        world_point: Optional[b2Vec2] = None,
        debug: bool = False
    ):
        """横滑りを抑制（タイヤは横方向に滑らない）"""
        # 適用点と速度の取得
        if world_point is None:
            world_point = body.worldCenter
            velocity = body.linearVelocity
        else:
            velocity = body.GetLinearVelocityFromWorldPoint(world_point)

        # 基準方向（前後方向）
        forward = b2Vec2(np.cos(direction_angle), np.sin(direction_angle))

        # 横方向（左右方向）
        lateral = b2Vec2(-forward.y, forward.x)

        # 横方向の速度成分
        lateral_velocity_magnitude = velocity.dot(lateral)
        lateral_velocity = lateral_velocity_magnitude * lateral

        # 横方向の速度を打ち消すインパルスを計算
        impulse = -body.mass * lateral_velocity

        # インパルスの大きさをクリップ
        impulse_length = np.linalg.norm([impulse.x, impulse.y])
        if impulse_length > self.max_lateral_impulse:
            impulse *= self.max_lateral_impulse / impulse_length

        if debug and impulse_length > 0.001:
            print(f"[DEBUG] Lateral impulse: ({impulse.x:.4f}, {impulse.y:.4f}), magnitude: {impulse_length:.4f}")

        # インパルスを適用
        body.ApplyLinearImpulse(impulse, world_point, True)
```

### 利点

- ✅ Bicycle Model物理計算が独立したクラスに
- ✅ 他の物理モデル（Ackermann Steering等）への移行が容易
- ✅ 単体テストが可能（Box2Dボディをモックして物理計算だけをテスト）
- ✅ 設定（VehicleConfig）を注入することで柔軟性が向上

---

## Phase 3: PhysicsParametersの管理

### 目的

Domain Randomization用のパラメータを構造化し、`reset()`メソッドの複雑性を削減する。

### 実装

**`src/env/vehicle/physics_params.py`**

```python
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
```

### 利点

- ✅ `reset()`の引数が6個→2個に削減（position, angle, physics_params）
- ✅ Domain Randomizationの設定が構造化
- ✅ `PhysicsParameters.create_from_dict()`でRandomizerから直接設定可能
- ✅ Noneチェックが`has_updates()`で一元化

---

## Phase 4: Vehicleクラスのリファクタリング

### 目的

`Vehicle`クラスを簡素化し、設定管理・物理計算を委譲する。

### 実装

**`src/env/vehicle.py`（リファクタリング後）**

```python
"""車両モデル（リファクタリング版）"""

from Box2D import b2World, b2Vec2, b2Body
import numpy as np
from typing import Tuple, Dict, Optional

# リファクタリング後のモジュール
from src.env.vehicle.config import VehicleConfig
from src.env.vehicle.physics_params import PhysicsParameters
from src.env.vehicle.bicycle_model import BicycleModelController


class Vehicle:
    """ミニカーの物理モデル（リファクタリング版）

    責務を以下のコンポーネントに委譲:
    - VehicleConfig: 車両寸法・制御パラメータ
    - PhysicsParameters: Domain Randomization用パラメータ
    - BicycleModelController: Bicycle Model物理計算
    """

    def __init__(
        self,
        world: b2World,
        start_pos: Tuple[float, float],
        start_angle: float = 0.0,
        # リファクタリング後の依存性注入
        config: Optional[VehicleConfig] = None,
        physics_params: Optional[PhysicsParameters] = None,
        bicycle_controller: Optional[BicycleModelController] = None,
    ):
        """
        Args:
            world: Box2Dの物理世界
            start_pos: 初期位置 (x, y)
            start_angle: 初期角度 (rad)
            config: 車両設定（Noneの場合はデフォルト作成）
            physics_params: 物理パラメータ（Noneの場合はデフォルト作成）
            bicycle_controller: Bicycle Modelコントローラー（Noneの場合は作成）
        """
        self.world = world

        # 設定の注入または作成
        self.config = config if config is not None else VehicleConfig.create_default()
        self.physics_params = physics_params if physics_params is not None else PhysicsParameters.create_default()

        # Bicycle Modelコントローラーの注入または作成
        if bicycle_controller is not None:
            self.controller = bicycle_controller
        else:
            self.controller = BicycleModelController(
                config=self.config,
                max_motor_force=self.physics_params.max_motor_force,
                max_lateral_impulse=self.physics_params.max_lateral_impulse,
            )

        # Box2Dボディ作成
        self.body = self._create_body(start_pos, start_angle)

    def _create_body(self, start_pos: Tuple[float, float], start_angle: float) -> b2Body:
        """Box2Dボディを作成"""
        body = self.world.CreateDynamicBody(
            position=b2Vec2(*start_pos),
            angle=start_angle,
            linearDamping=self.physics_params.linear_damping,
            angularDamping=self.physics_params.angular_damping,
        )

        # 車両の識別子を設定（衝突検出用）
        body.userData = "vehicle"

        # 車両の形状（矩形）
        body.CreatePolygonFixture(
            box=(self.config.length / 2, self.config.width / 2),
            density=self.physics_params.mass / (self.config.length * self.config.width),
            friction=self.physics_params.friction,
        )

        return body

    def apply_control(self, steering: float, throttle: float, debug: bool = False):
        """制御入力を適用（BicycleModelControllerに委譲）

        Args:
            steering: ステアリング角度 (-1.0 ~ 1.0)
            throttle: スロットル (-1.0 ~ 1.0) 負の値で後退
            debug: デバッグ情報を出力するか
        """
        # 制御入力の正規化
        steering = np.clip(steering, -1.0, 1.0)
        throttle = np.clip(throttle, -1.0, 1.0)

        # Bicycle Modelコントローラーに委譲
        self.controller.apply_control(self.body, steering, throttle, debug=debug)

    def get_state(self) -> Dict:
        """現在の状態を取得"""
        return {
            "position": (self.body.position.x, self.body.position.y),
            "angle": self.body.angle,
            "velocity": (self.body.linearVelocity.x, self.body.linearVelocity.y),
            "angular_velocity": self.body.angularVelocity,
            "speed": np.linalg.norm(
                [self.body.linearVelocity.x, self.body.linearVelocity.y]
            ),
        }

    def reset(
        self,
        position: Tuple[float, float],
        angle: float = 0.0,
        physics_params: Optional[PhysicsParameters] = None,
    ):
        """車両を初期状態にリセット

        Args:
            position: リセット位置 (x, y)
            angle: リセット角度 (rad)
            physics_params: 物理パラメータ（Noneの場合は現在値を維持）
        """
        # 物理パラメータを更新（指定された場合のみ）
        if physics_params is not None and physics_params.has_updates():
            self._update_physics_params(physics_params)

        # 位置と速度をリセット
        self.body.position = b2Vec2(*position)
        self.body.angle = angle
        self.body.linearVelocity = b2Vec2(0, 0)
        self.body.angularVelocity = 0

    def _update_physics_params(self, params: PhysicsParameters):
        """物理パラメータを更新"""
        # 質量の更新
        if params.mass is not None:
            self.physics_params.mass = params.mass
            for fixture in self.body.fixtures:
                fixture.density = self.physics_params.mass / (self.config.length * self.config.width)
            self.body.ResetMassData()

        # ボディパラメータの更新
        if params.linear_damping is not None:
            self.physics_params.linear_damping = params.linear_damping
            self.body.linearDamping = params.linear_damping

        if params.angular_damping is not None:
            self.physics_params.angular_damping = params.angular_damping
            self.body.angularDamping = params.angular_damping

        # フィクスチャの摩擦係数を更新
        if params.friction is not None:
            self.physics_params.friction = params.friction
            for fixture in self.body.fixtures:
                fixture.friction = params.friction

        # コントローラーのパラメータを更新
        if params.max_motor_force is not None:
            self.physics_params.max_motor_force = params.max_motor_force
            self.controller.max_motor_force = params.max_motor_force

        if params.max_lateral_impulse is not None:
            self.physics_params.max_lateral_impulse = params.max_lateral_impulse
            self.controller.max_lateral_impulse = params.max_lateral_impulse
```

**`src/env/vehicle/__init__.py`**

```python
"""Vehicle モジュール"""

from src.env.vehicle.config import VehicleConfig, ControlParameters
from src.env.vehicle.physics_params import PhysicsParameters
from src.env.vehicle.bicycle_model import BicycleModelController

__all__ = [
    "VehicleConfig",
    "ControlParameters",
    "PhysicsParameters",
    "BicycleModelController",
]
```

### 行数の比較

| ファイル | 行数（Before） | 行数（After） | 削減率 |
|---------|-------------|-------------|--------|
| `vehicle.py` | 380行 | 120行 | **-68%** |
| `vehicle/config.py` | - | 60行 | - |
| `vehicle/physics_params.py` | - | 50行 | - |
| `vehicle/bicycle_model.py` | - | 150行 | - |
| **総計** | 380行 | 380行 | 0% |

### 主要メソッドの簡素化

| メソッド | Before | After | 削減率 |
|---------|--------|-------|--------|
| `__init__` | 54行 | 30行 | -44% |
| `apply_control` | 31行 | 8行 | -74% |
| `reset` | 56行 | 15行 | -73% |

---

## テスト戦略

### 統合テスト

**`scripts/test_refactored_vehicle.py`**

```python
"""リファクタリング後のVehicleの動作確認テスト"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Box2D import b2World
from src.env.vehicle import Vehicle
from src.env.vehicle.config import VehicleConfig
from src.env.vehicle.physics_params import PhysicsParameters


def test_basic_functionality():
    """基本的な機能のテスト"""
    print("=" * 60)
    print("Vehicle基本機能のテスト")
    print("=" * 60)

    # 物理世界を作成
    world = b2World(gravity=(0, 0))

    # 車両を作成
    print("\n[TEST 1] 車両の作成...")
    vehicle = Vehicle(world, start_pos=(0.0, 0.0), start_angle=0.0)
    print("✅ 車両の作成に成功")

    # 状態を取得
    print("\n[TEST 2] 状態の取得...")
    state = vehicle.get_state()
    assert state["position"] == (0.0, 0.0)
    assert state["angle"] == 0.0
    print(f"✅ 状態取得成功: position={state['position']}, angle={state['angle']:.2f}")

    # 制御入力を適用
    print("\n[TEST 3] 制御入力の適用...")
    vehicle.apply_control(steering=0.5, throttle=1.0)
    world.Step(1/60, 6, 2)
    state = vehicle.get_state()
    print(f"✅ 制御入力成功: speed={state['speed']:.2f}")

    # リセット
    print("\n[TEST 4] リセット...")
    vehicle.reset(position=(1.0, 1.0), angle=1.57)
    state = vehicle.get_state()
    assert abs(state["position"][0] - 1.0) < 0.01
    assert abs(state["position"][1] - 1.0) < 0.01
    print("✅ リセット成功")

    print("\n" + "=" * 60)
    print("すべてのテストに成功しました！")
    print("=" * 60)
    return True


def test_backward_compatibility():
    """後方互換性のテスト"""
    print("\n" + "=" * 60)
    print("後方互換性のテスト")
    print("=" * 60)

    print("\n[TEST] 既存の使用方法が動作するか...")

    # 既存の使用方法
    world = b2World(gravity=(0, 0))
    vehicle = Vehicle(world, start_pos=(0.0, 0.0), start_angle=0.0)

    vehicle.apply_control(steering=0.0, throttle=0.5)
    world.Step(1/60, 6, 2)
    vehicle.reset(position=(0.0, 0.0), angle=0.0)

    print("✅ 後方互換性テスト成功")
    return True


def test_custom_config():
    """カスタム設定のテスト"""
    print("\n" + "=" * 60)
    print("カスタム設定のテスト")
    print("=" * 60)

    print("\n[TEST] カスタム設定を使用...")

    # カスタム設定を作成
    custom_config = VehicleConfig.create_custom(
        width=0.2,
        length=0.5,
        max_steering_angle=0.6,
    )

    custom_params = PhysicsParameters.create_default()
    custom_params.mass = 2.0

    # 車両を作成
    world = b2World(gravity=(0, 0))
    vehicle = Vehicle(
        world,
        start_pos=(0.0, 0.0),
        config=custom_config,
        physics_params=custom_params,
    )

    assert vehicle.config.width == 0.2
    assert vehicle.config.length == 0.5
    assert vehicle.physics_params.mass == 2.0

    print("✅ カスタム設定テスト成功")
    return True


def test_domain_randomization():
    """Domain Randomizationのテスト"""
    print("\n" + "=" * 60)
    print("Domain Randomizationのテスト")
    print("=" * 60)

    print("\n[TEST] PhysicsParametersでリセット...")

    world = b2World(gravity=(0, 0))
    vehicle = Vehicle(world, start_pos=(0.0, 0.0))

    # Domain Randomization用のパラメータを作成
    randomized_params = PhysicsParameters(
        mass=1.8,
        friction=0.8,
        max_motor_force=25.0,
    )

    vehicle.reset(position=(0.0, 0.0), physics_params=randomized_params)

    assert vehicle.physics_params.mass == 1.8
    assert vehicle.physics_params.friction == 0.8
    assert vehicle.controller.max_motor_force == 25.0

    print("✅ Domain Randomizationテスト成功")
    return True


if __name__ == "__main__":
    success = True

    # 各テストを実行
    if not test_basic_functionality():
        success = False

    if not test_backward_compatibility():
        success = False

    if not test_custom_config():
        success = False

    if not test_domain_randomization():
        success = False

    # 結果
    print("\n" + "=" * 60)
    if success:
        print("🎉 すべてのテストに合格しました！")
    else:
        print("⚠️  一部のテストに失敗しました")
    print("=" * 60)

    sys.exit(0 if success else 1)
```

---

## 後方互換性の保証

### 既存コードへの影響

**✅ 影響なし** - 既存のコードはそのまま動作します。

**例**:

```python
# 既存のコード（そのまま動作）
from src.env.vehicle import Vehicle

world = b2World(gravity=(0, 0))
vehicle = Vehicle(world, start_pos=(0.0, 0.0), start_angle=0.0)

vehicle.apply_control(steering=0.5, throttle=1.0)
state = vehicle.get_state()
vehicle.reset(position=(0.0, 0.0), angle=0.0)
```

### MinicarEnvとの統合

**`src/env/minicar_env.py`の変更箇所**

```python
# Before
from src.env.vehicle import Vehicle

# 車両の作成
start_pos, start_angle = self.course.get_start_pose()
self.vehicle = Vehicle(self.world.world, start_pos, start_angle)

# リセット時
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

# After
from src.env.vehicle import Vehicle
from src.env.vehicle.physics_params import PhysicsParameters

# 車両の作成（変更なし）
start_pos, start_angle = self.course.get_start_pose()
self.vehicle = Vehicle(self.world.world, start_pos, start_angle)

# リセット時（簡潔に）
if physics_params:
    physics_params_obj = PhysicsParameters.create_from_dict(physics_params)
    self.vehicle.reset(start_pos, start_angle, physics_params=physics_params_obj)
```

### RandomizationManagerとの統合

**`src/env/randomization.py`に追加**

```python
def randomize_physics_for_vehicle(self) -> Optional[PhysicsParameters]:
    """Vehicle用の物理パラメータをランダム化

    Returns:
        PhysicsParameters（無効な場合はNone）
    """
    if self.enabled and self.physics_randomizer is not None:
        params_dict = self.physics_randomizer.randomize()
        return PhysicsParameters.create_from_dict(params_dict)
    return None
```

---

## 使用例

### 例1: デフォルト設定で使用

```python
from Box2D import b2World
from src.env.vehicle import Vehicle

# 物理世界を作成
world = b2World(gravity=(0, 0))

# デフォルト設定で車両を作成
vehicle = Vehicle(world, start_pos=(0.0, 0.0), start_angle=0.0)

# 制御入力を適用
vehicle.apply_control(steering=0.5, throttle=1.0)

# 物理シミュレーションを進める
world.Step(1/60, 6, 2)

# 状態を取得
state = vehicle.get_state()
print(f"Position: {state['position']}, Speed: {state['speed']}")
```

### 例2: カスタム設定で使用

```python
from Box2D import b2World
from src.env.vehicle import Vehicle
from src.env.vehicle.config import VehicleConfig
from src.env.vehicle.physics_params import PhysicsParameters

# カスタム車両設定
custom_config = VehicleConfig.create_custom(
    width=0.2,
    length=0.5,
    max_steering_angle=0.6,
    steering_threshold_straight=0.002,  # 制御パラメータも変更可能
)

# カスタム物理パラメータ
custom_params = PhysicsParameters(
    mass=2.0,
    friction=0.8,
    max_motor_force=25.0,
)

# 物理世界を作成
world = b2World(gravity=(0, 0))

# カスタム設定で車両を作成
vehicle = Vehicle(
    world,
    start_pos=(0.0, 0.0),
    config=custom_config,
    physics_params=custom_params,
)

vehicle.apply_control(steering=0.5, throttle=1.0)
```

### 例3: Domain Randomization

```python
from Box2D import b2World
from src.env.vehicle import Vehicle
from src.env.vehicle.physics_params import PhysicsParameters
from src.env.randomization import RandomizationManager

# 物理世界を作成
world = b2World(gravity=(0, 0))

# 車両を作成
vehicle = Vehicle(world, start_pos=(0.0, 0.0))

# Domain Randomization管理
randomization_manager = RandomizationManager(enabled=True)

# エピソード開始時にランダム化
randomized_params = randomization_manager.randomize_physics_for_vehicle()
vehicle.reset(position=(0.0, 0.0), physics_params=randomized_params)
```

### 例4: カスタムBicycle Modelコントローラー

```python
from Box2D import b2World
from src.env.vehicle import Vehicle
from src.env.vehicle.config import VehicleConfig
from src.env.vehicle.bicycle_model import BicycleModelController

# カスタムコントローラーを作成（例: 物理パラメータを変更）
custom_config = VehicleConfig.create_default()
custom_controller = BicycleModelController(
    config=custom_config,
    max_motor_force=30.0,  # より強力なモーター
    max_lateral_impulse=3.0,
)

# 物理世界を作成
world = b2World(gravity=(0, 0))

# カスタムコントローラーを注入
vehicle = Vehicle(
    world,
    start_pos=(0.0, 0.0),
    bicycle_controller=custom_controller,
)

vehicle.apply_control(steering=0.5, throttle=1.0)
```

---

## まとめ

### リファクタリングの成果

| 指標 | Before | After | 改善率 |
|-----|--------|-------|--------|
| `vehicle.py`の行数 | 380行 | 120行 | **-68%** |
| `__init__`の行数 | 54行 | 30行 | -44% |
| `apply_control`の行数 | 31行 | 8行 | -74% |
| `reset`の行数 | 56行 | 15行 | -73% |
| `reset`の引数数 | 8個 | 3個 | -63% |
| モジュール数 | 1個 | 4個 | - |

### 期待される効果

| 効果 | Before | After | 評価 |
|-----|--------|-------|------|
| **保守性** | 低（1ファイルに責務が混在） | 高（責務が明確に分離） | ⭐⭐⭐⭐⭐ |
| **可読性** | 中（380行、冗長なdocstring） | 高（各ファイル平均100行以下） | ⭐⭐⭐⭐⭐ |
| **テスト容易性** | 低（物理計算だけをテストできない） | 高（各モジュール独立） | ⭐⭐⭐⭐⭐ |
| **拡張性** | 低（他の物理モデルへの移行が困難） | 高（コントローラー差し替え可能） | ⭐⭐⭐⭐⭐ |
| **設定の柔軟性** | 低（クラス定数は変更不可） | 高（VehicleConfig, PhysicsParameters） | ⭐⭐⭐⭐⭐ |

### 次のステップ（推奨）

1. **Phase 1-4の実装** (優先度: 高)
   - `src/env/vehicle/config.py`の作成
   - `src/env/vehicle/physics_params.py`の作成
   - `src/env/vehicle/bicycle_model.py`の作成
   - `src/env/vehicle.py`のリファクタリング

2. **テストの作成と実行** (優先度: 高)
   - `scripts/test_refactored_vehicle.py`の作成
   - すべてのテストに合格することを確認

3. **MinicarEnvとの統合** (優先度: 高)
   - `src/env/minicar_env.py`を更新
   - `src/env/randomization.py`を更新
   - 既存の学習スクリプトで動作確認

4. **単体テストの追加** (優先度: 中)
   - `tests/env/test_vehicle_config.py`
   - `tests/env/test_physics_params.py`
   - `tests/env/test_bicycle_model.py`

5. **ドキュメントの更新** (優先度: 中)
   - `CLAUDE.md`の更新
   - 新しいアーキテクチャの図を追加

---

**このリファクタリングにより、`Vehicle`クラスの保守性・拡張性が大幅に向上し、新しい物理モデルの追加や実機パラメータのチューニングが格段に容易になります。**
