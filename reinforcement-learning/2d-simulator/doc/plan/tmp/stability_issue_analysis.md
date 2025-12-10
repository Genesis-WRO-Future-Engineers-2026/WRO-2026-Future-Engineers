# 超高速回転問題の原因分析と解決策

## 問題の症状

**現象**: 左右入力をすると最初は問題ないが、徐々に超高速で回転するようなあり得ない挙動になる

## 原因分析

### 現在の実装の問題点（`src/env/vehicle.py:85-110`）

```python
def _kill_lateral_velocity(self, world_point: b2Vec2, wheel_angle: float):
    # ホイール位置での速度を取得
    point_velocity = self.body.GetLinearVelocityFromWorldPoint(world_point)

    # 横方向の速度ベクトル
    lateral_velocity = lateral_velocity_magnitude * wheel_lateral

    # 横方向の速度を打ち消すインパルスを適用
    impulse = -self.body.mass * lateral_velocity  # ← 問題：無制限！
    self.body.ApplyLinearImpulse(impulse, world_point, True)
```

**問題点**:
1. **インパルスに上限がない**
   - `impulse = -self.body.mass * lateral_velocity` が無制限に大きくなる
   - 横滑りが大きいほど、より大きなインパルスを適用
   - これが正のフィードバックループを作り、不安定になる

2. **角速度の減衰がない**
   - 一度回転し始めると、止める力がない
   - `angularDamping=0.8` だけでは不十分

3. **インパルスの適用位置が問題を増幅**
   - 前輪と後輪の異なる位置にインパルスを適用
   - 横滑り抑制が逆にトルク（回転力）を生み出してしまう

### なぜ超高速回転が発生するのか

```
1. ステアリング入力 → 前輪が向きを変える
2. 前輪位置で大きな横滑りが発生
3. 大きな横滑り → 大きなインパルスを適用（無制限）
4. 大きなインパルス → 車体に大きなトルクが発生
5. 車体が回転 → さらに横滑りが増加
6. ステップ2に戻る（正のフィードバック）
```

## pybox2d公式実装の解決策

**参考**: https://github.com/pybox2d/pybox2d/blob/master/library/Box2D/examples/top_down_car.py

### 重要なポイント1: インパルスの上限設定

```python
def update_friction(self):
    impulse = -self.lateral_velocity * self.body.mass

    # ここが重要！インパルスに上限を設定
    if impulse.length > self.max_lateral_impulse:
        impulse *= self.max_lateral_impulse / impulse.length

    self.body.ApplyLinearImpulse(
        self.current_traction * impulse,
        self.body.worldCenter,
        True
    )
```

**効果**:
- インパルスが一定値を超えない
- 正のフィードバックループを防ぐ
- タイヤが滑る現象（ドリフト）も再現できる

### 重要なポイント2: 角速度の減衰

```python
# 角速度を積極的に減衰させる
aimp = 0.1 * self.current_traction * self.body.inertia * -self.body.angularVelocity
self.body.ApplyAngularImpulse(aimp, True)
```

**効果**:
- 回転が自然に減衰する
- 過剰な回転を抑制

### 重要なポイント3: ドラッグ力（空気抵抗）

```python
# 前後方向の抵抗
current_forward_normal = self.forward_velocity
current_forward_speed = current_forward_normal.Normalize()

drag_force_magnitude = -2 * current_forward_speed
self.body.ApplyForce(
    self.current_traction * drag_force_magnitude * current_forward_normal,
    self.body.worldCenter,
    True
)
```

## 解決策の選択肢

### 選択肢A: 現在の実装を修正（推奨）

**変更点**:
1. `max_lateral_impulse` パラメータを追加（推奨値: 2.5-5.0）
2. `_kill_lateral_velocity()` でインパルスをクリップ
3. 角速度の減衰を追加

**メリット**:
- 現在のアーキテクチャを維持
- 最小限の変更で問題を解決
- 理解しやすい

**デメリット**:
- pybox2d公式実装ほど精密ではない

### 選択肢B: pybox2d公式実装を参考に全面書き換え

**変更点**:
1. 車体とタイヤを別々のボディとして作成
2. RevoluteJointで接続
3. 各タイヤで独立に物理計算

**メリット**:
- 最も正確で安定
- 公式実装の実績がある

**デメリット**:
- 大規模な変更が必要
- 複雑になる
- RLの学習環境としてはオーバースペック

### 選択肢C: より単純なモデルに戻す

**変更点**:
1. Bicycle Modelを諦める
2. トルクベースの単純なモデルを使う
3. 適切なパラメータ調整

**メリット**:
- シンプル
- 調整が容易

**デメリット**:
- 現実的な挙動ではない
- 学習が難しい可能性

## 推奨：選択肢Aの実装詳細

### 1. パラメータの追加

```python
# vehicle.py の __init__ に追加
self.max_lateral_impulse = 2.5  # 横滑り抑制の最大インパルス
```

### 2. `_kill_lateral_velocity()` の修正

```python
def _kill_lateral_velocity(self, world_point: b2Vec2, wheel_angle: float):
    """
    ホイール位置での横滑りを抑制（タイヤは横方向に滑らない）
    """
    # ホイール位置での速度を取得
    point_velocity = self.body.GetLinearVelocityFromWorldPoint(world_point)

    # ホイールの向き（前後方向）
    wheel_forward = b2Vec2(np.cos(wheel_angle), np.sin(wheel_angle))

    # ホイールの横方向（左右方向）
    wheel_lateral = b2Vec2(-wheel_forward.y, wheel_forward.x)

    # 横方向の速度成分
    lateral_velocity_magnitude = point_velocity.dot(wheel_lateral)

    # 横方向の速度ベクトル
    lateral_velocity = lateral_velocity_magnitude * wheel_lateral

    # 横方向の速度を打ち消すインパルスを計算
    impulse = -self.body.mass * lateral_velocity

    # インパルスをクリップ（重要！）
    impulse_length = np.linalg.norm([impulse.x, impulse.y])
    if impulse_length > self.max_lateral_impulse:
        impulse *= self.max_lateral_impulse / impulse_length

    # インパルスを適用
    self.body.ApplyLinearImpulse(impulse, world_point, True)
```

### 3. `apply_control()` に角速度減衰を追加

```python
def apply_control(self, steering: float, throttle: float):
    # ... (既存のコード)

    # 駆動力を前輪の向きに沿って適用
    front_direction = b2Vec2(
        np.cos(front_wheel_angle), np.sin(front_wheel_angle)
    )
    force = throttle * self.max_motor_force * front_direction
    self.body.ApplyForce(force, front_wheel_world, True)

    # 角速度の減衰を追加（重要！）
    angular_impulse = -0.1 * self.body.inertia * self.body.angularVelocity
    self.body.ApplyAngularImpulse(angular_impulse, True)
```

### 4. パラメータの調整ガイド

| パラメータ | 推奨初期値 | 調整方向 | 効果 |
|-----------|-----------|---------|------|
| `max_lateral_impulse` | 2.5 | 大きく → グリップ力UP、小さく → ドリフトしやすい | 2.0-5.0 |
| `angularDamping` | 0.8 | 大きく → 回転減衰、小さく → 回転しやすい | 0.5-1.5 |
| 角速度減衰係数 | 0.1 | 大きく → 回転安定、小さく → 回転持続 | 0.05-0.2 |

## テスト計画

### 1. 安定性テスト
- 左右にステアリングを振り続ける
- 回転が徐々に大きくならないことを確認

### 2. 旋回テスト
- 定速で円を描く
- 一定の旋回半径を維持できることを確認

### 3. 高速テスト
- 最高速度で急旋回
- 車が飛んでいかないことを確認

### 4. ドリフトテスト
- 高速で急旋回
- 適度にドリフトすることを確認（完全にグリップではない）

## 実装の優先順位

1. **最優先**: インパルスのクリッピング
2. **高**: 角速度の減衰
3. **中**: パラメータの調整
4. **低**: ドラッグ力の追加（オプション）

## 参考資料

- **pybox2d公式実装**: https://github.com/pybox2d/pybox2d/blob/master/library/Box2D/examples/top_down_car.py
- **iforce2d チュートリアル**: https://www.iforce2d.net/b2dtut/top-down-car
- **Box2Dフォーラム**: http://www.box2d.org/forum/viewtopic.php?f=3&t=5362
