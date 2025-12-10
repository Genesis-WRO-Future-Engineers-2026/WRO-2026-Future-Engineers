# 壁衝突時の即終了機能 実装計画

## 現状分析

### 現在の実装（`src/env/minicar_env.py`）

#### 終了判定（`_check_terminated()` メソッド: 224-246行目）
```python
# 壁衝突（LiDARの最小距離が非常に小さい）
min_distance = np.min(lidar_scan)
if min_distance < 0.1:  # 10cm以内で衝突とみなす
    return True
```

**問題点:**
- LiDARベースの判定のため、LiDAR光線の間をすり抜けた場合に検出できない可能性
- 0.1m（10cm）の閾値が実際の車両サイズと適切に対応しているか不明
- 衝突時の報酬ペナルティが明示的でない

#### 報酬計算（`_compute_reward()` メソッド: 186-222行目）
```python
# 3. 壁接近ペナルティ
min_distance = np.min(lidar_scan)
if min_distance < 0.3:
    reward -= (0.3 - min_distance) * 10
```

**問題点:**
- 接近ペナルティはあるが、衝突時の明示的な大きなペナルティがない

---

## 実装方針

### アプローチ1: LiDAR判定の改善（推奨）
**メリット:**
- 既存のコードへの影響が小さい
- 実装が簡単
- LiDARは72方向あり、十分な密度で衝突を検出可能

**実装内容:**
1. 衝突判定の閾値を調整（車両サイズに基づく）
2. 衝突時の報酬ペナルティを追加
3. 衝突フラグを追加してinfo辞書で返す

### アプローチ2: Box2D衝突コールバックの利用（より正確）
**メリット:**
- 物理エンジンレベルの正確な衝突判定
- すり抜けの心配がない

**デメリット:**
- Box2Dの衝突コールバック実装が必要
- `src/physics/box2d_wrapper.py`の大幅な変更が必要
- コードの複雑性が増す

---

## 推奨実装: アプローチ1（LiDAR判定の改善）

### 1. 車両サイズの確認

`src/env/vehicle.py`で確認した車両の実際のサイズ:

```python
# 車両パラメータ（vehicle.py: 60-61行目）
self.width = 0.2  # m
self.length = 0.4  # m
```

**車両の対角線サイズ:**
```
対角線 = sqrt(0.2^2 + 0.4^2) = sqrt(0.20) ≈ 0.447m
車両中心から角までの距離（半径） = 0.447 / 2 ≈ 0.224m
```

**推奨衝突閾値:**
```
COLLISION_DISTANCE = 0.15m
理由: 車両半径（0.224m）よりも小さく、かつLiDARが車両中心から
      発射されることを考慮すると、0.15m程度が適切
```

### 2. `MinicarEnv`の修正内容

#### 2.1 衝突閾値の定数化
```python
class MinicarEnv(gym.Env):
    # クラス定数として追加
    COLLISION_DISTANCE = 0.15  # 車両の半径 + マージン（要調整）
    WALL_APPROACH_DISTANCE = 0.3  # 壁接近ペナルティの閾値
    COLLISION_PENALTY = -100.0  # 衝突時の報酬ペナルティ
```

#### 2.2 状態変数の追加
```python
def __init__(self, ...):
    # ...既存のコード...
    self.is_collision = False  # 衝突フラグ
```

#### 2.3 `_check_terminated()`の修正
```python
def _check_terminated(self) -> bool:
    """
    終了条件をチェック

    Returns:
        終了したかどうか
    """
    # キャッシュされたデータを使用
    state = self._cached_vehicle_state
    lidar_scan = self._cached_lidar_scan

    # ゴール到達（すべてのチェックポイントを通過している必要がある）
    checkpoints = self.course.get_checkpoints()
    all_checkpoints_passed = len(self.checkpoints_passed) == len(checkpoints)
    if all_checkpoints_passed and self.course.check_goal(state["position"]):
        return True

    # 壁衝突（LiDARの最小距離が衝突閾値以下）
    min_distance = np.min(lidar_scan)
    if min_distance <= self.COLLISION_DISTANCE:
        self.is_collision = True  # 衝突フラグを立てる
        return True

    return False
```

#### 2.4 `_compute_reward()`の修正
```python
def _compute_reward(self) -> float:
    """
    報酬を計算

    Returns:
        報酬
    """
    reward = 0.0
    # キャッシュされたデータを使用
    state = self._cached_vehicle_state
    lidar_scan = self._cached_lidar_scan

    # 1. 速度報酬
    speed = state["speed"]
    reward += speed * 0.1

    # 2. 時間ペナルティ
    reward -= 0.01

    # 3. 壁接近ペナルティ
    min_distance = np.min(lidar_scan)
    if min_distance < self.WALL_APPROACH_DISTANCE:
        reward -= (self.WALL_APPROACH_DISTANCE - min_distance) * 10

    # 3.5. 衝突ペナルティ（新規追加）
    if min_distance <= self.COLLISION_DISTANCE:
        reward += self.COLLISION_PENALTY  # 大きなペナルティ

    # 4. チェックポイント報酬
    checkpoints = self.course.get_checkpoints()
    for i, checkpoint in enumerate(checkpoints):
        if i not in self.checkpoints_passed:
            if self.course.check_checkpoint(state["position"], i):
                self.checkpoints_passed.add(i)
                reward += 50.0

    # 5. ゴール到達
    if self.course.check_goal(state["position"]):
        reward += 500.0

    return reward
```

#### 2.5 `_get_info()`の修正
```python
def _get_info(self) -> Dict[str, Any]:
    """
    追加情報を取得

    Returns:
        情報の辞書
    """
    # キャッシュされたデータを使用
    state = self._cached_vehicle_state
    lidar_scan = self._cached_lidar_scan

    return {
        "position": state["position"],
        "speed": state["speed"],
        "angle": state["angle"],
        "step_count": self.step_count,
        "total_reward": self.total_reward,
        "checkpoints_passed": len(self.checkpoints_passed),
        "min_distance": np.min(lidar_scan),
        "is_collision": self.is_collision,  # 新規追加
    }
```

#### 2.6 `reset()`の修正
```python
def reset(
    self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """環境をリセット"""
    super().reset(seed=seed)

    # 車両をリセット
    start_pos, start_angle = self.course.get_start_pose()
    self.vehicle.reset(start_pos, start_angle)

    # 状態をリセット
    self.step_count = 0
    self.last_action = np.zeros(2)
    self.total_reward = 0.0
    self.checkpoints_passed = set()
    self.is_collision = False  # 衝突フラグをリセット（新規追加）

    # 以下既存のコード...
```

### 3. テストケースの追加

#### 3.1 `tests/test_env.py`への追加
```python
def test_wall_collision_terminates():
    """壁衝突時に終了することを確認"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    obs, info = env.reset()

    # 壁に向かって直進する行動を繰り返す
    for _ in range(100):
        action = np.array([0.0, 1.0])  # 直進
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated:
            # 衝突フラグが立っていることを確認
            assert info["is_collision"] == True
            # ペナルティが与えられていることを確認
            assert reward <= MinicarEnv.COLLISION_PENALTY
            break

    env.close()


def test_collision_penalty():
    """衝突時に適切なペナルティが与えられることを確認"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    env.reset()

    # LiDARスキャンを衝突距離以下に設定してテスト
    # （内部テスト用）
    env._cached_lidar_scan = np.ones(72) * 0.05  # 5cm（衝突）

    reward = env._compute_reward()
    assert reward <= env.COLLISION_PENALTY
```

---

## パラメータ調整ガイドライン

### 衝突距離（COLLISION_DISTANCE）の決定方法

1. **車両サイズの確認**
   ```bash
   # vehicle.pyで車両の幅/長さを確認
   grep -n "width\|length\|WIDTH\|LENGTH" src/env/vehicle.py
   ```

2. **推奨値の計算**
   ```
   COLLISION_DISTANCE = 車両の対角線半径 + 安全マージン

   例: 車両が 0.2m × 0.1m の場合
   対角線 = sqrt(0.2^2 + 0.1^2) ≈ 0.224m
   半径 = 0.112m
   安全マージン = 0.05m
   → COLLISION_DISTANCE = 0.16m
   ```

3. **実験的調整**
   - 初期値: 0.15m
   - GUIモード（`--gui`）で実際の衝突を観察
   - 誤検知が多い場合: 閾値を下げる（0.12m など）
   - 検知漏れが多い場合: 閾値を上げる（0.18m など）

### 衝突ペナルティ（COLLISION_PENALTY）の決定方法

1. **既存の報酬スケールとの整合性**
   - ゴール報酬: +500.0
   - チェックポイント報酬: +50.0
   - 推奨ペナルティ: -100.0 〜 -200.0

2. **学習への影響を観察**
   - ペナルティが小さすぎる: 壁にぶつかる行動を学習しない
   - ペナルティが大きすぎる: 過度に保守的な行動（動かない）を学習
   - TensorBoardで「collision_rate」メトリクスを監視

---

## 実装スケジュール

### Phase 1: 基本実装（1日）
- [ ] `src/env/vehicle.py`で車両サイズを確認
- [ ] `MinicarEnv`に衝突判定パラメータを追加
- [ ] `_check_terminated()`を修正
- [ ] `_compute_reward()`を修正
- [ ] `_get_info()`を修正
- [ ] `reset()`を修正

### Phase 2: テスト（半日）
- [ ] `tests/test_env.py`にテストケースを追加
- [ ] テストを実行して動作確認
- [ ] GUIモードで視覚的に確認

### Phase 3: パラメータ調整（1日）
- [ ] 様々な閾値で学習を実行（短時間）
- [ ] 最適なパラメータを決定
- [ ] ドキュメントを更新

### Phase 4: 統合テスト（半日）
- [ ] カリキュラム学習での動作確認
- [ ] 既存の学習済みモデルでの影響確認
- [ ] CI/CDパイプラインでの確認

---

## 追加の改善案（オプション）

### 1. 衝突統計の追加
```python
# Trainerクラスに追加
self.collision_count = 0
self.total_episodes = 0

# エピソード終了時
if info["is_collision"]:
    self.collision_count += 1
self.total_episodes += 1

# TensorBoardにログ
collision_rate = self.collision_count / self.total_episodes
writer.add_scalar("metrics/collision_rate", collision_rate, iteration)
```

### 2. 動的な閾値調整（カリキュラム学習）
```python
# 難易度が上がるにつれて衝突閾値を厳しくする
def get_collision_distance(difficulty_level):
    base_distance = 0.20  # 初心者向け
    min_distance = 0.10   # 上級者向け
    return base_distance - (base_distance - min_distance) * (difficulty_level / max_level)
```

### 3. 衝突箇所の可視化
```python
# renderer.pyに追加
def draw_collision_point(self, position, angle, min_ray_index):
    """衝突したLiDAR光線を赤色で強調表示"""
    # 実装...
```

---

## まとめ

**推奨実装: アプローチ1（LiDAR判定の改善）**

- 実装難易度: 低
- 影響範囲: 小（`MinicarEnv`のみ）
- 期待効果: 高（明示的な衝突終了 + ペナルティ）
- 実装期間: 2-3日

Box2D衝突コールバック（アプローチ2）は、LiDAR判定で問題が発生した場合の次善策として検討。
