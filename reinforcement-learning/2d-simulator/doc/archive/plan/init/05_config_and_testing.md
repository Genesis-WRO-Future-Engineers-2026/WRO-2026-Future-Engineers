# 設定ファイルとテスト戦略

## 1. 設定ファイルのサンプル

### 1.1 環境設定 (configs/env_config.yaml)

```yaml
# 環境設定
env:
  # コース設定
  course_file: "courses/easy/simple_oval.json"

  # 車両パラメータ
  vehicle:
    width: 0.2        # m
    length: 0.4       # m
    mass: 1.0         # kg
    max_steering_angle: 0.5  # rad (約28度)
    max_motor_force: 20.0    # N
    friction_coefficient: 0.7

  # LiDARセンサー
  lidar:
    num_rays: 72
    max_range: 10.0   # m
    angle_min: 0      # rad
    angle_max: 6.28   # rad (2π)
    noise_level: 0.01 # 距離の1%のノイズ

  # シミュレーション
  simulation:
    time_step: 0.05   # 20Hz
    max_episode_steps: 2000
    physics_substeps: 4

  # レンダリング
  rendering:
    enabled: true
    fps: 30
    screen_width: 800
    screen_height: 600
    pixels_per_meter: 50

# 報酬設定
reward:
  # 前進報酬
  progress_reward: 1.0
  speed_reward: 0.1

  # ペナルティ
  time_penalty: -0.01
  wall_proximity_threshold: 0.3
  wall_proximity_penalty: -10.0
  collision_penalty: -100.0

  # ボーナス
  goal_bonus: 500.0
  checkpoint_bonus: 50.0
```

### 1.2 学習設定 (configs/training_config.yaml)

```yaml
# PPO設定
ppo:
  learning_rate: 3.0e-4
  batch_size: 256
  num_epochs: 10
  clip_ratio: 0.2
  entropy_coef: 0.01
  value_coef: 0.5
  max_grad_norm: 0.5

  # GAE
  gamma: 0.99
  gae_lambda: 0.95

# バッファ設定
buffer:
  capacity: 4096

# 学習ループ
training:
  total_timesteps: 1000000
  eval_frequency: 10000
  save_frequency: 50000
  num_eval_episodes: 10

  # 学習率スケジュール
  lr_schedule:
    type: "linear"  # constant, linear, exponential
    final_lr: 1.0e-5

# カリキュラム学習
curriculum:
  enabled: true
  courses:
    - "courses/easy/wide_oval.json"
    - "courses/medium/narrow_oval.json"
    - "courses/hard/shortcut_1.json"
  success_threshold: 0.8
  min_episodes_per_level: 50

# Domain Randomization
domain_randomization:
  enabled: true
  physics:
    friction_range: [0.5, 1.5]
    mass_range: [0.8, 1.2]
    motor_delay_range: [0.0, 0.05]
  sensor:
    lidar_noise_range: [0.005, 0.02]
    lidar_dropout_prob: 0.05

# ロギング
logging:
  tensorboard_dir: "logs/tensorboard"
  log_frequency: 100  # ステップごと
  video_frequency: 10000  # 動画保存頻度
```

### 1.3 モデル設定 (configs/model_config.yaml)

```yaml
# ポリシーネットワーク
policy:
  hidden_sizes: [256, 256]
  activation: "relu"
  log_std_init: -0.5

# 価値関数ネットワーク
value:
  hidden_sizes: [256, 256]
  activation: "relu"

# 正規化
normalization:
  obs_normalize: true
  reward_normalize: true
  clip_obs: 10.0
  clip_reward: 10.0
```

---

## 2. テスト戦略

### 2.1 ユニットテスト

#### 環境テスト (tests/test_env.py)
```python
import pytest
from src.env.minicar_env import MinicarEnv

def test_env_reset():
    """環境リセットのテスト"""
    env = MinicarEnv(config)
    obs, info = env.reset()

    assert obs.shape == (77,)
    assert 'position' in info

def test_env_step():
    """ステップ実行のテスト"""
    env = MinicarEnv(config)
    env.reset()

    action = np.array([0.0, 0.5])  # まっすぐ前進
    obs, reward, terminated, truncated, info = env.step(action)

    assert obs.shape == (77,)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)

def test_collision_detection():
    """衝突検出のテスト"""
    env = MinicarEnv(config)
    env.reset()

    # 壁に向かって全速力
    for _ in range(100):
        obs, reward, terminated, truncated, info = env.step([1.0, 1.0])
        if terminated:
            assert reward < -50  # 衝突ペナルティ
            break
```

#### 車両テスト (tests/test_vehicle.py)
```python
def test_vehicle_motion():
    """車両の動きのテスト"""
    world = PhysicsWorld()
    vehicle = Vehicle(world.world, (0, 0), 0)

    # 前進
    vehicle.apply_control(steering=0.0, throttle=1.0)
    for _ in range(100):
        world.step()

    # 前方に移動したか確認
    assert vehicle.get_state()['position'][0] > 0

def test_steering():
    """ステアリングのテスト"""
    world = PhysicsWorld()
    vehicle = Vehicle(world.world, (0, 0), 0)

    # 右に旋回
    vehicle.apply_control(steering=1.0, throttle=0.5)
    for _ in range(100):
        world.step()

    # 角度が変化したか確認
    assert abs(vehicle.get_state()['angle']) > 0.1
```

#### LiDARテスト (tests/test_sensors.py)
```python
def test_lidar_scan():
    """LiDARスキャンのテスト"""
    world = PhysicsWorld()
    # 簡単な壁を作成
    world.add_static_polygon([(5, -5), (5, 5), (5.1, 5), (5.1, -5)])

    lidar = LiDARSensor(world.world)
    distances = lidar.scan(position=(0, 0), orientation=0)

    assert len(distances) == 72
    assert np.min(distances) > 0
    assert np.min(distances) < lidar.max_range

def test_lidar_noise():
    """LiDARノイズのテスト"""
    lidar = LiDARSensor(...)
    clean_scan = np.ones(72) * 5.0

    noisy_scan = lidar.add_noise(clean_scan, noise_level=0.1)

    # ノイズが追加されている
    assert not np.allclose(clean_scan, noisy_scan)
    # 範囲内
    assert np.all(noisy_scan >= 0)
```

#### PPOテスト (tests/test_ppo.py)
```python
def test_policy_forward():
    """ポリシーの順伝播テスト"""
    policy = GaussianPolicy(obs_dim=77, action_dim=2)
    obs = torch.randn(32, 77)

    mean, log_std = policy.forward(obs)

    assert mean.shape == (32, 2)
    assert log_std.shape == (32, 2)

def test_policy_sample():
    """ポリシーのサンプリングテスト"""
    policy = GaussianPolicy(obs_dim=77, action_dim=2)
    obs = torch.randn(32, 77)

    action, log_prob = policy.sample(obs)

    assert action.shape == (32, 2)
    assert log_prob.shape == (32,)

def test_ppo_update():
    """PPO更新のテスト"""
    policy = GaussianPolicy(...)
    value = ValueNetwork(...)
    ppo = PPO(policy, value, config)

    buffer = create_dummy_buffer()

    stats = ppo.update(buffer)

    assert 'policy_loss' in stats
    assert 'value_loss' in stats
```

### 2.2 統合テスト

#### エンドツーエンドテスト
```python
def test_full_training_loop():
    """完全な学習ループのテスト（短時間版）"""
    env = MinicarEnv(config)
    policy = GaussianPolicy(...)
    value = ValueNetwork(...)
    ppo = PPO(policy, value, config)

    # 100エピソードだけ学習
    for episode in range(100):
        obs, _ = env.reset()
        done = False

        while not done:
            action, log_prob = policy.sample(torch.from_numpy(obs))
            next_obs, reward, terminated, truncated, info = env.step(action.numpy())
            done = terminated or truncated
            obs = next_obs

        if episode % 10 == 0:
            ppo.update(buffer)

    # 学習が進んでいることを確認
    assert get_average_reward() > initial_reward
```

### 2.3 パフォーマンステスト

```python
def test_simulation_speed():
    """シミュレーション速度のテスト"""
    env = MinicarEnv(config)
    env.reset()

    start_time = time.time()
    for _ in range(1000):
        env.step(env.action_space.sample())
    elapsed = time.time() - start_time

    # 1000ステップが1秒以内
    assert elapsed < 1.0

def test_training_throughput():
    """学習スループットのテスト"""
    # リアルタイムの10倍以上のスピード目標
    ...
```

### 2.4 CI/CD設定

#### GitHub Actions (.github/workflows/test.yml)
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## 3. デバッグとトラブルシューティング

### 3.1 よくある問題

#### 問題1: 学習が収束しない
**症状:** 報酬が増えない、ランダムな動きを続ける

**チェック項目:**
1. 報酬スケールが適切か（報酬の範囲を確認）
2. 学習率が適切か（大きすぎる/小さすぎる）
3. 観測の正規化が機能しているか
4. ポリシーのエントロピーが十分か（探索が足りない）

**解決策:**
```python
# 報酬の範囲を確認
print(f"Reward range: {np.min(rewards)} to {np.max(rewards)}")

# エントロピーを増やす
config['entropy_coef'] = 0.05  # デフォルト0.01から増加

# 学習率を調整
config['learning_rate'] = 1e-4
```

#### 問題2: シミュレーションが遅い
**症状:** リアルタイムより遅い

**チェック項目:**
1. レンダリングが有効になっていないか
2. 物理演算のサブステップが多すぎないか
3. LiDARのレイ数が多すぎないか

**解決策:**
```yaml
# レンダリングを無効化
rendering:
  enabled: false

# 物理サブステップを減らす
simulation:
  physics_substeps: 2  # デフォルト4から削減
```

#### 問題3: 壁を抜ける
**症状:** 車両が壁をすり抜ける

**チェック項目:**
1. 物理ステップが大きすぎる
2. 車両速度が速すぎる
3. 衝突検出が機能していない

**解決策:**
```yaml
simulation:
  time_step: 0.02  # より小さいステップ
  physics_substeps: 8  # サブステップを増やす

vehicle:
  max_motor_force: 10.0  # 最大力を減らす
```

### 3.2 可視化とデバッグツール

#### 学習曲線の可視化
```python
# scripts/plot_learning_curve.py
import matplotlib.pyplot as plt
from tensorboard.backend.event_processing import event_accumulator

def plot_rewards(log_dir):
    ea = event_accumulator.EventAccumulator(log_dir)
    ea.Reload()

    rewards = ea.Scalars('reward/episode')
    steps = [r.step for r in rewards]
    values = [r.value for r in rewards]

    plt.plot(steps, values)
    plt.xlabel('Steps')
    plt.ylabel('Episode Reward')
    plt.title('Learning Curve')
    plt.savefig('learning_curve.png')
```

#### 軌跡の可視化
```python
# scripts/visualize_trajectory.py
def visualize_trajectory(model_path, course_path):
    env = MinicarEnv(...)
    policy = load_model(model_path)

    obs, _ = env.reset()
    trajectory = []

    for _ in range(1000):
        action, _ = policy.sample(obs)
        obs, reward, done, _, info = env.step(action)
        trajectory.append(info['position'])

        if done:
            break

    # 軌跡をプロット
    trajectory = np.array(trajectory)
    plt.plot(trajectory[:, 0], trajectory[:, 1])
    plt.savefig('trajectory.png')
```

---

## 4. ベストプラクティス

### 4.1 開発フロー

1. **機能ブランチ**: `feature/lidar-sensor`
2. **テスト駆動開発**: 先にテストを書く
3. **コードレビュー**: PRでレビュー
4. **CI/CD**: 自動テスト実行
5. **マージ**: `develop` → `main`

### 4.2 コミットメッセージ

```
[type] 簡潔な説明

詳細な説明（必要に応じて）

type: feat, fix, docs, test, refactor
```

例:
```
[feat] LiDARセンサーのノイズモデルを実装

ガウシアンノイズとドロップアウトを追加。
Domain Randomizationで使用。
```

### 4.3 ドキュメント

- **docstring**: すべての関数・クラスに記述
- **型ヒント**: 可能な限り使用
- **README**: セットアップ手順を明記
- **CHANGELOG**: 変更履歴を記録

---

## 5. パフォーマンスチューニング

### 5.1 学習の高速化

1. **並列環境**: 複数の環境を並列実行
```python
from gymnasium.vector import AsyncVectorEnv

envs = AsyncVectorEnv([
    lambda: MinicarEnv(config) for _ in range(8)
])
```

2. **GPU活用**: ネットワーク計算をGPUで実行
```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
policy.to(device)
value.to(device)
```

3. **効率的なバッファ**: NumPy配列を使用

### 5.2 推論の高速化

1. **ONNX変換**: 実機デプロイ用
2. **モデル量子化**: 精度を維持しつつサイズ削減
3. **バッチ推論**: 可能であればバッチで処理

---

## まとめ

テスト戦略と設定管理を適切に行うことで、開発効率と品質を向上させることができます。特にユニットテストは開発の初期段階から導入し、継続的にメンテナンスすることが重要です。
