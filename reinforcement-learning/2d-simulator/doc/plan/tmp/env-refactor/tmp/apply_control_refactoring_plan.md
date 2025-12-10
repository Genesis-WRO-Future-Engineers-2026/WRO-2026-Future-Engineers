# apply_control メソッド リファクタリング実装計画

**作成日:** 2025-12-10
**対象:** `src/env/vehicle.py` の `apply_control` メソッド
**目的:** 可読性・保守性・テスト容易性の向上
**優先度:** 🟡 高
**推定作業時間:** 3時間

---

## 📋 目次

1. [現状分析](#現状分析)
2. [問題点の詳細](#問題点の詳細)
3. [リファクタリング方針](#リファクタリング方針)
4. [実装詳細](#実装詳細)
5. [段階的な実装手順](#段階的な実装手順)
6. [テスト戦略](#テスト戦略)
7. [リスクと対策](#リスクと対策)
8. [完了条件](#完了条件)

---

## 現状分析

### メソッド構成

#### `apply_control` メソッド (50-125行: 75行)

```python
def apply_control(self, steering: float, throttle: float, debug: bool = False):
    # 1. パラメータの正規化 (4行: 59-62)
    steering = np.clip(steering, -1.0, 1.0)
    throttle = np.clip(throttle, -1.0, 1.0)
    steer_angle = -steering * self.max_steering_angle

    # 2. ホイール位置の計算 (8行: 69-78)
    front_wheel_local = b2Vec2(self.wheelbase / 2, 0)
    rear_wheel_local = b2Vec2(-self.wheelbase / 2, 0)
    front_wheel_world = self.body.GetWorldPoint(front_wheel_local)
    rear_wheel_world = self.body.GetWorldPoint(rear_wheel_local)
    front_wheel_angle = self.body.angle + steer_angle
    rear_wheel_angle = self.body.angle

    # 3. デバッグ出力 (7行: 82-88)
    if debug:
        print(...)

    # 4. 横滑り抑制 (8行: 90-98)
    if abs(steer_angle) < 0.001:  # ← マジックナンバー
        self._kill_lateral_velocity_at_center(self.body.angle, debug=debug)
    else:
        self._kill_lateral_velocity(front_wheel_world, front_wheel_angle, debug=debug)
        self._kill_lateral_velocity(rear_wheel_world, rear_wheel_angle, debug=debug)

    # 5. 駆動力適用 (13行: 100-113)
    if abs(steer_angle) < 0.001:  # ← 同じ条件判定が再度出現
        drive_direction = b2Vec2(np.cos(self.body.angle), np.sin(self.body.angle))
        force = throttle * self.max_motor_force * drive_direction
        self.body.ApplyForce(force, self.body.worldCenter, True)
    else:
        front_direction = b2Vec2(np.cos(front_wheel_angle), np.sin(front_wheel_angle))
        force = throttle * self.max_motor_force * front_direction
        self.body.ApplyForce(force, front_wheel_world, True)

    # 6. 角速度減衰 (10行: 115-124)
    if abs(steering) < 0.05:  # ← マジックナンバー
        angular_damping = 0.8  # ← マジックナンバー
    else:
        angular_damping = 0.1  # ← マジックナンバー
    angular_impulse = -angular_damping * self.body.inertia * self.body.angularVelocity
    self.body.ApplyAngularImpulse(angular_impulse, True)
```

#### 補助メソッド

```python
# _kill_lateral_velocity_at_center (126-161行: 35行)
# _kill_lateral_velocity (163-199行: 36行)
```

この2つのメソッドは非常に似た実装を持つ（コード重複率: 約85%）

### コード行数の詳細

| セクション | 行数 | 責任 |
|-----------|------|------|
| パラメータ正規化 | 4 | 入力値の範囲制限 |
| ホイール位置計算 | 8 | 幾何学計算 |
| デバッグ出力 | 7 | ログ出力 |
| 横滑り抑制 | 8 | タイヤの物理特性シミュレーション |
| 駆動力適用 | 13 | エンジンの力をシミュレーション |
| 角速度減衰 | 10 | 回転の安定性制御 |
| **合計** | **50** | **6つの異なる責任** |

### サイクロマティック複雑度

```
apply_control メソッド: 複雑度 = 8
├─ if debug (82行)                    : +1
├─ if abs(steer_angle) < 0.001 (92行) : +1
├─ else (95行)                        : +1
├─ if abs(steer_angle) < 0.001 (102行): +1 ← 重複条件
├─ else (107行)                       : +1
├─ if abs(steering) < 0.05 (117行)    : +1
└─ else (120行)                       : +1

基本パス: 1
総複雑度: 8
```

**推奨値**: 5以下

---

## 問題点の詳細

### 🔴 1. 単一責任原則 (SRP) 違反

1つのメソッドが以下の6つの責任を持つ:

1. 入力の検証・正規化
2. 幾何学的計算（ホイール位置）
3. デバッグ情報の出力
4. タイヤの横滑り抑制
5. 駆動力の適用
6. 角速度の減衰

### 🔴 2. 同じ条件判定の重複

`abs(steer_angle) < 0.001` という判定が2箇所に登場:

- 92行: 横滑り抑制の分岐
- 102行: 駆動力適用の分岐

**問題点:**
- 閾値変更時に2箇所を修正する必要がある
- ロジックの一貫性が保証されない
- 条件の意図（"ほぼ直進とみなす"）が明確でない

### 🔴 3. マジックナンバーの多用

| 値 | 箇所 | 意味（推測） |
|---|------|-------------|
| `0.001` | 92, 102行 | ほぼ直進とみなすステアリング閾値 (rad) |
| `0.05` | 117行 | 強い角速度減衰を適用する閾値 |
| `0.8` | 119行 | 強い角速度減衰係数 |
| `0.1` | 122行 | 通常の角速度減衰係数 |

**問題点:**
- 値の根拠が不明
- チューニング時にどこを変更すべきか不明
- 単位やスケールが明記されていない

### 🔴 4. テストが困難

現状では以下のテストが不可能:

- 横滑り抑制ロジックだけをテストする
- 駆動力適用ロジックだけをテストする
- 角速度減衰ロジックだけをテストする

**理由:** すべてが1つのメソッドに結合されているため

### 🟡 5. デバッグコードの混在

`debug` パラメータと `if debug:` ブロックが本番コードに混在:

```python
if debug:
    print(f"[DEBUG] Steering: {steering:.4f}, Throttle: {throttle:.4f}")
    print(f"[DEBUG] Body angle: {self.body.angle:.4f}, ...")
    front_vel = self.body.GetLinearVelocityFromWorldPoint(front_wheel_world)
    rear_vel = self.body.GetLinearVelocityFromWorldPoint(rear_wheel_world)
    print(f"[DEBUG] Front wheel velocity: ...")
    print(f"[DEBUG] Rear wheel velocity: ...")
```

**問題点:**
- 本番コードの可読性を下げる
- 計算コストが常に発生（`if debug` 判定）
- ロギングフレームワークを使うべき

### 🟡 6. コード重複

`_kill_lateral_velocity_at_center` と `_kill_lateral_velocity` は85%同じコード:

```python
# 共通部分
vehicle_forward = b2Vec2(np.cos(angle), np.sin(angle))
vehicle_lateral = b2Vec2(-vehicle_forward.y, vehicle_forward.x)
lateral_velocity_magnitude = velocity.dot(vehicle_lateral)
lateral_velocity = lateral_velocity_magnitude * vehicle_lateral
impulse = -self.body.mass * lateral_velocity
impulse_length = np.linalg.norm([impulse.x, impulse.y])
if impulse_length > self.max_lateral_impulse:
    impulse *= self.max_lateral_impulse / impulse_length

# 唯一の違い
self.body.ApplyLinearImpulse(impulse, world_point, True)
#                                     ^^^^^^^^^^^
# - _kill_lateral_velocity_at_center: self.body.worldCenter
# - _kill_lateral_velocity:           引数で指定された world_point
```

---

## リファクタリング方針

### 基本戦略

**段階的リファクタリング (Incremental Refactoring)**

一度にすべてを変更せず、以下の順序で段階的に改善:

```
フェーズ1: 定数の抽出         (30分) ← 影響度: 低、効果: 高
    ↓
フェーズ2: メソッド分割         (1時間) ← 影響度: 中、効果: 高
    ↓
フェーズ3: 重複コードの統合     (45分) ← 影響度: 中、効果: 中
    ↓
フェーズ4: デバッグ機能の改善   (45分) ← 影響度: 低、効果: 中
```

各フェーズ後にテストを実行し、物理挙動が変わっていないことを確認。

### 設計原則

1. **単一責任原則 (SRP)**: 1メソッド = 1つの責任
2. **DRY原則**: コードの重複を排除
3. **開放閉鎖原則 (OCP)**: 拡張に開き、修正に閉じる
4. **明示的は暗黙的に勝る**: マジックナンバーを定数化

### 目標のメソッド構成

```python
class Vehicle:
    # ===== 定数定義 (物理パラメータ) =====
    STEERING_THRESHOLD_STRAIGHT = 0.001  # rad - ほぼ直進とみなす閾値
    STEERING_THRESHOLD_DAMPING = 0.05    # 正規化値 - 強い減衰を適用する閾値
    ANGULAR_DAMPING_STRONG = 0.8         # 強い角速度減衰係数
    ANGULAR_DAMPING_NORMAL = 0.1         # 通常の角速度減衰係数

    # ===== メインメソッド =====
    def apply_control(self, steering: float, throttle: float):
        """制御入力を適用 (15-20行)"""
        steering, throttle = self._normalize_control(steering, throttle)
        steer_angle = -steering * self.max_steering_angle

        wheel_positions = self._compute_wheel_positions()

        self._apply_tire_friction(steer_angle, wheel_positions)
        self._apply_drive_force(steer_angle, throttle, wheel_positions)
        self._apply_angular_damping(steering)

    # ===== サブシステムメソッド (各10-15行) =====
    def _normalize_control(self, steering, throttle) -> Tuple[float, float]:
        """入力の正規化"""

    def _compute_wheel_positions(self) -> Dict:
        """ホイール位置の計算"""

    def _apply_tire_friction(self, steer_angle, wheel_positions):
        """タイヤの横滑り抑制"""

    def _apply_drive_force(self, steer_angle, throttle, wheel_positions):
        """駆動力の適用"""

    def _apply_angular_damping(self, steering):
        """角速度の減衰"""

    def _kill_lateral_velocity(self, direction_angle, world_point=None):
        """横滑り抑制（統合版）"""
```

---

## 実装詳細

### フェーズ1: 定数の抽出 (30分)

#### ステップ1-1: 定数定義の追加

**場所:** `vehicle.py` の `__init__` メソッドの前（クラス変数として）

```python
class Vehicle:
    """ミニカーの物理モデル"""

    # ========================================
    # 制御パラメータ定数
    # ========================================

    # ステアリング閾値
    STEERING_THRESHOLD_STRAIGHT = 0.001  # rad
    """
    ほぼ直進とみなすステアリング角度の閾値。
    この値以下の場合、トルクを発生させないために
    重心に駆動力を適用する。
    """

    STEERING_THRESHOLD_DAMPING = 0.05  # 正規化値 (-1.0 ~ 1.0)
    """
    強い角速度減衰を適用するステアリング入力の閾値。
    この値以下の場合、回転を素早く止めるために
    ANGULAR_DAMPING_STRONG を適用する。
    """

    # 角速度減衰係数
    ANGULAR_DAMPING_STRONG = 0.8
    """
    強い角速度減衰係数。
    ステアリング入力が小さい時に適用され、
    回転を素早く止める。
    """

    ANGULAR_DAMPING_NORMAL = 0.1
    """
    通常の角速度減衰係数。
    ステアリング入力がある時に適用され、
    自然な旋回を可能にする。
    """

    def __init__(self, ...):
        # 既存のコード
```

#### ステップ1-2: マジックナンバーの置き換え

**場所:** `apply_control` メソッド内

```python
# ===== 修正前 =====
if abs(steer_angle) < 0.001:
    self._kill_lateral_velocity_at_center(self.body.angle, debug=debug)
else:
    # ...

if abs(steer_angle) < 0.001:
    # 駆動力を重心に適用
    # ...

if abs(steering) < 0.05:
    angular_damping = 0.8
else:
    angular_damping = 0.1

# ===== 修正後 =====
if abs(steer_angle) < self.STEERING_THRESHOLD_STRAIGHT:
    self._kill_lateral_velocity_at_center(self.body.angle, debug=debug)
else:
    # ...

if abs(steer_angle) < self.STEERING_THRESHOLD_STRAIGHT:
    # 駆動力を重心に適用
    # ...

if abs(steering) < self.STEERING_THRESHOLD_DAMPING:
    angular_damping = self.ANGULAR_DAMPING_STRONG
else:
    angular_damping = self.ANGULAR_DAMPING_NORMAL
```

#### テスト: フェーズ1

```bash
# 既存のテストを実行
python -m pytest tests/ -v

# または手動でシミュレーションを実行
python src/train.py --episodes 1 --render
```

**確認事項:**
- [ ] 車両の挙動が変わっていないか
- [ ] 直進性能が保たれているか
- [ ] 旋回性能が保たれているか

---

### フェーズ2: メソッド分割 (1時間)

#### ステップ2-1: `_normalize_control` メソッド

```python
def _normalize_control(self, steering: float, throttle: float) -> Tuple[float, float]:
    """
    制御入力を正規化（-1.0 ~ 1.0にクリップ）

    Args:
        steering: ステアリング入力（生の値）
        throttle: スロットル入力（生の値）

    Returns:
        (正規化されたステアリング, 正規化されたスロットル)
    """
    steering = np.clip(steering, -1.0, 1.0)
    throttle = np.clip(throttle, -1.0, 1.0)
    return steering, throttle
```

#### ステップ2-2: `_compute_wheel_positions` メソッド

```python
def _compute_wheel_positions(self) -> Dict:
    """
    前輪と後輪のワールド座標位置を計算

    Returns:
        {
            "front_local": b2Vec2,   # 前輪のローカル座標
            "rear_local": b2Vec2,    # 後輪のローカル座標
            "front_world": b2Vec2,   # 前輪のワールド座標
            "rear_world": b2Vec2,    # 後輪のワールド座標
        }
    """
    # 前輪と後輪の位置（ローカル座標系）
    front_local = b2Vec2(self.wheelbase / 2, 0)  # 車体前方
    rear_local = b2Vec2(-self.wheelbase / 2, 0)  # 車体後方

    # ワールド座標系に変換
    front_world = self.body.GetWorldPoint(front_local)
    rear_world = self.body.GetWorldPoint(rear_local)

    return {
        "front_local": front_local,
        "rear_local": rear_local,
        "front_world": front_world,
        "rear_world": rear_world,
    }
```

#### ステップ2-3: `_apply_tire_friction` メソッド

```python
def _apply_tire_friction(self, steer_angle: float, wheel_positions: Dict):
    """
    タイヤの横滑りを抑制

    Args:
        steer_angle: ステアリング角度 (rad)
        wheel_positions: _compute_wheel_positions() の戻り値
    """
    if abs(steer_angle) < self.STEERING_THRESHOLD_STRAIGHT:
        # 完全に真っ直ぐ進む時は、重心で横滑りを抑制（トルクなし）
        self._kill_lateral_velocity_at_center(self.body.angle)
    else:
        # ステアリングがある時は各ホイールで抑制
        front_wheel_angle = self.body.angle + steer_angle
        rear_wheel_angle = self.body.angle

        self._kill_lateral_velocity(
            wheel_positions["front_world"],
            front_wheel_angle
        )
        self._kill_lateral_velocity(
            wheel_positions["rear_world"],
            rear_wheel_angle
        )
```

#### ステップ2-4: `_apply_drive_force` メソッド

```python
def _apply_drive_force(
    self,
    steer_angle: float,
    throttle: float,
    wheel_positions: Dict
):
    """
    駆動力を適用

    Args:
        steer_angle: ステアリング角度 (rad)
        throttle: スロットル (-1.0 ~ 1.0)
        wheel_positions: _compute_wheel_positions() の戻り値
    """
    if abs(steer_angle) < self.STEERING_THRESHOLD_STRAIGHT:
        # 真っ直ぐ進む時は車体の向きで重心に適用（トルクなし）
        direction = b2Vec2(
            np.cos(self.body.angle),
            np.sin(self.body.angle)
        )
        force = throttle * self.max_motor_force * direction
        self.body.ApplyForce(force, self.body.worldCenter, True)
    else:
        # ステアリングがある時は前輪位置に適用（通常のBicycle Model）
        front_wheel_angle = self.body.angle + steer_angle
        direction = b2Vec2(
            np.cos(front_wheel_angle),
            np.sin(front_wheel_angle)
        )
        force = throttle * self.max_motor_force * direction
        self.body.ApplyForce(force, wheel_positions["front_world"], True)
```

#### ステップ2-5: `_apply_angular_damping` メソッド

```python
def _apply_angular_damping(self, steering: float):
    """
    角速度の減衰を適用（回転の安定性のため）

    ステアリング入力が小さい時は強い減衰を適用し、
    回転を素早く止める。

    Args:
        steering: 正規化されたステアリング入力 (-1.0 ~ 1.0)
    """
    if abs(steering) < self.STEERING_THRESHOLD_DAMPING:
        damping = self.ANGULAR_DAMPING_STRONG
    else:
        damping = self.ANGULAR_DAMPING_NORMAL

    angular_impulse = -damping * self.body.inertia * self.body.angularVelocity
    self.body.ApplyAngularImpulse(angular_impulse, True)
```

#### ステップ2-6: 新しい `apply_control` メソッド

```python
def apply_control(self, steering: float, throttle: float):
    """
    制御入力を適用（Bicycle Modelベース）

    Args:
        steering: ステアリング角度 (-1.0 ~ 1.0)
        throttle: スロットル (-1.0 ~ 1.0) 負の値で後退

    Note:
        後退時のステアリング反転は行わない（強化学習用途のため）
        Bicycle Modelの物理的な挙動に従う：
        - 前進時: 左入力 → 左回転
        - 後退時: 左入力 → 右回転（物理的に正しい挙動）
    """
    # 制御入力の正規化
    steering, throttle = self._normalize_control(steering, throttle)
    steer_angle = -steering * self.max_steering_angle

    # ホイール位置の計算
    wheel_positions = self._compute_wheel_positions()

    # 各サブシステムに制御を委譲
    self._apply_tire_friction(steer_angle, wheel_positions)
    self._apply_drive_force(steer_angle, throttle, wheel_positions)
    self._apply_angular_damping(steering)
```

#### テスト: フェーズ2

```bash
# 単体テストを実行
python -m pytest tests/test_vehicle.py::test_apply_control -v

# 統合テストを実行
python -m pytest tests/test_integration.py -v

# 挙動の目視確認
python src/train.py --episodes 1 --render
```

**確認事項:**
- [ ] すべてのユニットテストが成功
- [ ] 統合テストが成功
- [ ] 車両の挙動が変わっていないか（特に旋回と直進）
- [ ] パフォーマンスが劣化していないか

---

### フェーズ3: 重複コードの統合 (45分)

#### ステップ3-1: `_kill_lateral_velocity` の統合

```python
def _kill_lateral_velocity(
    self,
    direction_angle: float,
    world_point: Optional[b2Vec2] = None
):
    """
    横滑りを抑制（タイヤは横方向に滑らない）

    Args:
        direction_angle: 基準方向の角度（ワールド座標系、rad）
        world_point: インパルスを適用する位置。
                     Noneの場合は重心に適用（トルクなし）

    Note:
        world_pointがNoneの場合、重心での速度を使用し、
        重心にインパルスを適用するため、トルクが発生しない。
    """
    # 適用点と速度の取得
    if world_point is None:
        # 重心での処理（トルクなし）
        world_point = self.body.worldCenter
        velocity = self.body.linearVelocity
    else:
        # 指定位置での処理
        velocity = self.body.GetLinearVelocityFromWorldPoint(world_point)

    # 基準方向（前後方向）
    forward = b2Vec2(np.cos(direction_angle), np.sin(direction_angle))

    # 横方向（左右方向）
    lateral = b2Vec2(-forward.y, forward.x)

    # 横方向の速度成分
    lateral_velocity_magnitude = velocity.dot(lateral)

    # 横方向の速度ベクトル
    lateral_velocity = lateral_velocity_magnitude * lateral

    # 横方向の速度を打ち消すインパルスを計算
    impulse = -self.body.mass * lateral_velocity

    # インパルスの大きさをクリップ（安定性のため重要）
    impulse_length = np.linalg.norm([impulse.x, impulse.y])
    if impulse_length > self.max_lateral_impulse:
        impulse *= self.max_lateral_impulse / impulse_length

    # インパルスを適用
    self.body.ApplyLinearImpulse(impulse, world_point, True)
```

#### ステップ3-2: 古いメソッドの削除と呼び出し更新

```python
# ===== 削除 =====
# def _kill_lateral_velocity_at_center(self, vehicle_angle, debug=False):
#     ...
#
# def _kill_lateral_velocity(self, world_point, wheel_angle, debug=False):
#     ...

# ===== 呼び出し箇所の更新 =====

# _apply_tire_friction メソッド内
def _apply_tire_friction(self, steer_angle: float, wheel_positions: Dict):
    if abs(steer_angle) < self.STEERING_THRESHOLD_STRAIGHT:
        # 重心での横滑り抑制（トルクなし）
        self._kill_lateral_velocity(self.body.angle)  # world_point=None
    else:
        # 各ホイールでの横滑り抑制
        front_wheel_angle = self.body.angle + steer_angle
        rear_wheel_angle = self.body.angle

        self._kill_lateral_velocity(
            front_wheel_angle,
            wheel_positions["front_world"]
        )
        self._kill_lateral_velocity(
            rear_wheel_angle,
            wheel_positions["rear_world"]
        )
```

#### テスト: フェーズ3

```bash
# 横滑り抑制の単体テスト
python -m pytest tests/test_vehicle.py::test_kill_lateral_velocity -v

# 統合テスト
python -m pytest tests/test_integration.py -v

# 挙動確認
python src/train.py --episodes 1 --render
```

**確認事項:**
- [ ] 統合後の挙動が変わっていないか
- [ ] 直進時のトルク発生がないか
- [ ] 旋回時の横滑り抑制が機能しているか

---

### フェーズ4: デバッグ機能の改善 (45分)

#### ステップ4-1: ロギング機能の追加

```python
import logging

class Vehicle:
    def __init__(self, ...):
        # 既存のコード

        # ロガーの設定
        self.logger = logging.getLogger(__name__)

    def apply_control(self, steering: float, throttle: float):
        """制御入力を適用"""
        # 制御入力の正規化
        steering, throttle = self._normalize_control(steering, throttle)
        steer_angle = -steering * self.max_steering_angle

        # デバッグログ（DEBUG レベル）
        self.logger.debug(
            f"Control input: steering={steering:.4f}, throttle={throttle:.4f}, "
            f"steer_angle={steer_angle:.4f}"
        )

        # ホイール位置の計算
        wheel_positions = self._compute_wheel_positions()

        # 各サブシステムに制御を委譲
        self._apply_tire_friction(steer_angle, wheel_positions)
        self._apply_drive_force(steer_angle, throttle, wheel_positions)
        self._apply_angular_damping(steering)

        # 状態のログ（DEBUG レベル）
        self.logger.debug(
            f"Body state: angle={self.body.angle:.4f}, "
            f"angular_velocity={self.body.angularVelocity:.4f}"
        )
```

#### ステップ4-2: ロギング設定（オプション）

使用側でロギングレベルを制御:

```python
# train.py または minicar_env.py
import logging

# デバッグモード
if args.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
```

#### 後方互換性の維持（オプション）

既存の `debug` パラメータを残したい場合:

```python
def apply_control(self, steering: float, throttle: float, debug: bool = False):
    """制御入力を適用"""
    if debug:
        # デバッグモードの場合、一時的にログレベルを変更
        original_level = self.logger.level
        self.logger.setLevel(logging.DEBUG)

    try:
        # 既存のロジック
        steering, throttle = self._normalize_control(steering, throttle)
        # ...
    finally:
        if debug:
            self.logger.setLevel(original_level)
```

#### テスト: フェーズ4

```bash
# ロギングが機能することを確認
python src/train.py --episodes 1 --debug

# 通常モードで不要なログが出ないことを確認
python src/train.py --episodes 1
```

---

## 段階的な実装手順

### 全体の流れ

```
準備 (15分)
  ↓
フェーズ1: 定数の抽出 (30分)
  ├─ テスト実行
  ├─ 挙動確認
  └─ コミット
  ↓
フェーズ2: メソッド分割 (1時間)
  ├─ テスト実行
  ├─ 挙動確認
  └─ コミット
  ↓
フェーズ3: 重複コードの統合 (45分)
  ├─ テスト実行
  ├─ 挙動確認
  └─ コミット
  ↓
フェーズ4: デバッグ機能の改善 (45分)
  ├─ テスト実行
  ├─ 挙動確認
  └─ コミット
  ↓
最終確認 (15分)
```

### 準備

#### 1. ブランチ作成

```bash
git checkout -b refactor/apply-control-method
```

#### 2. ベースライン測定

```bash
# パフォーマンステスト
python scripts/benchmark_vehicle.py > baseline_performance.txt

# 挙動テスト
python src/train.py --episodes 1 --render --seed 42

# 挙動を動画で記録（オプション）
python scripts/record_behavior.py --output baseline_behavior.mp4
```

#### 3. テストコードの準備

後述の「テスト戦略」を参照し、テストコードを事前に作成。

---

## テスト戦略

### テストの種類

1. **ユニットテスト**: 各メソッドの機能を個別にテスト
2. **統合テスト**: メソッド間の連携をテスト
3. **回帰テスト**: リファクタリング前後で挙動が同じことを確認
4. **パフォーマンステスト**: 実行速度が劣化していないことを確認

### ユニットテスト

#### `test_vehicle.py`

```python
import pytest
import numpy as np
from Box2D import b2World
from src.env.vehicle import Vehicle


class TestVehicleRefactoring:
    """apply_control リファクタリングのテスト"""

    @pytest.fixture
    def world(self):
        """Box2D ワールドを作成"""
        return b2World(gravity=(0, 0), doSleep=True)

    @pytest.fixture
    def vehicle(self, world):
        """車両インスタンスを作成"""
        return Vehicle(world, start_pos=(0, 0), start_angle=0)

    # ===== フェーズ1のテスト =====

    def test_constants_defined(self, vehicle):
        """定数が正しく定義されているか"""
        assert hasattr(vehicle, "STEERING_THRESHOLD_STRAIGHT")
        assert hasattr(vehicle, "STEERING_THRESHOLD_DAMPING")
        assert hasattr(vehicle, "ANGULAR_DAMPING_STRONG")
        assert hasattr(vehicle, "ANGULAR_DAMPING_NORMAL")

        # 値の妥当性チェック
        assert 0 < vehicle.STEERING_THRESHOLD_STRAIGHT < 0.1
        assert 0 < vehicle.STEERING_THRESHOLD_DAMPING < 0.5
        assert 0 < vehicle.ANGULAR_DAMPING_STRONG <= 1.0
        assert 0 < vehicle.ANGULAR_DAMPING_NORMAL <= 1.0

    # ===== フェーズ2のテスト =====

    def test_normalize_control(self, vehicle):
        """制御入力の正規化"""
        # 範囲内の値
        s, t = vehicle._normalize_control(0.5, 0.8)
        assert s == 0.5
        assert t == 0.8

        # 範囲外の値（クリップされる）
        s, t = vehicle._normalize_control(1.5, -2.0)
        assert s == 1.0
        assert t == -1.0

        s, t = vehicle._normalize_control(-1.5, 2.0)
        assert s == -1.0
        assert t == 1.0

    def test_compute_wheel_positions(self, vehicle):
        """ホイール位置の計算"""
        positions = vehicle._compute_wheel_positions()

        # 必要なキーが存在するか
        assert "front_local" in positions
        assert "rear_local" in positions
        assert "front_world" in positions
        assert "rear_world" in positions

        # ローカル座標での距離が wheelbase と一致するか
        front = positions["front_local"]
        rear = positions["rear_local"]
        distance = np.sqrt((front.x - rear.x)**2 + (front.y - rear.y)**2)
        assert np.isclose(distance, vehicle.wheelbase, rtol=1e-5)

        # ワールド座標での距離も同じはず（回転していないので）
        front_w = positions["front_world"]
        rear_w = positions["rear_world"]
        distance_w = np.sqrt((front_w.x - rear_w.x)**2 + (front_w.y - rear_w.y)**2)
        assert np.isclose(distance_w, vehicle.wheelbase, rtol=1e-5)

    def test_apply_tire_friction(self, vehicle, world):
        """タイヤの横滑り抑制"""
        # 初期状態: 静止
        assert vehicle.body.linearVelocity.length == 0

        # 横方向に速度を与える
        vehicle.body.linearVelocity = (0, 1.0)  # y方向（横方向）

        # ホイール位置を計算
        wheel_positions = vehicle._compute_wheel_positions()

        # 直進状態での横滑り抑制
        vehicle._apply_tire_friction(0.0, wheel_positions)

        # ワールドをステップ（力が適用される）
        world.Step(1/60, 6, 2)

        # 横方向の速度が減少しているはず
        assert abs(vehicle.body.linearVelocity.y) < 1.0

    def test_apply_drive_force(self, vehicle, world):
        """駆動力の適用"""
        # 初期状態: 静止
        initial_speed = vehicle.get_state()["speed"]
        assert initial_speed == 0

        # ホイール位置を計算
        wheel_positions = vehicle._compute_wheel_positions()

        # 前進指令
        vehicle._apply_drive_force(0.0, 1.0, wheel_positions)

        # ワールドをステップ
        for _ in range(10):
            world.Step(1/60, 6, 2)

        # 速度が増加しているはず
        final_speed = vehicle.get_state()["speed"]
        assert final_speed > 0

    def test_apply_angular_damping(self, vehicle, world):
        """角速度の減衰"""
        # 初期角速度を与える
        vehicle.body.angularVelocity = 1.0  # rad/s

        # 小さいステアリング入力（強い減衰）
        vehicle._apply_angular_damping(0.01)
        world.Step(1/60, 6, 2)

        angular_vel_strong = vehicle.body.angularVelocity

        # 角速度をリセット
        vehicle.body.angularVelocity = 1.0

        # 大きいステアリング入力（通常の減衰）
        vehicle._apply_angular_damping(0.5)
        world.Step(1/60, 6, 2)

        angular_vel_normal = vehicle.body.angularVelocity

        # 強い減衰の方が角速度の減少が大きいはず
        assert angular_vel_strong < angular_vel_normal

    # ===== フェーズ3のテスト =====

    def test_kill_lateral_velocity_at_center(self, vehicle, world):
        """重心での横滑り抑制（トルクなし）"""
        # 横方向に速度を与える
        vehicle.body.linearVelocity = (0, 1.0)
        initial_angular_velocity = vehicle.body.angularVelocity

        # 重心での横滑り抑制
        vehicle._kill_lateral_velocity(vehicle.body.angle)
        world.Step(1/60, 6, 2)

        # 横方向の速度が減少
        assert abs(vehicle.body.linearVelocity.y) < 1.0

        # 角速度は変わらない（トルクなし）
        assert vehicle.body.angularVelocity == initial_angular_velocity

    def test_kill_lateral_velocity_at_wheel(self, vehicle, world):
        """ホイール位置での横滑り抑制"""
        # 横方向に速度を与える
        vehicle.body.linearVelocity = (0, 1.0)

        # 前輪位置での横滑り抑制
        wheel_positions = vehicle._compute_wheel_positions()
        vehicle._kill_lateral_velocity(
            vehicle.body.angle,
            wheel_positions["front_world"]
        )
        world.Step(1/60, 6, 2)

        # 横方向の速度が減少
        assert abs(vehicle.body.linearVelocity.y) < 1.0

    # ===== 統合テスト =====

    def test_apply_control_straight(self, vehicle, world):
        """直進制御"""
        # 直進指令
        for _ in range(100):
            vehicle.apply_control(steering=0.0, throttle=1.0)
            world.Step(1/60, 6, 2)

        state = vehicle.get_state()

        # x方向に進んでいる
        assert state["position"][0] > 0

        # y方向はほとんど動いていない
        assert abs(state["position"][1]) < 0.1

        # 角度はほとんど変わっていない
        assert abs(state["angle"]) < 0.1

    def test_apply_control_turn_left(self, vehicle, world):
        """左旋回制御"""
        # 左旋回指令
        for _ in range(100):
            vehicle.apply_control(steering=1.0, throttle=1.0)
            world.Step(1/60, 6, 2)

        state = vehicle.get_state()

        # 前進している
        assert state["speed"] > 0

        # 左に旋回している（正の角速度）
        assert state["angle"] > 0

    def test_apply_control_turn_right(self, vehicle, world):
        """右旋回制御"""
        # 右旋回指令
        for _ in range(100):
            vehicle.apply_control(steering=-1.0, throttle=1.0)
            world.Step(1/60, 6, 2)

        state = vehicle.get_state()

        # 前進している
        assert state["speed"] > 0

        # 右に旋回している（負の角速度）
        assert state["angle"] < 0

    def test_apply_control_backward(self, vehicle, world):
        """後退制御"""
        # 後退指令
        for _ in range(100):
            vehicle.apply_control(steering=0.0, throttle=-1.0)
            world.Step(1/60, 6, 2)

        state = vehicle.get_state()

        # x方向の負の方向に進んでいる
        assert state["position"][0] < 0

        # 速度がある
        assert state["speed"] > 0
```

### 回帰テスト

#### `test_regression.py`

```python
import pytest
import numpy as np
from Box2D import b2World
from src.env.vehicle import Vehicle


class TestRegressionVehicle:
    """リファクタリング前後で挙動が変わっていないことを確認"""

    # 基準となる軌跡データ（リファクタリング前に取得）
    BASELINE_TRAJECTORY = [
        # (time, x, y, angle, speed)
        # このデータはリファクタリング前に実際に実行して取得する
    ]

    @pytest.fixture
    def world(self):
        return b2World(gravity=(0, 0), doSleep=True)

    @pytest.fixture
    def vehicle(self, world):
        np.random.seed(42)  # 再現性のため
        return Vehicle(world, start_pos=(0, 0), start_angle=0)

    def test_trajectory_consistency(self, vehicle, world):
        """軌跡の一貫性テスト"""
        # 同じ制御入力シーケンスを適用
        control_sequence = [
            (0.0, 1.0),   # 直進
            (0.5, 1.0),   # 左旋回
            (-0.5, 1.0),  # 右旋回
            (0.0, -1.0),  # 後退
        ]

        trajectory = []
        time = 0.0
        dt = 1/60

        for steering, throttle in control_sequence:
            for _ in range(50):  # 各制御を50ステップ
                vehicle.apply_control(steering, throttle)
                world.Step(dt, 6, 2)

                state = vehicle.get_state()
                trajectory.append((
                    time,
                    state["position"][0],
                    state["position"][1],
                    state["angle"],
                    state["speed"]
                ))
                time += dt

        # ベースラインと比較（実際のベースラインデータが必要）
        # ここでは形式だけ示す
        if self.BASELINE_TRAJECTORY:
            for i, (t_base, x_base, y_base, a_base, s_base) in enumerate(self.BASELINE_TRAJECTORY):
                t, x, y, a, s = trajectory[i]

                assert np.isclose(x, x_base, rtol=0.01, atol=0.01)
                assert np.isclose(y, y_base, rtol=0.01, atol=0.01)
                assert np.isclose(a, a_base, rtol=0.01, atol=0.01)
                assert np.isclose(s, s_base, rtol=0.01, atol=0.01)
```

### パフォーマンステスト

#### `benchmark_vehicle.py`

```python
import time
import numpy as np
from Box2D import b2World
from src.env.vehicle import Vehicle


def benchmark_apply_control(iterations: int = 10000):
    """apply_control のパフォーマンスをベンチマーク"""
    world = b2World(gravity=(0, 0), doSleep=True)
    vehicle = Vehicle(world, start_pos=(0, 0), start_angle=0)

    # ウォームアップ
    for _ in range(100):
        vehicle.apply_control(0.5, 1.0)
        world.Step(1/60, 6, 2)

    # ベンチマーク
    start_time = time.time()

    for i in range(iterations):
        steering = np.sin(i * 0.01)
        throttle = np.cos(i * 0.01)
        vehicle.apply_control(steering, throttle)
        world.Step(1/60, 6, 2)

    elapsed = time.time() - start_time

    print(f"Iterations: {iterations}")
    print(f"Total time: {elapsed:.4f} s")
    print(f"Time per iteration: {elapsed / iterations * 1000:.4f} ms")
    print(f"Iterations per second: {iterations / elapsed:.2f}")


if __name__ == "__main__":
    benchmark_apply_control()
```

---

## リスクと対策

### 高リスク

| リスク | 影響 | 発生確率 | 対策 |
|-------|------|---------|------|
| メソッド分割で物理挙動が変わる | 🔴 大 | 🟢 低 | - 段階的リファクタリング<br>- 各段階でテスト<br>- 回帰テストの実施 |
| 横滑り抑制の統合でトルクが発生 | 🔴 大 | 🟡 中 | - 重心適用の場合は明示的に `world_point=None`<br>- ユニットテストで検証 |

### 中リスク

| リスク | 影響 | 発生確率 | 対策 |
|-------|------|---------|------|
| パフォーマンスの劣化 | 🟡 中 | 🟢 低 | - メソッド呼び出しオーバーヘッドは無視できるレベル<br>- ベンチマークで確認 |
| 定数の値が不適切 | 🟡 中 | 🟢 低 | - 既存の値をそのまま使用<br>- コメントで意図を明記 |

### 低リスク

| リスク | 影響 | 発生確率 | 対策 |
|-------|------|---------|------|
| ロギング機能の追加で実行速度が低下 | 🟢 小 | 🟢 低 | - DEBUG レベルは本番では無効<br>- パフォーマンステストで確認 |
| テストコードの保守コスト | 🟢 小 | 🟡 中 | - 重要なテストに絞る<br>- 自動テストで効率化 |

---

## 完了条件

### 機能要件

- [ ] `apply_control` メソッドが30行以下
- [ ] サイクロマティック複雑度が5以下
- [ ] 各サブメソッドが10-20行
- [ ] マジックナンバーがすべて定数化
- [ ] コード重複が解消（`_kill_lateral_velocity` の統合）

### 品質要件

- [ ] すべてのユニットテストが成功
- [ ] すべての統合テストが成功
- [ ] 回帰テストが成功（挙動が変わっていない）
- [ ] パフォーマンステストが成功（10%以内の変動）
- [ ] コードレビューを通過

### ドキュメント要件

- [ ] 各メソッドに docstring が記述されている
- [ ] 定数にコメントが記述されている
- [ ] README に変更内容を記載
- [ ] CHANGELOG を更新

### Git要件

- [ ] 各フェーズごとにコミット
- [ ] コミットメッセージが明確
- [ ] 最終的に main ブランチにマージ

---

## チェックリスト

### フェーズ1: 定数の抽出

- [ ] クラス定数を定義
- [ ] `STEERING_THRESHOLD_STRAIGHT` を定義
- [ ] `STEERING_THRESHOLD_DAMPING` を定義
- [ ] `ANGULAR_DAMPING_STRONG` を定義
- [ ] `ANGULAR_DAMPING_NORMAL` を定義
- [ ] 各定数に docstring を記述
- [ ] `apply_control` 内のマジックナンバーを置き換え
- [ ] テストを実行して成功を確認
- [ ] 挙動を目視確認
- [ ] コミット: `refactor: Extract magic numbers to class constants in Vehicle`

### フェーズ2: メソッド分割

- [ ] `_normalize_control` メソッドを実装
- [ ] `_compute_wheel_positions` メソッドを実装
- [ ] `_apply_tire_friction` メソッドを実装
- [ ] `_apply_drive_force` メソッドを実装
- [ ] `_apply_angular_damping` メソッドを実装
- [ ] 新しい `apply_control` メソッドを実装
- [ ] 古い `apply_control` をバックアップ（コメントアウト）
- [ ] ユニットテストを実装
- [ ] すべてのテストが成功
- [ ] 挙動を目視確認
- [ ] コミット: `refactor: Split apply_control into smaller methods`

### フェーズ3: 重複コードの統合

- [ ] 新しい `_kill_lateral_velocity` を実装（world_point オプション）
- [ ] `_apply_tire_friction` の呼び出しを更新
- [ ] 古い `_kill_lateral_velocity_at_center` を削除
- [ ] 古い `_kill_lateral_velocity` を削除（名前が同じなので注意）
- [ ] ユニットテストを実装
- [ ] すべてのテストが成功
- [ ] 挙動を目視確認（特にトルク発生の有無）
- [ ] コミット: `refactor: Unify lateral velocity suppression methods`

### フェーズ4: デバッグ機能の改善

- [ ] `logging` モジュールをインポート
- [ ] `__init__` でロガーを初期化
- [ ] `apply_control` にデバッグログを追加
- [ ] 各サブメソッドにデバッグログを追加（オプション）
- [ ] 古い `debug` パラメータの処理を削除または互換性を維持
- [ ] デバッグモードでログが出力されることを確認
- [ ] 通常モードでログが出ないことを確認
- [ ] コミット: `refactor: Improve debug logging in Vehicle`

### 最終確認

- [ ] すべてのテストが成功
- [ ] パフォーマンスが劣化していない
- [ ] ドキュメントが更新されている
- [ ] コードレビューを実施
- [ ] main ブランチにマージ

---

## まとめ

### リファクタリング効果

#### Before (現状)

- `apply_control`: 75行、複雑度8
- マジックナンバー: 4箇所
- 重複コード: 2メソッド（85%重複）
- テスト不可能な構造

#### After (目標)

- `apply_control`: 15-20行、複雑度2
- マジックナンバー: 0箇所（すべて定数化）
- 重複コード: 0箇所
- 各機能を個別にテスト可能

### 期待される改善

| 指標 | 改善前 | 改善後 | 改善率 |
|-----|--------|--------|--------|
| `apply_control` 行数 | 75行 | 15-20行 | 73-80%削減 |
| サイクロマティック複雑度 | 8 | 2 | 75%削減 |
| マジックナンバー | 4箇所 | 0箇所 | 100%削減 |
| 重複コード | 約30行 | 0行 | 100%削減 |
| テストカバレッジ | 0% | 80%以上 | - |

### 次のステップ

1. この計画書をレビュー
2. 必要に応じて調整
3. フェーズ1から順次実装
4. 各フェーズ後にテスト・コミット
5. 最終確認後にマージ

---

**実装を開始する準備ができました！**
