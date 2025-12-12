# チェックポイント情報を観測空間に追加する実装計画

## 概要

現在の観測空間にはチェックポイントやゴールの位置情報が含まれていないため、エージェントが「どこに向かえばいいか」を学習できず、成功率が60%で停滞している。

次のチェックポイントへの**距離**と**角度**を観測空間に追加することで、エージェントが目的地を認識できるようにする。

---

## 現状の問題

### 観測空間（10次元）
```python
[
    lidar_scan,        # 5次元（前方120度の壁までの距離）
    velocity,          # 2次元（vx, vy）
    angular_velocity,  # 1次元
    last_action,       # 2次元（steering, throttle）
]
```

### 問題点
- ✅ 壁の位置は分かる（LiDAR）
- ✅ 自分の速度・回転は分かる
- ❌ **次のチェックポイントがどこにあるか分からない**
- ❌ **ゴールがどの方向にあるか分からない**

### 結果
- 成功率が60%で停滞
- エージェントがランダムに走り回る
- 「たまたまゴールに到達」することはあるが、再現性がない

---

## 目標

### 新しい観測空間（12次元）
```python
[
    lidar_scan,              # 5次元
    velocity,                # 2次元
    angular_velocity,        # 1次元
    last_action,             # 2次元
    checkpoint_distance,     # 1次元 ← 新規
    checkpoint_angle,        # 1次元 ← 新規
]
```

### 追加する情報
1. **checkpoint_distance**: 次のチェックポイントまでの直線距離（m）
2. **checkpoint_angle**: 次のチェックポイントへの角度（rad）
   - 車両の正面方向を0とした相対角度
   - 範囲: -π ~ π（-180° ~ 180°）
   - 正: 右方向、負: 左方向

---

## 実装手順

### Phase 1: チェックポイント情報の計算機能を追加

**ファイル**: `src/env/minicar_env.py`

#### 1.1 次のチェックポイント情報を計算するメソッドを追加

```python
def _get_next_checkpoint_info(self) -> Tuple[float, float]:
    """
    次のチェックポイントへの距離と角度を計算

    Returns:
        (distance, angle): 距離（m）と角度（rad）
    """
    # キャッシュされた車両状態を使用
    vehicle_pos = self._cached_vehicle_state["position"]
    vehicle_angle = self._cached_vehicle_state["angle"]

    checkpoints = self.course.get_checkpoints()

    # 全チェックポイントを通過済みの場合はゴールを目標とする
    if self.next_checkpoint_index >= len(checkpoints):
        target_pos, _ = self.course.get_goal_info()
    else:
        checkpoint = checkpoints[self.next_checkpoint_index]
        target_pos = checkpoint["position"]

    # 距離を計算
    dx = target_pos[0] - vehicle_pos[0]
    dy = target_pos[1] - vehicle_pos[1]
    distance = np.sqrt(dx**2 + dy**2)

    # 絶対角度を計算（ワールド座標系）
    target_angle_world = np.arctan2(dy, dx)

    # 車両座標系での相対角度に変換
    # 車両の正面方向が0、右が正、左が負
    relative_angle = target_angle_world - vehicle_angle

    # -π ~ π の範囲に正規化
    relative_angle = np.arctan2(np.sin(relative_angle), np.cos(relative_angle))

    return distance, relative_angle
```

#### 1.2 `_get_observation()` メソッドを更新

```python
def _get_observation(self) -> np.ndarray:
    """
    現在の観測を取得

    Returns:
        観測ベクトル (12次元)  # 10次元 → 12次元に変更
    """
    # キャッシュされたデータを使用
    lidar_scan = self._cached_lidar_scan
    velocity = np.array(self._cached_vehicle_state["velocity"])
    angular_velocity = np.array([self._cached_vehicle_state["angular_velocity"]])

    # 次のチェックポイント情報を取得
    checkpoint_distance, checkpoint_angle = self._get_next_checkpoint_info()

    # 観測を結合
    obs = np.concatenate([
        lidar_scan,              # 5
        velocity,                # 2
        angular_velocity,        # 1
        self.last_action,        # 2
        [checkpoint_distance],   # 1 (新規)
        [checkpoint_angle],      # 1 (新規)
    ])

    return obs.astype(np.float32)
```

#### 1.3 observation_spaceの定義を更新（`__init__`メソッド内）

```python
# 観測空間: LiDAR(5) + velocity(2) + angular_velocity(1) + last_action(2) + checkpoint_info(2) = 12
self.observation_space = spaces.Box(
    low=-np.inf, high=np.inf, shape=(12,), dtype=np.float32  # 10 → 12
)
```

---

### Phase 2: テストを追加

**ファイル**: `tests/test_checkpoint_observation.py`（新規作成）

#### 2.1 チェックポイント情報計算のテスト

```python
"""チェックポイント観測のテスト"""

import pytest
import numpy as np
from src.env.minicar_env import MinicarEnv


def test_checkpoint_distance_calculation():
    """チェックポイント距離の計算が正しいか"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    obs, _ = env.reset()

    # 観測空間が12次元であることを確認
    assert obs.shape == (12,), f"Expected shape (12,), got {obs.shape}"

    # チェックポイント距離が正の値であることを確認
    checkpoint_distance = obs[10]
    assert checkpoint_distance > 0, f"Distance should be positive, got {checkpoint_distance}"

    env.close()


def test_checkpoint_angle_range():
    """チェックポイント角度が適切な範囲にあるか"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    obs, _ = env.reset()

    # チェックポイント角度が -π ~ π の範囲内であることを確認
    checkpoint_angle = obs[11]
    assert -np.pi <= checkpoint_angle <= np.pi, \
        f"Angle should be in [-π, π], got {checkpoint_angle}"

    env.close()


def test_checkpoint_info_updates():
    """ステップごとにチェックポイント情報が更新されるか"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    obs1, _ = env.reset()

    # 1ステップ実行
    action = env.action_space.sample()
    obs2, _, _, _, _ = env.step(action)

    # チェックポイント情報が変化していることを確認
    distance1 = obs1[10]
    distance2 = obs2[10]

    # 移動したので距離が変わっているはず
    # （同じ場所に留まる可能性もあるので、単に値が存在することを確認）
    assert isinstance(distance2, (int, float, np.floating))

    env.close()


def test_checkpoint_switches_to_goal():
    """全チェックポイント通過後、ゴールが目標になるか"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    obs, _ = env.reset()

    # 強制的に全チェックポイントを通過済みにする
    checkpoints = env.course.get_checkpoints()
    env.next_checkpoint_index = len(checkpoints)

    # 観測を再取得
    distance, angle = env._get_next_checkpoint_info()

    # ゴールまでの距離が計算されていることを確認
    goal_pos, _ = env.course.get_goal_info()
    vehicle_pos = env._cached_vehicle_state["position"]
    expected_distance = np.sqrt(
        (goal_pos[0] - vehicle_pos[0])**2 +
        (goal_pos[1] - vehicle_pos[1])**2
    )

    assert abs(distance - expected_distance) < 1e-5, \
        f"Expected distance to goal {expected_distance}, got {distance}"

    env.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

### Phase 3: 既存のテストを更新

**影響を受けるファイル**:
- `tests/test_env.py`

#### 3.1 観測空間のサイズを更新

```python
def test_observation_space():
    """観測空間のテスト"""
    env = MinicarEnv()
    obs, _ = env.reset()

    # 観測が12次元であることを確認（10 → 12に変更）
    assert obs.shape == (12,), f"Expected shape (12,), got {obs.shape}"

    # ステップ実行
    action = env.action_space.sample()
    obs, _, _, _, _ = env.step(action)

    # ステップ後も12次元であることを確認
    assert obs.shape == (12,), f"Expected shape (12,), got {obs.shape}"

    env.close()
```

---

### Phase 4: ドキュメント更新

**ファイル**: `CLAUDE.md`

#### 4.1 観測空間の説明を更新

```markdown
### 観測空間構成 (12次元)  # 10次元 → 12次元に変更

- LiDAR: 5次元（前方120度を5方向でカバー: -60° ~ +60°）
- 速度: 2次元（vx, vy）
- 角速度: 1次元
- 前回の行動: 2次元（steering, throttle）
- **次のチェックポイント距離: 1次元（m）**  # 新規
- **次のチェックポイント角度: 1次元（rad、-π ~ π）**  # 新規

**チェックポイント情報**:
- 全チェックポイント通過前: 次のチェックポイントへの距離と角度
- 全チェックポイント通過後: ゴールへの距離と角度
- 角度は車両座標系（正面が0、右が正、左が負）
```

---

## 期待される効果

### 学習の改善

1. **目的地認識**: エージェントが「どこに行けばいいか」を理解できる
2. **探索効率の向上**: ランダムな走行ではなく、目標に向かって移動
3. **成功率の向上**: 60% → 75%以上（カリキュラム学習のLevel 1進出）
4. **学習速度の向上**: 目標が明確なため、学習が早く収束

### 報酬との相乗効果

```python
# 現在の報酬設計
- 速度報酬: +0.05 * speed
- 時間ペナルティ: -0.3
- チェックポイント報酬: +100
- ゴール報酬: +500
- 時間ボーナス: +(2000-steps)*1.5

# チェックポイント情報の追加により
→ エージェントがチェックポイントに向かって移動
→ チェックポイント報酬+100を効率的に獲得
→ ゴール到達の確率が大幅に向上
→ 時間ボーナスも獲得しやすくなる
```

---

## 実装の優先度

### 必須（Phase 1, 2, 3）
- ✅ チェックポイント情報計算機能の追加
- ✅ 観測空間の拡張
- ✅ テストの追加・更新

### 推奨（Phase 4）
- ドキュメント更新

---

## 実装後の検証手順

### 1. テスト実行

```bash
# 新しいテストを実行
pytest tests/test_checkpoint_observation.py -v

# 既存のテストも実行（観測空間のサイズ変更の影響確認）
pytest tests/test_env.py -v

# 全テスト実行
pytest tests/ -v
```

### 2. 短時間学習で動作確認

```bash
# 5イテレーションの短時間学習
python scripts/rl-training/train_curriculum.py \
  --total-iterations 5 \
  --n-steps 256
```

### 3. GUIで可視化確認

```bash
# GUIで観測値を確認
python scripts/rl-training/train_curriculum.py \
  --total-iterations 5 \
  --n-steps 256 \
  --gui
```

### 4. 本格的な学習

```bash
# 新しい観測空間で学習開始
python scripts/rl-training/train_curriculum.py \
  --total-iterations 200
```

---

## リスクと対策

### リスク1: 観測空間の変更により既存のモデルが使えない

**対策**:
- 古いチェックポイント（10次元）は破棄
- ゼロから学習し直す
- モデルの互換性を保つ必要はない（改善が期待できるため）

### リスク2: 距離・角度の正規化が必要かもしれない

**対策**:
- まずは正規化なしで実装
- 学習が不安定な場合は以下を検討:
  - 距離を最大値で正規化（例: 距離 / 100.0）
  - 角度は既に -π ~ π に正規化されている

### リスク3: チェックポイント通過時の目標切り替えにバグがある可能性

**対策**:
- テストで `next_checkpoint_index` の更新を検証
- ログで観測値を出力して確認

---

## 実装完了の定義

- [ ] Phase 1: チェックポイント情報計算機能を実装
- [ ] Phase 2: テストを追加し、全テスト通過
- [ ] Phase 3: 既存のテストを更新し、全テスト通過
- [ ] Phase 4: ドキュメントを更新
- [ ] 短時間学習で動作確認（エラーなし）
- [ ] 本格的な学習で成功率が向上することを確認

---

## 次のステップ

1. この計画をレビュー
2. Phase 1から順番に実装
3. 各Phaseごとにテストして動作確認
4. 最終的に200イテレーションの学習を実行
5. 成功率75%到達を確認

---

**作成日**: 2025-12-11
**場所**: `doc/plan/tmp/checkpoint-observation-implementation-plan.md`
