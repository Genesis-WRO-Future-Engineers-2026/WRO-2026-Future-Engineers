# pybox2d公式実装ベースの車両物理実装計画

## 1. 現在の実装の問題点

### 現在のアプローチ（単一ボディ + 仮想ホイール）
- 車体：1つのボディ
- ホイール：計算上の仮想点
- 横滑り抑制：仮想ホイール位置にインパルスを適用

### 問題
1. **物理的に不正確**
   - 何も入力していないのに動く
   - 横滑り抑制が車体にトルクを発生させる（意図しない副作用）

2. **調整が困難**
   - パラメータ調整が難しい
   - 安定性と応答性のトレードオフが厳しい

3. **根本的な限界**
   - 単一ボディでは前輪と後輪の独立した挙動を正確に再現できない

## 2. pybox2d公式実装の分析

### 2.1 アーキテクチャ

**参考コード**: https://github.com/pybox2d/pybox2d/blob/master/library/Box2D/examples/top_down_car.py

```
TDCar (車全体)
├── body (車体ボディ)
└── tires (4つのタイヤ)
    ├── TDTire (後輪左)
    ├── TDTire (後輪右)
    ├── TDTire (前輪左)
    └── TDTire (前輪右)

各タイヤ:
- 独立したボディ（Box2Dの動的ボディ）
- RevoluteJointで車体に接続
- 前輪のジョイントはlimitで角度を制御（ステアリング）
```

### 2.2 TDTire クラスの役割

#### プロパティ
```python
@property
def forward_velocity(self):
    """タイヤの前後方向の速度"""
    current_normal = body.GetWorldVector((0, 1))
    return current_normal.dot(body.linearVelocity) * current_normal

@property
def lateral_velocity(self):
    """タイヤの横方向の速度"""
    right_normal = body.GetWorldVector((1, 0))
    return right_normal.dot(body.linearVelocity) * right_normal
```

#### メソッド

**1. update_friction() - 摩擦の更新（最重要）**
```python
def update_friction(self):
    # 横滑り抑制
    impulse = -self.lateral_velocity * self.body.mass
    if impulse.length > self.max_lateral_impulse:
        impulse *= self.max_lateral_impulse / impulse.length
    self.body.ApplyLinearImpulse(impulse, self.body.worldCenter, True)

    # 角速度の減衰
    aimp = 0.1 * self.body.inertia * -self.body.angularVelocity
    self.body.ApplyAngularImpulse(aimp, True)

    # ドラッグ力（前進抵抗）
    current_forward_normal = self.forward_velocity
    current_forward_speed = current_forward_normal.Normalize()
    drag_force_magnitude = -2 * current_forward_speed
    self.body.ApplyForce(
        drag_force_magnitude * current_forward_normal,
        self.body.worldCenter, True
    )
```

**2. update_drive() - 駆動力の適用**
```python
def update_drive(self, keys):
    # 前後キーに応じて駆動力を適用
    if 'up' in keys:
        desired_speed = self.max_forward_speed
    elif 'down' in keys:
        desired_speed = self.max_backward_speed
    else:
        return

    current_forward_normal = self.body.GetWorldVector((0, 1))
    current_speed = self.forward_velocity.dot(current_forward_normal)

    force = 0.0
    if desired_speed > current_speed:
        force = self.max_drive_force
    elif desired_speed < current_speed:
        force = -self.max_drive_force

    self.body.ApplyForce(
        force * current_forward_normal,
        self.body.worldCenter, True
    )
```

**3. update_turn() - ステアリング（タイヤ自体の回転）**
```python
def update_turn(self, keys):
    # タイヤ自体にトルクを適用（公式実装では使われていない）
    if 'left' in keys:
        desired_torque = self.turn_torque
    elif 'right' in keys:
        desired_torque = -self.turn_torque
    else:
        return
    self.body.ApplyTorque(desired_torque, True)
```

### 2.3 TDCar クラスの役割

#### 初期化
```python
def __init__(self, world, ...):
    # 車体を作成
    self.body = world.CreateDynamicBody(position=position)
    self.body.CreatePolygonFixture(vertices=vertices, density=density)

    # 4つのタイヤを作成
    self.tires = [TDTire(self, **tire_kws) for i in range(4)]

    # RevoluteJointでタイヤを車体に接続
    for tire, anchor in zip(self.tires, anchors):
        j = world.CreateRevoluteJoint(
            bodyA=self.body,
            bodyB=tire.body,
            localAnchorA=anchor,      # 車体上の接続点
            localAnchorB=(0, 0),      # タイヤの中心
            enableMotor=False,
            enableLimit=True,
            lowerAngle=0,
            upperAngle=0,             # 初期はロック（後輪）
        )
        tire.body.position = self.body.worldCenter + anchor
        self.joints.append(j)
```

#### 更新ループ
```python
def update(self, keys, hz):
    # 1. すべてのタイヤで摩擦を更新
    for tire in self.tires:
        tire.update_friction()

    # 2. すべてのタイヤで駆動力を適用
    for tire in self.tires:
        tire.update_drive(keys)

    # 3. 前輪のステアリング角度を制御
    lock_angle = math.radians(40.)
    turn_speed_per_sec = math.radians(160.)
    turn_per_timestep = turn_speed_per_sec / hz

    desired_angle = 0.0
    if 'left' in keys:
        desired_angle = lock_angle
    elif 'right' in keys:
        desired_angle = -lock_angle

    # 前輪のジョイント角度を変更
    front_left_joint, front_right_joint = self.joints[2:4]
    angle_now = front_left_joint.angle
    angle_to_turn = desired_angle - angle_now

    # 角度変化を制限（滑らかなステアリング）
    angle_to_turn = np.clip(angle_to_turn, -turn_per_timestep, turn_per_timestep)

    new_angle = angle_now + angle_to_turn
    front_left_joint.SetLimits(new_angle, new_angle)
    front_right_joint.SetLimits(new_angle, new_angle)
```

### 2.4 重要なポイント

1. **各タイヤは独立したボディ**
   - タイヤ自身が物理演算の対象
   - タイヤに直接インパルスを適用しても、車体に意図しないトルクは発生しない（ジョイントで適切に接続されているため）

2. **RevoluteJointの役割**
   - タイヤと車体を接続
   - ジョイントのlimitを変えることでステアリング角度を制御
   - 物理的に正確な接続

3. **ステアリングの実装**
   - タイヤにトルクを与えるのではない
   - ジョイントのlimitを変えることで、タイヤの角度を強制的に制御

4. **安定性の秘訣**
   - タイヤボディで直接物理計算
   - インパルスのクリッピング
   - 角速度の減衰
   - ドラッグ力

## 3. RLに適した実装設計

### 3.1 公式実装との違い

公式実装はデモ用なので、RLには不要な部分があります：

| 公式実装 | RLでの対応 |
|---------|----------|
| キーボード入力 | action (steering, throttle) |
| 4つのタイヤで独立に駆動 | 全タイヤ同じ駆動力でOK |
| 地面エリアの摩擦変化 | 不要（削除） |
| 滑らかなステアリング（時間制限） | 不要（即座に角度変更でOK） |

### 3.2 クラス設計

#### Tire クラス（新規作成）

**ファイル**: `src/env/tire.py`

```python
class Tire:
    """タイヤの物理モデル"""

    def __init__(
        self,
        world: b2World,
        position: Tuple[float, float],
        max_forward_speed: float = 10.0,
        max_backward_speed: float = -5.0,
        max_drive_force: float = 150.0,
        max_lateral_impulse: float = 3.0,
        size: Tuple[float, float] = (0.1, 0.2),
    ):
        """
        Args:
            world: Box2D物理世界
            position: 初期位置
            max_forward_speed: 最大前進速度 (m/s)
            max_backward_speed: 最大後退速度 (m/s)
            max_drive_force: 最大駆動力 (N)
            max_lateral_impulse: 最大横滑り抑制インパルス
            size: タイヤサイズ (width, length)
        """
        self.max_forward_speed = max_forward_speed
        self.max_backward_speed = max_backward_speed
        self.max_drive_force = max_drive_force
        self.max_lateral_impulse = max_lateral_impulse

        # タイヤボディを作成
        self.body = world.CreateDynamicBody(position=position)
        self.body.CreatePolygonFixture(
            box=size,
            density=1.0,
        )

    @property
    def forward_velocity(self) -> b2Vec2:
        """タイヤの前後方向の速度ベクトル"""
        forward_normal = self.body.GetWorldVector((0, 1))
        return forward_normal.dot(self.body.linearVelocity) * forward_normal

    @property
    def lateral_velocity(self) -> b2Vec2:
        """タイヤの横方向の速度ベクトル"""
        lateral_normal = self.body.GetWorldVector((1, 0))
        return lateral_normal.dot(self.body.linearVelocity) * lateral_normal

    def update_friction(self):
        """摩擦（横滑り抑制、角速度減衰、ドラッグ）を適用"""
        # 1. 横滑り抑制
        impulse = -self.lateral_velocity * self.body.mass
        impulse_length = impulse.length
        if impulse_length > self.max_lateral_impulse:
            impulse *= self.max_lateral_impulse / impulse_length
        self.body.ApplyLinearImpulse(impulse, self.body.worldCenter, True)

        # 2. 角速度の減衰
        angular_impulse = 0.1 * self.body.inertia * -self.body.angularVelocity
        self.body.ApplyAngularImpulse(angular_impulse, True)

        # 3. ドラッグ力（前進方向の抵抗）
        forward_vel = self.forward_velocity
        drag_magnitude = -2.0 * forward_vel.length
        if forward_vel.length > 0:
            forward_vel.Normalize()
            self.body.ApplyForce(
                drag_magnitude * forward_vel,
                self.body.worldCenter,
                True
            )

    def apply_drive_force(self, throttle: float):
        """
        駆動力を適用

        Args:
            throttle: スロットル (-1.0 ~ 1.0)
        """
        # 目標速度を決定
        if throttle > 0:
            desired_speed = throttle * self.max_forward_speed
        else:
            desired_speed = throttle * abs(self.max_backward_speed)

        # 現在の前進速度
        forward_normal = self.body.GetWorldVector((0, 1))
        current_speed = self.forward_velocity.dot(forward_normal)

        # 必要な力を計算
        if abs(desired_speed - current_speed) < 0.1:
            return  # 既に目標速度に近い

        if desired_speed > current_speed:
            force = self.max_drive_force
        else:
            force = -self.max_drive_force

        # 力を適用
        self.body.ApplyForce(
            force * forward_normal,
            self.body.worldCenter,
            True
        )
```

#### Vehicle クラス（改修）

**ファイル**: `src/env/vehicle.py`

```python
from src.env.tire import Tire

class Vehicle:
    """ミニカーの物理モデル（pybox2d公式実装ベース）"""

    def __init__(
        self,
        world: b2World,
        start_pos: Tuple[float, float],
        start_angle: float = 0.0,
    ):
        self.world = world

        # 車両パラメータ
        self.width = 0.2  # m
        self.length = 0.4  # m
        self.wheelbase = 0.3  # m
        self.track_width = 0.18  # m（左右のタイヤの間隔）

        self.max_steering_angle = 0.5  # rad

        # 車体ボディを作成
        self.body = world.CreateDynamicBody(
            position=b2Vec2(*start_pos),
            angle=start_angle,
            linearDamping=0.1,
            angularDamping=0.3,
        )
        self.body.CreatePolygonFixture(
            box=(self.length / 2, self.width / 2),
            density=0.1,
        )

        # タイヤの位置（ローカル座標）
        tire_positions = [
            (-self.wheelbase / 2, -self.track_width / 2),  # 後輪左
            (-self.wheelbase / 2, self.track_width / 2),   # 後輪右
            (self.wheelbase / 2, -self.track_width / 2),   # 前輪左
            (self.wheelbase / 2, self.track_width / 2),    # 前輪右
        ]

        # 4つのタイヤを作成
        self.tires = []
        self.joints = []

        for local_pos in tire_positions:
            # ワールド座標に変換
            world_pos = self.body.GetWorldPoint(b2Vec2(*local_pos))

            # タイヤを作成
            tire = Tire(world, (world_pos.x, world_pos.y))
            tire.body.angle = start_angle
            self.tires.append(tire)

            # RevoluteJointで車体とタイヤを接続
            joint = world.CreateRevoluteJoint(
                bodyA=self.body,
                bodyB=tire.body,
                localAnchorA=b2Vec2(*local_pos),
                localAnchorB=b2Vec2(0, 0),
                enableMotor=False,
                enableLimit=True,
                lowerAngle=0,
                upperAngle=0,
            )
            self.joints.append(joint)

    def apply_control(self, steering: float, throttle: float):
        """
        制御入力を適用

        Args:
            steering: ステアリング (-1.0 ~ 1.0)
            throttle: スロットル (-1.0 ~ 1.0)
        """
        steering = np.clip(steering, -1.0, 1.0)
        throttle = np.clip(throttle, -1.0, 1.0)

        # 1. すべてのタイヤで摩擦を更新
        for tire in self.tires:
            tire.update_friction()

        # 2. すべてのタイヤで駆動力を適用
        for tire in self.tires:
            tire.apply_drive_force(throttle)

        # 3. 前輪のステアリング角度を設定
        steer_angle = steering * self.max_steering_angle

        # 前輪のジョイント（インデックス2, 3）
        front_left_joint = self.joints[2]
        front_right_joint = self.joints[3]

        # ジョイントのlimitを変更してステアリング
        front_left_joint.SetLimits(steer_angle, steer_angle)
        front_right_joint.SetLimits(steer_angle, steer_angle)

    def get_state(self) -> Dict:
        """車両の状態を取得"""
        return {
            "position": (self.body.position.x, self.body.position.y),
            "angle": self.body.angle,
            "velocity": (self.body.linearVelocity.x, self.body.linearVelocity.y),
            "angular_velocity": self.body.angularVelocity,
            "speed": np.linalg.norm(
                [self.body.linearVelocity.x, self.body.linearVelocity.y]
            ),
        }

    def reset(self, position: Tuple[float, float], angle: float = 0.0):
        """車両をリセット"""
        self.body.position = b2Vec2(*position)
        self.body.angle = angle
        self.body.linearVelocity = b2Vec2(0, 0)
        self.body.angularVelocity = 0

        # タイヤもリセット
        tire_positions = [
            (-self.wheelbase / 2, -self.track_width / 2),
            (-self.wheelbase / 2, self.track_width / 2),
            (self.wheelbase / 2, -self.track_width / 2),
            (self.wheelbase / 2, self.track_width / 2),
        ]

        for tire, local_pos in zip(self.tires, tire_positions):
            world_pos = self.body.GetWorldPoint(b2Vec2(*local_pos))
            tire.body.position = world_pos
            tire.body.angle = angle
            tire.body.linearVelocity = b2Vec2(0, 0)
            tire.body.angularVelocity = 0

        # 前輪のステアリングをリセット
        self.joints[2].SetLimits(0, 0)
        self.joints[3].SetLimits(0, 0)
```

## 4. 実装ステップ

### フェーズ1: Tire クラスの作成
1. `src/env/tire.py` を新規作成
2. `Tire` クラスを実装
   - `__init__`
   - `forward_velocity` プロパティ
   - `lateral_velocity` プロパティ
   - `update_friction()`
   - `apply_drive_force()`
3. 単体テスト（オプション）

### フェーズ2: Vehicle クラスの改修
1. `src/env/vehicle.py` をバックアップ
2. 新しい `Vehicle` クラスを実装
   - `__init__`: 車体 + 4タイヤ + ジョイント
   - `apply_control()`: 新しいロジック
   - `get_state()`: 既存を維持
   - `reset()`: タイヤのリセットを追加
3. 既存のインポートを確認

### フェーズ3: 統合テスト
1. `MinicarEnv` で新しい `Vehicle` が動作するか確認
2. 手動制御でテスト
3. パラメータ調整

### フェーズ4: 最適化（オプション）
1. パラメータのチューニング
2. 描画の改善（タイヤも描画）

## 5. パラメータ設定

### 車両パラメータ
| パラメータ | 推奨値 | 説明 |
|-----------|-------|------|
| `width` | 0.2 m | 車体幅 |
| `length` | 0.4 m | 車体長 |
| `wheelbase` | 0.3 m | 前後輪間距離 |
| `track_width` | 0.18 m | 左右タイヤ間隔 |
| `max_steering_angle` | 0.5 rad (28°) | 最大ステアリング角 |
| `linearDamping` | 0.1 | 車体の線形減衰 |
| `angularDamping` | 0.3 | 車体の角減衰 |

### タイヤパラメータ
| パラメータ | 推奨値 | 説明 |
|-----------|-------|------|
| `max_forward_speed` | 10.0 m/s | 最大前進速度 |
| `max_backward_speed` | -5.0 m/s | 最大後退速度 |
| `max_drive_force` | 150 N | 最大駆動力 |
| `max_lateral_impulse` | 3.0 | 最大横滑り抑制 |
| `size` | (0.1, 0.2) m | タイヤサイズ |

## 6. テスト計画

### 6.1 単体テスト

**Tire クラス**:
1. タイヤが作成されるか
2. `forward_velocity` が正しく計算されるか
3. `lateral_velocity` が正しく計算されるか
4. `update_friction()` で横滑りが抑制されるか
5. `apply_drive_force()` で加速するか

**Vehicle クラス**:
1. 車体と4つのタイヤが作成されるか
2. ジョイントが正しく接続されているか
3. ステアリング入力で前輪が回転するか
4. スロットル入力で加速するか

### 6.2 統合テスト

1. **静止テスト**
   - steering=0, throttle=0
   - 車が動かないことを確認

2. **直進テスト**
   - steering=0, throttle=1.0
   - 車が真っ直ぐ進むことを確認

3. **左旋回テスト**
   - steering=-1.0, throttle=1.0
   - 車が左に曲がることを確認

4. **右旋回テスト**
   - steering=1.0, throttle=1.0
   - 車が右に曲がることを確認

5. **後退テスト**
   - steering=1.0, throttle=-0.5
   - 車が後退しながら旋回することを確認

6. **安定性テスト**
   - 連続でステアリングを左右に振る
   - 回転が発散しないことを確認

7. **コース走行テスト**
   - 手動制御でコースを1周
   - 自然な挙動で制御可能か確認

### 6.3 パフォーマンステスト

1. フレームレート確認
2. 物理演算のステップ時間測定
3. 必要に応じて最適化

## 7. 既存コードとの互換性

### MinicarEnv クラス

**変更不要**:
- `Vehicle` クラスのインターフェース（`apply_control()`, `get_state()`, `reset()`）は維持
- `MinicarEnv` は変更なしで動作するはず

**潜在的な問題**:
- タイヤボディが壁と衝突する可能性
  - 解決策: タイヤのフィクスチャを `sensor=True` に設定（衝突判定なし）

### Renderer クラス

**現在**:
- 車体のみ描画

**改善案（オプション）**:
- タイヤも描画すると視覚的に分かりやすい
- タイヤの向き（ステアリング角）も表示

## 8. 移行戦略

### オプションA: 段階的移行（推奨）
1. 新しい実装を `src/env/vehicle_v2.py` として作成
2. テスト用の環境を別途作成
3. 動作確認後、`vehicle.py` を置き換え

### オプションB: 直接置き換え
1. `src/env/vehicle.py` をバックアップ
2. 新しい実装で置き換え
3. 問題があればバックアップから復元

## 9. 期待される結果

### 改善点
1. **安定性**: 何も入力していない時は完全に静止
2. **正確性**: 物理的に正確な挙動
3. **制御性**: 自然で制御しやすい
4. **調整性**: パラメータ調整が直感的

### 挙動
- 停止時: 回転しない、動かない
- 低速時: 緩やかに旋回
- 高速時: 素早く旋回、ドリフトする
- 後退時: 逆向きに旋回

## 10. リスクと対策

### リスク1: 実装が複雑
**対策**: pybox2d公式コードをベースにする、段階的に実装

### リスク2: パフォーマンス低下
**対策**: プロファイリング、必要に応じて最適化

### リスク3: 既存の学習モデルとの互換性
**対策**: observation spaceは変更しない

### リスク4: タイヤが壁と衝突
**対策**: タイヤを `sensor=True` に設定

## 11. 参考資料

- **pybox2d公式実装**: https://github.com/pybox2d/pybox2d/blob/master/library/Box2D/examples/top_down_car.py
- **iforce2d チュートリアル**: https://www.iforce2d.net/b2dtut/top-down-car
- **Box2D マニュアル**: https://box2d.org/documentation/

## 12. 実装チェックリスト

- [ ] `src/env/tire.py` を作成
- [ ] `Tire` クラスを実装
  - [ ] `__init__`
  - [ ] `forward_velocity` プロパティ
  - [ ] `lateral_velocity` プロパティ
  - [ ] `update_friction()`
  - [ ] `apply_drive_force()`
- [ ] `src/env/vehicle.py` をバックアップ
- [ ] 新しい `Vehicle` クラスを実装
  - [ ] `__init__`: 車体 + タイヤ + ジョイント
  - [ ] `apply_control()`: 新ロジック
  - [ ] `get_state()`: 既存維持
  - [ ] `reset()`: タイヤリセット追加
- [ ] 単体テスト
  - [ ] タイヤ単体
  - [ ] 車両単体
- [ ] 統合テスト
  - [ ] 静止テスト
  - [ ] 直進テスト
  - [ ] 旋回テスト
  - [ ] 安定性テスト
- [ ] 手動制御でコース走行
- [ ] パラメータ調整
- [ ] レンダラーの改善（オプション）
