# Domain Randomization実装計画 - テスト戦略

## 1. テスト全体構成

Domain Randomizationの実装には、以下の3つのレベルのテストが必要です。

### 1.1 テストレベル

| レベル | 目的 | 実行タイミング |
|--------|------|--------------|
| **ユニットテスト** | 各モジュールの個別機能を検証 | 実装直後 |
| **統合テスト** | モジュール間の連携を検証 | Phase 2完了後 |
| **学習テスト** | 実際の学習での動作を検証 | Phase 3完了後 |

---

## 2. ユニットテスト

### 2.1 PhysicsRandomizerのテスト

#### ファイル: `tests/test_physics_randomizer.py`

```python
"""PhysicsRandomizerのユニットテスト"""

import pytest
import numpy as np
from src.domain_randomization.physics_randomizer import (
    PhysicsRandomizer,
    PhysicsRandomizationConfig,
    DEFAULT_PHYSICS_CONFIG,
    MILD_PHYSICS_CONFIG,
    STRONG_PHYSICS_CONFIG,
)


def test_physics_randomizer_initialization():
    """初期化のテスト"""
    config = PhysicsRandomizationConfig()
    randomizer = PhysicsRandomizer(config)

    assert randomizer.config == config
    assert randomizer._rng is not None


def test_physics_randomizer_default_params():
    """デフォルトパラメータのテスト"""
    config = PhysicsRandomizationConfig()
    randomizer = PhysicsRandomizer(config)

    default_params = randomizer.get_default_params()

    assert default_params['friction'] == 0.7
    assert default_params['mass'] == 1.4
    assert default_params['motor_force'] == 20.0


def test_physics_randomizer_range():
    """ランダム化範囲のテスト"""
    config = PhysicsRandomizationConfig()
    randomizer = PhysicsRandomizer(config)

    # 100回ランダム化して範囲を確認
    for _ in range(100):
        params = randomizer.randomize()

        # 摩擦係数
        assert 0.5 <= params['friction'] <= 1.0

        # 質量
        assert 1.2 <= params['mass'] <= 1.6

        # 慣性スケール
        assert 0.8 <= params['inertia_scale'] <= 1.2

        # モーター力
        assert 18.0 <= params['motor_force'] <= 22.0

        # モーター遅延
        assert 0.0 <= params['motor_delay'] <= 0.05

        # 線形減衰
        assert 0.4 <= params['linear_damping'] <= 0.6

        # 角減衰
        assert 0.6 <= params['angular_damping'] <= 1.0

        # 最大横滑りインパルス
        assert 2.0 <= params['max_lateral_impulse'] <= 3.0


def test_physics_randomizer_reproducibility():
    """再現性のテスト（シードが同じなら同じ結果）"""
    config1 = PhysicsRandomizationConfig(seed=42)
    config2 = PhysicsRandomizationConfig(seed=42)

    randomizer1 = PhysicsRandomizer(config1)
    randomizer2 = PhysicsRandomizer(config2)

    params1 = randomizer1.randomize()
    params2 = randomizer2.randomize()

    # 同じシードなら同じパラメータ
    assert params1['friction'] == params2['friction']
    assert params1['mass'] == params2['mass']
    assert params1['motor_force'] == params2['motor_force']


def test_physics_randomizer_disabled():
    """ランダム化無効のテスト"""
    config = PhysicsRandomizationConfig(
        friction_range=None,
        mass_range=None,
        motor_force_range=None,
    )
    randomizer = PhysicsRandomizer(config)

    params = randomizer.randomize()

    # デフォルト値が返される
    assert params['friction'] == 0.7
    assert params['mass'] == 1.4
    assert params['motor_force'] == 20.0


def test_preset_configs():
    """プリセット設定のテスト"""
    # デフォルト設定
    assert DEFAULT_PHYSICS_CONFIG.friction_range == (0.5, 1.0)

    # Mild設定
    assert MILD_PHYSICS_CONFIG.friction_range == (0.6, 0.8)

    # Strong設定
    assert STRONG_PHYSICS_CONFIG.friction_range == (0.5, 1.0)
```

---

### 2.2 SensorNoiseRandomizerのテスト

#### ファイル: `tests/test_sensor_noise.py`

```python
"""SensorNoiseRandomizerのユニットテスト"""

import pytest
import numpy as np
from src.env.sensors import LiDARSensor
from src.physics.box2d_wrapper import PhysicsWorld
from src.domain_randomization.sensor_noise import (
    SensorNoiseRandomizer,
    SensorNoiseConfig,
    DEFAULT_SENSOR_NOISE_CONFIG,
)


@pytest.fixture
def lidar_sensor():
    """LiDARセンサーのフィクスチャ"""
    world = PhysicsWorld()
    return LiDARSensor(world.world, num_rays=5, max_range=3.0)


def test_sensor_noise_initialization():
    """初期化のテスト"""
    config = SensorNoiseConfig()
    randomizer = SensorNoiseRandomizer(config)

    assert randomizer.config == config


def test_sensor_noise_params_range():
    """ノイズパラメータ範囲のテスト"""
    config = SensorNoiseConfig()
    randomizer = SensorNoiseRandomizer(config)

    # 100回パラメータ生成して範囲を確認
    for _ in range(100):
        params = randomizer.get_noise_params()

        assert 0.01 <= params['noise_level'] <= 0.02
        assert 0.02 <= params['dropout_prob'] <= 0.05
        assert 0.005 <= params['spike_prob'] <= 0.01


def test_sensor_noise_apply(lidar_sensor):
    """ノイズ適用のテスト"""
    config = SensorNoiseConfig()
    randomizer = SensorNoiseRandomizer(config)

    # クリーンなスキャン
    clean_scan = np.array([1.0, 1.5, 2.0, 2.5, 3.0])

    # ノイズ適用
    noisy_scan = randomizer.apply_noise(lidar_sensor, clean_scan.copy())

    # 形状は同じ
    assert noisy_scan.shape == clean_scan.shape

    # 値は変わっている（高確率で）
    # NOTE: 低確率で全く同じになる可能性があるので、厳密なassertは避ける
    assert not np.allclose(noisy_scan, clean_scan, atol=0.001)

    # 範囲内（0～max_range）
    assert np.all(noisy_scan >= 0.0)
    assert np.all(noisy_scan <= 3.0)


def test_sensor_noise_reproducibility(lidar_sensor):
    """再現性のテスト"""
    config1 = SensorNoiseConfig(seed=42)
    config2 = SensorNoiseConfig(seed=42)

    randomizer1 = SensorNoiseRandomizer(config1)
    randomizer2 = SensorNoiseRandomizer(config2)

    clean_scan = np.array([1.0, 1.5, 2.0, 2.5, 3.0])

    noisy_scan1 = randomizer1.apply_noise(lidar_sensor, clean_scan.copy())
    noisy_scan2 = randomizer2.apply_noise(lidar_sensor, clean_scan.copy())

    # 同じシードなら同じノイズ
    np.testing.assert_array_almost_equal(noisy_scan1, noisy_scan2)


def test_sensor_noise_disabled(lidar_sensor):
    """ノイズ無効のテスト"""
    config = SensorNoiseConfig(
        noise_level_range=(0.0, 0.0),
        dropout_prob_range=(0.0, 0.0),
        spike_prob_range=(0.0, 0.0),
    )
    randomizer = SensorNoiseRandomizer(config)

    clean_scan = np.array([1.0, 1.5, 2.0, 2.5, 3.0])
    noisy_scan = randomizer.apply_noise(lidar_sensor, clean_scan.copy())

    # ノイズなしなので同じ
    np.testing.assert_array_equal(noisy_scan, clean_scan)
```

---

### 2.3 実行方法

```bash
# すべてのDomain Randomizationテストを実行
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"
pytest tests/test_physics_randomizer.py tests/test_sensor_noise.py -v
```

---

## 3. 統合テスト

### 3.1 環境統合テスト

#### ファイル: `tests/test_env_domain_randomization.py`

```python
"""MinicarEnvのDomain Randomization統合テスト"""

import pytest
import numpy as np
from src.env.minicar_env import MinicarEnv
from src.domain_randomization import get_config


def test_env_with_dr_disabled():
    """Domain Randomization無効のテスト"""
    env = MinicarEnv(
        course_file="courses/easy/simple_oval.json",
        enable_domain_randomization=False,
    )

    obs, info = env.reset()

    assert obs.shape == (10,)
    assert env.physics_randomizer is None
    assert env.sensor_noise_randomizer is None


def test_env_with_dr_enabled():
    """Domain Randomization有効のテスト"""
    config = get_config('mild')

    env = MinicarEnv(
        course_file="courses/easy/simple_oval.json",
        enable_domain_randomization=True,
        physics_randomization_config=config['physics'],
        sensor_noise_config=config['sensor'],
    )

    obs, info = env.reset()

    assert obs.shape == (10,)
    assert env.physics_randomizer is not None
    assert env.sensor_noise_randomizer is not None


def test_env_randomization_varies():
    """エピソードごとにパラメータが変わることを確認"""
    config = get_config('mild')

    env = MinicarEnv(
        course_file="courses/easy/simple_oval.json",
        enable_domain_randomization=True,
        physics_randomization_config=config['physics'],
        sensor_noise_config=config['sensor'],
    )

    # 複数回リセットして観測が変わることを確認
    observations = []
    for _ in range(5):
        obs, _ = env.reset()
        observations.append(obs.copy())

        # 1ステップ実行（センサーノイズの確認）
        action = env.action_space.sample()
        obs, _, _, _, _ = env.step(action)

    # 少なくとも一部は異なる観測になっているはず
    # （完全に同じになる確率は極めて低い）
    all_same = all(np.allclose(observations[0], obs) for obs in observations[1:])
    assert not all_same, "Observations should vary across episodes"


def test_env_multiple_steps():
    """複数ステップの実行テスト"""
    config = get_config('standard')

    env = MinicarEnv(
        course_file="courses/easy/simple_oval.json",
        enable_domain_randomization=True,
        physics_randomization_config=config['physics'],
        sensor_noise_config=config['sensor'],
    )

    obs, _ = env.reset()

    for _ in range(10):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)

        assert obs.shape == (10,)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)

        if terminated or truncated:
            break


def test_env_config_levels():
    """各設定レベルで環境が作成できることを確認"""
    for level in ['disabled', 'mild', 'standard', 'strong']:
        if level == 'disabled':
            env = MinicarEnv(
                course_file="courses/easy/simple_oval.json",
                enable_domain_randomization=False,
            )
        else:
            config = get_config(level)
            env = MinicarEnv(
                course_file="courses/easy/simple_oval.json",
                enable_domain_randomization=True,
                physics_randomization_config=config['physics'],
                sensor_noise_config=config['sensor'],
            )

        obs, _ = env.reset()
        assert obs.shape == (10,)
```

---

### 3.2 実行方法

```bash
pytest tests/test_env_domain_randomization.py -v
```

---

## 4. 学習テスト

### 4.1 短時間学習テスト

Domain Randomizationを有効にして、短時間（10-20イテレーション）の学習が正常に完了することを確認します。

```bash
# Mild設定でテスト
python scripts/rl-training/train.py \
  --course courses/easy/simple_oval.json \
  --total-iterations 10 \
  --enable-domain-randomization \
  --dr-level mild \
  --n-steps 512 \
  --batch-size 64

# Standard設定でテスト
python scripts/rl-training/train.py \
  --course courses/easy/simple_oval.json \
  --total-iterations 20 \
  --enable-domain-randomization \
  --dr-level standard \
  --n-steps 1024
```

### 4.2 比較テスト

Domain Randomizationあり/なしで学習を比較します。

#### テスト設定

| 項目 | Domain Randomizationなし | Domain Randomizationあり |
|------|----------------------|----------------------|
| **コース** | simple_oval.json | simple_oval.json |
| **イテレーション** | 100 | 100 |
| **設定レベル** | N/A | standard |

#### 実行コマンド

```bash
# Domain Randomizationなし
python scripts/rl-training/train.py \
  --course courses/easy/simple_oval.json \
  --total-iterations 100 \
  --save-freq 10 \
  --checkpoint-dir models/checkpoints/no_dr

# Domain Randomizationあり
python scripts/rl-training/train.py \
  --course courses/easy/simple_oval.json \
  --total-iterations 100 \
  --enable-domain-randomization \
  --dr-level standard \
  --save-freq 10 \
  --checkpoint-dir models/checkpoints/with_dr
```

#### 評価指標

| 指標 | 目標 | 測定方法 |
|------|------|---------|
| **学習の収束** | 両方とも収束 | TensorBoardで報酬曲線を確認 |
| **最終報酬** | DR有 ≥ 80% of DR無 | 最後の10イテレーションの平均 |
| **安定性** | DR有の方が分散小 | 報酬の標準偏差を比較 |
| **成功率** | DR有 ≥ 70% | 評価エピソードでのゴール到達率 |

### 4.3 TensorBoardでの確認

```bash
# TensorBoard起動
tensorboard --logdir=logs

# ブラウザで http://localhost:6006 を開く
# 以下を確認:
# - 報酬曲線（平滑化して比較）
# - エピソード長
# - 損失関数の推移
```

---

## 5. パフォーマンステスト

### 5.1 計算コストの測定

Domain Randomizationによるオーバーヘッドを測定します。

```python
# test_performance.py
import time
import numpy as np
from src.env.minicar_env import MinicarEnv
from src.domain_randomization import get_config


def benchmark_env(enable_dr: bool, dr_level: str = 'standard', n_steps: int = 1000):
    """環境のパフォーマンスベンチマーク"""
    if enable_dr:
        config = get_config(dr_level)
        env = MinicarEnv(
            course_file="courses/easy/simple_oval.json",
            enable_domain_randomization=True,
            physics_randomization_config=config['physics'],
            sensor_noise_config=config['sensor'],
        )
    else:
        env = MinicarEnv(
            course_file="courses/easy/simple_oval.json",
            enable_domain_randomization=False,
        )

    # リセット時間
    reset_times = []
    for _ in range(10):
        start = time.time()
        env.reset()
        reset_times.append(time.time() - start)

    # ステップ時間
    env.reset()
    step_times = []
    for _ in range(n_steps):
        action = env.action_space.sample()
        start = time.time()
        env.step(action)
        step_times.append(time.time() - start)

    return {
        'reset_time_mean': np.mean(reset_times),
        'reset_time_std': np.std(reset_times),
        'step_time_mean': np.mean(step_times),
        'step_time_std': np.std(step_times),
    }


if __name__ == "__main__":
    print("Benchmarking without Domain Randomization...")
    results_no_dr = benchmark_env(enable_dr=False)

    print("Benchmarking with Domain Randomization (standard)...")
    results_with_dr = benchmark_env(enable_dr=True, dr_level='standard')

    print("\n" + "="*60)
    print("Results:")
    print("="*60)
    print(f"Without DR:")
    print(f"  Reset time: {results_no_dr['reset_time_mean']*1000:.2f} ± {results_no_dr['reset_time_std']*1000:.2f} ms")
    print(f"  Step time:  {results_no_dr['step_time_mean']*1000:.2f} ± {results_no_dr['step_time_std']*1000:.2f} ms")

    print(f"\nWith DR:")
    print(f"  Reset time: {results_with_dr['reset_time_mean']*1000:.2f} ± {results_with_dr['reset_time_std']*1000:.2f} ms")
    print(f"  Step time:  {results_with_dr['step_time_mean']*1000:.2f} ± {results_with_dr['step_time_std']*1000:.2f} ms")

    print(f"\nOverhead:")
    reset_overhead = (results_with_dr['reset_time_mean'] / results_no_dr['reset_time_mean'] - 1) * 100
    step_overhead = (results_with_dr['step_time_mean'] / results_no_dr['step_time_mean'] - 1) * 100
    print(f"  Reset: +{reset_overhead:.1f}%")
    print(f"  Step:  +{step_overhead:.1f}%")
```

**目標**: オーバーヘッド < 10%

---

## 6. テストチェックリスト

### ユニットテスト
- [ ] PhysicsRandomizer初期化テスト
- [ ] PhysicsRandomizerパラメータ範囲テスト
- [ ] PhysicsRandomizer再現性テスト
- [ ] SensorNoiseRandomizer初期化テスト
- [ ] SensorNoiseRandomizerパラメータ範囲テスト
- [ ] SensorNoiseRandomizer再現性テスト

### 統合テスト
- [ ] MinicarEnv with DR無効テスト
- [ ] MinicarEnv with DR有効テスト
- [ ] 複数エピソードでのランダム化テスト
- [ ] すべての設定レベルでの環境作成テスト

### 学習テスト
- [ ] Mild設定での短時間学習テスト
- [ ] Standard設定での短時間学習テスト
- [ ] Strong設定での短時間学習テスト
- [ ] DR有無の比較学習テスト

### パフォーマンステスト
- [ ] リセット時間測定
- [ ] ステップ時間測定
- [ ] オーバーヘッド計算

### 最終検証
- [ ] すべてのユニットテストがパス
- [ ] 統合テストがパス
- [ ] 学習が正常に収束
- [ ] パフォーマンスオーバーヘッド < 10%
- [ ] ドキュメント完備

---

## 7. 継続的な検証

### 7.1 定期的なテスト実行

```bash
# すべてのテストを実行
pytest tests/ -v --cov=src --cov-report=html

# Domain Randomization関連のみ
pytest tests/test_physics_randomizer.py \
       tests/test_sensor_noise.py \
       tests/test_env_domain_randomization.py \
       -v
```

### 7.2 学習曲線のモニタリング

TensorBoardで以下を定期的にチェック:
- 報酬の推移
- エピソード長
- 成功率
- 損失関数

---

**完了**: これですべてのDomain Randomization実装計画ドキュメントが完成しました！
