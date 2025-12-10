# 現実的なミニカーのステアリング実装計画

## 1. 現在の実装の問題点分析

### 1.1 現在のコード（`src/env/vehicle.py:48-71`）

```python
def apply_control(self, steering: float, throttle: float):
    # ステアリング角度
    steer_angle = np.clip(steering, -1.0, 1.0) * self.max_steering_angle

    # 車両の向き
    angle = self.body.angle
    direction = b2Vec2(
        np.cos(angle + steer_angle), np.sin(angle + steer_angle)
    )

    # モーター力を適用（負の値で後退）
    throttle = np.clip(throttle, -1.0, 1.0)
    force = throttle * self.max_motor_force * direction
    self.body.ApplyForceToCenter(force, True)

    # 横滑り抑制
    self._apply_lateral_friction()
```

### 1.2 問題点

1. **車体が回転しない**
   - ステアリング角度を力の方向に加算しているだけ
   - 車体（`self.body`）の角度は変化しない
   - 結果：斜めに進むだけで旋回しない

2. **ホイールの概念がない**
   - 現実の車は前輪がステアリングで向きを変え、後輪は固定
   - 現在は単一のボディに力を適用しているだけ

3. **横滑り抑制の位置が不適切**
   - 車体中心で横滑り抑制を適用
   - 現実のタイヤは前輪位置と後輪位置で独立に横滑りを抑制する

4. **運動学的に不正確**
   - 車両の回転は前輪と後輪の位置関係と速度から自然に発生すべき
   - 現在は力の方向を変えているだけで、運動学を無視している

## 2. 理論：Bicycle Model（バイシクルモデル）

### 2.1 Bicycle Modelとは

- 4輪車を2輪車として単純化したモデル
- 前輪2つを1つの仮想ホイール、後輪2つを1つの仮想ホイールとして扱う
- Ackermann Steeringと運動学的に同等

### 2.2 キーコンセプト

```
        前輪（ステアリング可能）
            ●
            |
            |  L (ホイールベース)
            |
            ●
        後輪（固定）
```

**運動学的関係式**：
```
角速度 ω = (v / L) * tan(δ)

ここで：
- ω: 車体の角速度 (rad/s)
- v: 車体の速度 (m/s)
- L: ホイールベース（前輪と後輪の距離） (m)
- δ: ステアリング角度 (rad)
```

**重要な特性**：
1. 速度が0なら回転しない（v=0 → ω=0）
2. ステアリング角度が大きいほど回転が大きい
3. ホイールベースが短いほど回転しやすい
4. 速度が速いほど回転が速い（ただし旋回半径は大きくなる）

### 2.3 タイヤの物理

**横滑り抑制（Lateral Friction）**：
- タイヤは横方向（車軸と垂直方向）には滑らない
- タイヤは前後方向（車軸と平行方向）には自由に動ける
- これを実現するには、各ホイール位置で横方向の速度成分を毎フレーム打ち消す

## 3. Box2Dでの実装方法

### 3.1 基本アプローチ

Box2Dで正確な車両物理を実装する方法は2つあります：

#### アプローチA：複数ボディ方式（高精度）
- 車体、前輪左、前輪右、後輪左、後輪右の5つのボディを作成
- ジョイントで接続
- 各ホイールで独立に横滑り抑制
- **利点**: 非常に正確、リアルな挙動
- **欠点**: 複雑、Box2Dのジョイント設定が難しい

#### アプローチB：単一ボディ + 仮想ホイール方式（簡易）
- 車体は1つのボディ
- 前輪と後輪の位置を計算で求める
- 各ホイール位置で横滑り抑制を適用
- 運動学的な式を使って角速度を計算し、適用
- **利点**: シンプル、調整しやすい、十分にリアル
- **欠点**: アプローチAほど正確ではない

**推奨**: アプローチB（単一ボディ + 仮想ホイール方式）
- RLの学習環境としては十分な精度
- 実装とデバッグが容易
- パラメータ調整がしやすい

### 3.2 実装の流れ（アプローチB）

```python
def apply_control(self, steering: float, throttle: float):
    # 1. パラメータ準備
    steering = np.clip(steering, -1.0, 1.0)
    throttle = np.clip(throttle, -1.0, 1.0)
    steer_angle = steering * self.max_steering_angle

    # 2. 前輪と後輪の位置を計算（ローカル座標系）
    front_wheel_local = (self.wheelbase / 2, 0)  # 車体前方
    rear_wheel_local = (-self.wheelbase / 2, 0)  # 車体後方

    # 3. ワールド座標系に変換
    front_wheel_world = self.body.GetWorldPoint(front_wheel_local)
    rear_wheel_world = self.body.GetWorldPoint(rear_wheel_local)

    # 4. 各ホイールの速度を取得
    front_wheel_velocity = self.body.GetLinearVelocityFromWorldPoint(front_wheel_world)
    rear_wheel_velocity = self.body.GetLinearVelocityFromWorldPoint(rear_wheel_world)

    # 5. 各ホイールで横滑り抑制
    self._kill_lateral_velocity(front_wheel_world, front_wheel_velocity, steer_angle)
    self._kill_lateral_velocity(rear_wheel_world, rear_wheel_velocity, 0)

    # 6. 駆動力を前輪の向きに沿って適用
    front_direction = b2Vec2(
        np.cos(self.body.angle + steer_angle),
        np.sin(self.body.angle + steer_angle)
    )
    force = throttle * self.max_motor_force * front_direction
    self.body.ApplyForce(force, front_wheel_world, True)

    # 7. 角速度を運動学的に計算して適用（オプション：より正確な挙動）
    # current_speed = self.body.linearVelocity.length
    # if current_speed > 0.1:
    #     angular_velocity = (current_speed / self.wheelbase) * np.tan(steer_angle)
    #     # 現在の角速度との差分をトルクで調整
    #     ...

def _kill_lateral_velocity(self, world_point, velocity, wheel_angle):
    """ホイール位置での横滑りを抑制"""
    # ホイールの向き（ワールド座標系）
    wheel_direction = b2Vec2(
        np.cos(self.body.angle + wheel_angle),
        np.sin(self.body.angle + wheel_angle)
    )

    # ホイールの横方向ベクトル
    wheel_lateral = b2Vec2(-wheel_direction.y, wheel_direction.x)

    # 横方向の速度成分
    lateral_velocity = wheel_lateral.dot(velocity) * wheel_lateral

    # 横方向の速度を打ち消すインパルス
    impulse = -self.body.mass * lateral_velocity
    self.body.ApplyLinearImpulse(impulse, world_point, True)
```

## 4. 実装ステップ

### ステップ1: パラメータの追加
- `self.wheelbase`: ホイールベース（前輪と後輪の距離）
  - 推奨値: `self.length * 0.7` ≈ 0.28m
  - 車両長が0.4mなので、その70%程度が妥当

### ステップ2: `_kill_lateral_velocity()` メソッドの実装
- ホイール位置、速度、ホイール角度を引数に取る
- ホイールの横方向の速度を打ち消すインパルスを適用

### ステップ3: `_apply_lateral_friction()` メソッドの削除
- 現在の車体中心での横滑り抑制は不要

### ステップ4: `apply_control()` メソッドの書き換え
- 前輪・後輪位置の計算
- 各ホイールでの横滑り抑制
- 前輪位置への駆動力適用

### ステップ5: テストと調整
- 手動制御で挙動を確認
- パラメータの微調整

## 5. パラメータ調整ガイド

### 5.1 主要パラメータ

| パラメータ | 現在値 | 推奨範囲 | 効果 |
|-----------|--------|----------|------|
| `wheelbase` | - | 0.25-0.30m | 短いほど曲がりやすい |
| `max_steering_angle` | 0.5 rad (28°) | 0.3-0.6 rad | 大きいほど急旋回可能 |
| `max_motor_force` | 20.0 N | 15-30 N | 大きいほど加速が速い |
| `linearDamping` | 0.5 | 0.3-0.8 | 大きいほど減速が速い |
| `angularDamping` | 0.8 | 0.5-1.5 | 大きいほど回転が安定 |

### 5.2 調整手順

1. **まず `wheelbase` を決定**
   - 車両長の65-75%程度
   - 短い → 曲がりやすいが不安定
   - 長い → 安定だが曲がりにくい

2. **`max_steering_angle` を調整**
   - 0.4 rad (23°) から開始
   - 曲がりが弱ければ増やす（最大0.6 rad）
   - 曲がりすぎなら減らす（最小0.3 rad）

3. **横滑り抑制の強度を調整**
   - `_kill_lateral_velocity()` 内のインパルスに係数をかける
   - `impulse = -self.body.mass * lateral_velocity * 0.8`
   - 係数が小さいほどドリフトしやすい

4. **`angularDamping` を調整**
   - 回転が過敏なら増やす（0.8 → 1.2）
   - 回転が鈍いなら減らす（0.8 → 0.5）

## 6. 期待される挙動

### 6.1 正しく実装された場合

- **停止時**: ステアリングを切っても回転しない
- **低速時**: ステアリングに応じて緩やかに曲がる
- **高速時**: ステアリングに応じて速く回転する（旋回半径は大きい）
- **前進時**: スムーズに弧を描いて旋回
- **後退時**: 逆向きに旋回（前輪が後ろになるため）

### 6.2 よくある問題と対処

| 問題 | 原因 | 対処 |
|------|------|------|
| 曲がらない | wheelbaseが長すぎる、max_steering_angleが小さすぎる | パラメータ調整 |
| 曲がりすぎ | wheelbaseが短すぎる、max_steering_angleが大きすぎる | パラメータ調整 |
| 横滑りする | 横滑り抑制が弱い | インパルスの係数を増やす |
| 不安定 | angularDampingが小さすぎる | angularDampingを増やす |
| 停止時に回転 | 実装ミス（速度チェックがない） | 実装を見直す |

## 7. テスト計画

### 7.1 単体テスト

1. **直進テスト**
   - steering=0, throttle=1.0
   - 車が真っ直ぐ進むことを確認

2. **左旋回テスト**
   - steering=-1.0, throttle=1.0
   - 車が左に弧を描いて進むことを確認

3. **右旋回テスト**
   - steering=1.0, throttle=1.0
   - 車が右に弧を描いて進むことを確認

4. **停止時テスト**
   - steering=1.0, throttle=0.0
   - 車が回転しないことを確認

5. **後退テスト**
   - steering=1.0, throttle=-0.5
   - 車が後退しながら逆向きに旋回することを確認

### 7.2 統合テスト

- 手動制御モード (`scripts/simulator-demo/manual_control.py`) で実際に走らせる
- コースを1周できるか確認
- 挙動が自然か確認

### 7.3 パラメータ調整テスト

- 各パラメータを変えて挙動の変化を確認
- 最適な値を見つける

## 8. 実装の優先順位

### 優先度：高
1. `wheelbase` パラメータの追加
2. `_kill_lateral_velocity()` メソッドの実装
3. `apply_control()` メソッドの書き換え（基本版）

### 優先度：中
4. パラメータの調整
5. テストと検証

### 優先度：低（オプション）
6. 運動学的な角速度の計算と適用（より正確な挙動）
7. タイヤの摩擦係数の動的調整（路面状態のシミュレーション）

## 9. 参考資料

- **Bicycle Model理論**: ROS2 Control Documentation - Wheeled Mobile Robot Kinematics
- **Box2D実装**: iforce2d - Top-down car physics tutorial
- **運動学**: Algorithms for Automated Driving - Kinematic Bicycle Model

## 10. 実装後の確認事項

- [ ] 車が前進しながら曲がるか
- [ ] ステアリング角度に応じて曲がり具合が変わるか
- [ ] 停止時は回転しないか
- [ ] 速度が速いほど回転が速いか（旋回半径は大きい）
- [ ] 後退時に逆向きに旋回するか
- [ ] 横滑りせずにグリップしているか
- [ ] コースを完走できるか
- [ ] 挙動が自然で制御しやすいか
