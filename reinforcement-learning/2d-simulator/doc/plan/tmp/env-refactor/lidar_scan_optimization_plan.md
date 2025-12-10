# LiDARスキャン重複実行の最適化 - 実装計画

## 📋 概要

**作成日:** 2025-12-10
**対象ファイル:** `src/env/minicar_env.py`
**優先度:** 🔴 最高
**期待効果:** パフォーマンス 2-5倍向上

---

## 🔍 問題の詳細分析

### 現状の問題

`MinicarEnv.step()` メソッドにおいて、1ステップ内でLiDARスキャンが最大**5回**重複実行されています。

#### 重複実行箇所の特定

| 呼び出し箇所 | ファイル行 | メソッド | 目的 |
|------------|---------|---------|------|
| 1回目 | 155行 | `_get_observation()` | 観測値の取得 |
| 2回目 | 193行 | `_compute_reward()` | 壁接近ペナルティ計算 |
| 3回目 | 228行 | `_check_terminated()` | 壁衝突判定 |
| 4回目 | 243行 | `_get_info()` | デバッグ情報 |
| 5回目 | 286行 | `render()` | 描画（render_mode='human'時のみ） |

#### パフォーマンスへの影響

```python
# LiDARスキャン1回のコスト
- 72本のレイキャスト (デフォルト)
- 各レイキャストでBox2Dの衝突判定を実行
- 推定: 1スキャン ≈ 0.5-2ms (環境による)

# 現状のコスト
- render_mode=None: 4回 × 0.5-2ms = 2-8ms/step
- render_mode='human': 5回 × 0.5-2ms = 2.5-10ms/step

# 最適化後のコスト
- 1回 × 0.5-2ms = 0.5-2ms/step

# 改善率
- 約 75-80% の計算時間削減
```

### 根本原因

1. **データフローの設計不足**: 各メソッドが独立してLiDARデータを取得している
2. **キャッシング機構の欠如**: 同一ステップ内での結果再利用がない
3. **責任分離の不明確**: 誰がLiDARスキャンを実行すべきか明確でない

---

## 💡 解決策の設計

### 基本方針

**「1ステップに1回だけLiDARスキャンを実行し、結果をキャッシュして再利用する」**

### アーキテクチャ設計

```
step() 開始
  ↓
1. 物理シミュレーション実行
  ↓
2. ★ LiDARスキャン実行（1回のみ）
  ↓
3. 結果をインスタンス変数にキャッシュ
  ↓
4. 各メソッドはキャッシュを参照
  ├─ _get_observation() → キャッシュ使用
  ├─ _compute_reward() → キャッシュ使用
  ├─ _check_terminated() → キャッシュ使用
  └─ _get_info() → キャッシュ使用
  ↓
5. render() → キャッシュ使用
  ↓
step() 終了
```

### 技術的な実装アプローチ

#### アプローチ1: シンプルキャッシング（推奨）

```python
class MinicarEnv(gym.Env):
    def __init__(self, ...):
        # ...
        # キャッシュ用の変数を追加
        self._cached_lidar_scan = None
        self._cached_vehicle_state = None

    def step(self, action):
        # 制御と物理シミュレーション
        steering = float(action[0])
        throttle = float(action[1])
        self.vehicle.apply_control(steering, throttle)
        self.world.step()

        # ★ LiDARスキャンを1回だけ実行してキャッシュ
        self._cached_vehicle_state = self.vehicle.get_state()
        self._cached_lidar_scan = self.lidar.scan(
            self._cached_vehicle_state["position"],
            self._cached_vehicle_state["angle"]
        )

        # 各メソッドはキャッシュを使用
        obs = self._get_observation()
        reward = self._compute_reward()
        terminated = self._check_terminated()
        truncated = self.step_count >= self.max_steps
        info = self._get_info()

        # 状態更新
        self.last_action = action
        self.step_count += 1

        return obs, reward, terminated, truncated, info

    def _get_observation(self):
        # キャッシュされたLiDARスキャンを使用
        lidar_scan = self._cached_lidar_scan
        velocity = np.array(self._cached_vehicle_state["velocity"])
        angular_velocity = np.array([self._cached_vehicle_state["angular_velocity"]])

        obs = np.concatenate([
            lidar_scan,
            velocity,
            angular_velocity,
            self.last_action,
        ])
        return obs.astype(np.float32)
```

**メリット:**
- シンプルで理解しやすい
- 既存コードへの変更が最小限
- デバッグしやすい

**デメリット:**
- キャッシュの無効化を手動で管理する必要がある

#### アプローチ2: プロパティベース（より洗練されている）

```python
class MinicarEnv(gym.Env):
    def __init__(self, ...):
        # ...
        self._lidar_scan_cache = None
        self._lidar_scan_cache_valid = False

    @property
    def current_lidar_scan(self):
        """現在のLiDARスキャンを取得（必要に応じて計算）"""
        if not self._lidar_scan_cache_valid:
            state = self.vehicle.get_state()
            self._lidar_scan_cache = self.lidar.scan(
                state["position"],
                state["angle"]
            )
            self._lidar_scan_cache_valid = True
        return self._lidar_scan_cache

    def _invalidate_lidar_cache(self):
        """LiDARキャッシュを無効化"""
        self._lidar_scan_cache_valid = False

    def step(self, action):
        # 制御と物理シミュレーション
        # ...
        self.world.step()

        # キャッシュを無効化（新しい物理状態）
        self._invalidate_lidar_cache()

        # 各メソッドは self.current_lidar_scan を使用
        obs = self._get_observation()
        # ...
```

**メリット:**
- キャッシュの無効化が明示的
- 遅延評価（必要になるまで計算しない）
- 拡張性が高い

**デメリット:**
- コードが若干複雑
- プロパティの理解が必要

---

## 🔨 実装手順

### Step 1: キャッシュ変数の追加

**ファイル:** `src/env/minicar_env.py`

```python
# __init__メソッド内に追加（54行付近）
def __init__(self, ...):
    # ... 既存のコード ...

    # LiDARスキャンのキャッシュ
    self._cached_lidar_scan = None
    self._cached_vehicle_state = None
```

### Step 2: step()メソッドの修正

**ファイル:** `src/env/minicar_env.py:105-143`

```python
def step(self, action: np.ndarray):
    """1ステップ実行"""
    # 行動を適用
    steering = float(action[0])
    throttle = float(action[1])
    self.vehicle.apply_control(steering, throttle)

    # 物理シミュレーション
    self.world.step()

    # ★ 車両状態とLiDARスキャンをキャッシュ（1回のみ実行）
    self._cached_vehicle_state = self.vehicle.get_state()
    self._cached_lidar_scan = self.lidar.scan(
        self._cached_vehicle_state["position"],
        self._cached_vehicle_state["angle"]
    )

    # 観測・報酬・終了判定（キャッシュを使用）
    obs = self._get_observation()
    reward = self._compute_reward()
    terminated = self._check_terminated()
    truncated = self.step_count >= self.max_steps
    info = self._get_info()

    # 状態更新
    self.last_action = action
    self.step_count += 1

    return obs, reward, terminated, truncated, info
```

### Step 3: _get_observation()の修正

**ファイル:** `src/env/minicar_env.py:145-173`

```python
def _get_observation(self) -> np.ndarray:
    """現在の観測を取得"""
    # ★ キャッシュされたデータを使用
    lidar_scan = self._cached_lidar_scan
    velocity = np.array(self._cached_vehicle_state["velocity"])
    angular_velocity = np.array([self._cached_vehicle_state["angular_velocity"]])

    # 観測を結合
    obs = np.concatenate([
        lidar_scan,  # 72
        velocity,  # 2
        angular_velocity,  # 1
        self.last_action,  # 2
    ])

    return obs.astype(np.float32)
```

### Step 4: _compute_reward()の修正

**ファイル:** `src/env/minicar_env.py:175-210`

```python
def _compute_reward(self) -> float:
    """報酬を計算"""
    reward = 0.0
    # ★ キャッシュされた状態を使用
    state = self._cached_vehicle_state
    lidar_scan = self._cached_lidar_scan

    # 1. 速度報酬
    speed = state["speed"]
    reward += speed * 0.1

    # 2. 時間ペナルティ
    reward -= 0.01

    # 3. 壁接近ペナルティ（★ キャッシュされたLiDARを使用）
    min_distance = np.min(lidar_scan)
    if min_distance < 0.3:
        reward -= (0.3 - min_distance) * 10

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

### Step 5: _check_terminated()の修正

**ファイル:** `src/env/minicar_env.py:212-233`

```python
def _check_terminated(self) -> bool:
    """終了条件をチェック"""
    # ★ キャッシュされたデータを使用
    state = self._cached_vehicle_state
    lidar_scan = self._cached_lidar_scan

    # ゴール到達
    checkpoints = self.course.get_checkpoints()
    all_checkpoints_passed = len(self.checkpoints_passed) == len(checkpoints)
    if all_checkpoints_passed and self.course.check_goal(state["position"]):
        return True

    # 壁衝突（★ キャッシュされたLiDARを使用）
    min_distance = np.min(lidar_scan)
    if min_distance < 0.1:
        return True

    return False
```

### Step 6: _get_info()の修正

**ファイル:** `src/env/minicar_env.py:235-253`

```python
def _get_info(self) -> Dict[str, Any]:
    """追加情報を取得"""
    # ★ キャッシュされたデータを使用
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
    }
```

### Step 7: render()の修正

**ファイル:** `src/env/minicar_env.py:255-306`

```python
def render(self):
    """環境を描画"""
    if self.render_mode != "human":
        return

    if self.renderer is None:
        self.renderer = Renderer()

    # 画面クリア
    self.renderer.clear()

    # ★ キャッシュされた状態を使用
    state = self._cached_vehicle_state

    # カメラを車両に追従
    self.renderer.set_camera(state["position"][0], state["position"][1])

    # 壁を描画
    self.renderer.draw_walls(self.course.walls)

    # チェックポイントを描画
    checkpoints = self.course.get_checkpoints()
    for i, cp in enumerate(checkpoints):
        if i not in self.checkpoints_passed:
            self.renderer.draw_checkpoint(
                tuple(cp["position"]), cp.get("radius", 1.0)
            )

    # ゴールを描画
    goal_pos, goal_radius = self.course.get_goal_info()
    self.renderer.draw_goal(goal_pos, goal_radius)

    # LiDARを描画（★ キャッシュされたLiDARを使用）
    self.renderer.draw_lidar(
        state["position"],
        state["angle"],
        self._cached_lidar_scan,  # キャッシュを使用
        num_rays=72
    )

    # 車両を描画
    self.renderer.draw_vehicle(state["position"], state["angle"])

    # デバッグ情報
    info = self._get_info()
    debug_info = {
        "Speed": info["speed"],
        "Step": info["step_count"],
        "Reward": info["total_reward"],
        "CPs": f"{info['checkpoints_passed']}/{len(checkpoints)}",
        "Min Dist": info["min_distance"],
    }
    self.renderer.draw_debug_info(debug_info)

    # 画面更新
    self.renderer.update()
```

### Step 8: reset()メソッドの修正

**ファイル:** `src/env/minicar_env.py:78-103`

```python
def reset(self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None):
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

    # ★ キャッシュをリセット
    self._cached_vehicle_state = self.vehicle.get_state()
    self._cached_lidar_scan = self.lidar.scan(
        self._cached_vehicle_state["position"],
        self._cached_vehicle_state["angle"]
    )

    # 初期観測
    obs = self._get_observation()
    info = self._get_info()

    return obs, info
```

---

## 🧪 テスト計画

### 1. 機能テスト

#### テスト1: 基本動作の確認

```python
# test_lidar_optimization.py
import numpy as np
from src.env.minicar_env import MinicarEnv

def test_basic_functionality():
    """基本的な動作が変わっていないことを確認"""
    env = MinicarEnv(render_mode=None)

    # リセット
    obs, info = env.reset()
    assert obs.shape == (77,), "観測空間のサイズが正しい"

    # ステップ実行
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)

    assert obs.shape == (77,), "観測が正しく返される"
    assert isinstance(reward, float), "報酬が返される"
    assert isinstance(terminated, bool), "終了フラグが返される"
    assert "min_distance" in info, "情報辞書が正しい"

    env.close()
    print("✅ 基本動作テスト: PASS")
```

#### テスト2: キャッシュの整合性確認

```python
def test_cache_consistency():
    """キャッシュされたデータが一貫していることを確認"""
    env = MinicarEnv(render_mode=None)
    env.reset()

    # 1ステップ実行
    action = np.array([0.5, 0.8])
    obs, reward, terminated, truncated, info = env.step(action)

    # キャッシュの存在確認
    assert env._cached_lidar_scan is not None, "LiDARキャッシュが存在する"
    assert env._cached_vehicle_state is not None, "状態キャッシュが存在する"

    # キャッシュとget_state()の一致確認
    current_state = env.vehicle.get_state()
    assert env._cached_vehicle_state["position"] == current_state["position"], \
        "位置が一致"
    assert env._cached_vehicle_state["angle"] == current_state["angle"], \
        "角度が一致"

    env.close()
    print("✅ キャッシュ整合性テスト: PASS")
```

### 2. パフォーマンステスト

```python
import time

def test_performance_improvement():
    """パフォーマンスの改善を測定"""
    env = MinicarEnv(render_mode=None)
    env.reset()

    # 1000ステップ実行して時間を測定
    num_steps = 1000
    start_time = time.time()

    for _ in range(num_steps):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            env.reset()

    elapsed_time = time.time() - start_time
    fps = num_steps / elapsed_time

    print(f"✅ パフォーマンステスト:")
    print(f"   - 実行時間: {elapsed_time:.2f}秒")
    print(f"   - FPS: {fps:.1f}")
    print(f"   - 1ステップあたり: {elapsed_time/num_steps*1000:.2f}ms")

    env.close()
```

### 3. 回帰テスト

```python
def test_observation_consistency():
    """観測値が変更前と同じであることを確認"""
    env = MinicarEnv(render_mode=None, course_file="courses/easy/simple_oval.json")

    # シード固定
    obs1, _ = env.reset(seed=42)

    # 決定的な行動を取る
    actions = [
        np.array([0.0, 1.0]),  # 真っ直ぐ前進
        np.array([0.5, 1.0]),  # 右に曲がりながら前進
        np.array([-0.5, 0.5]), # 左に曲がりながら減速
    ]

    observations = []
    for action in actions:
        obs, _, _, _, _ = env.step(action)
        observations.append(obs.copy())

    # 同じシードで再実行
    env.reset(seed=42)
    for i, action in enumerate(actions):
        obs, _, _, _, _ = env.step(action)
        assert np.allclose(obs, observations[i], atol=1e-5), \
            f"ステップ{i}の観測値が一致する"

    env.close()
    print("✅ 観測値一貫性テスト: PASS")
```

### 4. レンダリングテスト

```python
def test_rendering_with_cache():
    """レンダリングモードでもキャッシュが機能することを確認"""
    env = MinicarEnv(render_mode="human")
    env.reset()

    # 数ステップ実行してレンダリング
    for _ in range(10):
        action = env.action_space.sample()
        obs, _, terminated, truncated, _ = env.step(action)
        env.render()

        if terminated or truncated:
            break

    env.close()
    print("✅ レンダリングテスト: PASS")
```

---

## ⚠️ 注意点とリスク

### 注意点

1. **キャッシュの無効化タイミング**
   - `step()`の最初にキャッシュが更新される
   - `reset()`でもキャッシュを初期化する必要がある

2. **車両状態の同期**
   - `_cached_vehicle_state`と実際の車両状態が同期していることを保証する
   - 物理シミュレーション後に必ずキャッシュを更新する

3. **メモリ使用量**
   - LiDARスキャン: 72個のfloat (約0.3KB)
   - 車両状態: 辞書 (約0.1KB)
   - **影響は無視できるレベル**

### 潜在的なリスク

| リスク | 影響度 | 対策 |
|--------|--------|------|
| キャッシュの不整合 | 中 | テストで検証、アサーション追加 |
| reset()でのキャッシュ初期化忘れ | 低 | テストケースでカバー |
| 複数環境並列実行時の問題 | 低 | 各環境インスタンスが独立したキャッシュを持つ |

### デバッグのヒント

```python
# デバッグ用のアサーションを追加（開発中のみ）
def _get_observation(self):
    assert self._cached_lidar_scan is not None, \
        "LiDARキャッシュが初期化されていません"
    # ...
```

---

## 📊 期待される効果

### パフォーマンス改善

| 指標 | 変更前 | 変更後 | 改善率 |
|------|--------|--------|--------|
| LiDARスキャン回数/step | 4-5回 | 1回 | 75-80%削減 |
| 計算時間/step | 2-10ms | 0.5-2ms | 75-80%削減 |
| トレーニング速度 (FPS) | 100-200 | 400-1000 | 2-5倍向上 |

### コード品質

- ✅ **可読性向上**: データフローが明確になる
- ✅ **保守性向上**: 変更箇所が1箇所に集約される
- ✅ **拡張性向上**: 他のセンサーにも同じパターンを適用できる

---

## 🚀 実装スケジュール

| フェーズ | 作業内容 | 所要時間 | 担当 |
|---------|---------|---------|------|
| Phase 1 | Step 1-3の実装 | 30分 | - |
| Phase 2 | Step 4-8の実装 | 30分 | - |
| Phase 3 | テストコード作成 | 30分 | - |
| Phase 4 | テスト実行と修正 | 30分 | - |
| Phase 5 | パフォーマンス測定 | 15分 | - |
| **合計** | | **約2時間15分** | |

---

## ✅ チェックリスト

### 実装前

- [ ] 現在のコードのバックアップを取る
- [ ] 変更前のパフォーマンスを測定する（ベースライン）
- [ ] テストケースを準備する

### 実装中

- [ ] Step 1: キャッシュ変数の追加
- [ ] Step 2: step()メソッドの修正
- [ ] Step 3: _get_observation()の修正
- [ ] Step 4: _compute_reward()の修正
- [ ] Step 5: _check_terminated()の修正
- [ ] Step 6: _get_info()の修正
- [ ] Step 7: render()の修正
- [ ] Step 8: reset()の修正

### 実装後

- [ ] 全テストケースをパス
- [ ] パフォーマンステストで改善を確認
- [ ] コードレビュー
- [ ] ドキュメント更新
- [ ] コミット＆プッシュ

---

## 📝 関連ドキュメント

- 元の問題分析: `doc/analysis/env_code_review.md`（もし存在すれば）
- テストコード: `tests/test_lidar_optimization.py`（実装予定）
- パフォーマンスベンチマーク: `benchmarks/lidar_performance.py`（実装予定）

---

## 🔄 今後の拡張

この最適化パターンは、他の重い計算にも適用できます:

1. **衝突検出のキャッシング**
   - 壁との衝突判定を1回だけ実行

2. **チェックポイント判定のキャッシング**
   - チェックポイント通過判定を最適化

3. **より高度なキャッシング戦略**
   - ステップ番号でキャッシュを管理
   - 複数フレームのキャッシュ

---

**実装準備完了。この計画に基づいて実装を開始できます。**
