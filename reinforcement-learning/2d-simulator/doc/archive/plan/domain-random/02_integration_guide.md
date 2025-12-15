# Domain Randomization実装計画 - 統合ガイド

## ステップバイステップの実装手順

このドキュメントでは、Domain Randomizationを既存のコードベースに統合する手順を詳しく説明します。

---

## Phase 1: 基本実装（Day 1-3）

### Day 1: PhysicsRandomizerの実装

#### ステップ 1.1: ファイル作成

```bash
# 実装ファイルを作成
touch src/domain_randomization/physics_randomizer.py
```

#### ステップ 1.2: PhysicsRandomizerの実装

`src/domain_randomization/physics_randomizer.py`に以下を実装:

1. `PhysicsRandomizationConfig`データクラス
2. `PhysicsRandomizer`クラス
3. プリセット設定（`DEFAULT_PHYSICS_CONFIG`, `MILD_PHYSICS_CONFIG`, `STRONG_PHYSICS_CONFIG`）

詳細は[01_implementation_details.md](./01_implementation_details.md)のセクション1を参照。

#### ステップ 1.3: 動作確認

```python
# test_physics_randomizer.py
from src.domain_randomization.physics_randomizer import (
    PhysicsRandomizer,
    PhysicsRandomizationConfig,
)

def test_randomizer():
    config = PhysicsRandomizationConfig()
    randomizer = PhysicsRandomizer(config)

    # 10回ランダム化してパラメータ範囲を確認
    for i in range(10):
        params = randomizer.randomize()
        print(f"Trial {i+1}:")
        print(f"  Friction: {params['friction']:.3f}")
        print(f"  Mass: {params['mass']:.3f} kg")
        print(f"  Motor Force: {params['motor_force']:.3f} N")
        print()

        # 範囲チェック
        assert 0.5 <= params['friction'] <= 1.0
        assert 1.2 <= params['mass'] <= 1.6
        assert 18.0 <= params['motor_force'] <= 22.0

    print("✅ PhysicsRandomizer test passed!")

if __name__ == "__main__":
    test_randomizer()
```

```bash
# 実行
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"
python test_physics_randomizer.py
```

---

### Day 2: SensorNoiseの実装

#### ステップ 2.1: ファイル作成

```bash
touch src/domain_randomization/sensor_noise.py
```

#### ステップ 2.2: SensorNoiseRandomizerの実装

`src/domain_randomization/sensor_noise.py`に以下を実装:

1. `SensorNoiseConfig`データクラス
2. `SensorNoiseRandomizer`クラス
3. プリセット設定

詳細は[01_implementation_details.md](./01_implementation_details.md)のセクション2を参照。

#### ステップ 2.3: 動作確認

```python
# test_sensor_noise.py
import numpy as np
from src.env.sensors import LiDARSensor
from src.physics.box2d_wrapper import PhysicsWorld
from src.domain_randomization.sensor_noise import (
    SensorNoiseRandomizer,
    SensorNoiseConfig,
)

def test_sensor_noise():
    # テスト用の環境を作成
    world = PhysicsWorld()

    # LiDARセンサー
    lidar = LiDARSensor(world.world, num_rays=5, max_range=3.0)

    # ノイズランダマイザー
    config = SensorNoiseConfig()
    randomizer = SensorNoiseRandomizer(config)

    # クリーンなスキャン（仮想的に）
    clean_scan = np.array([1.0, 1.5, 2.0, 2.5, 3.0])

    print("Clean scan:", clean_scan)
    print()

    # 10回ノイズ適用
    for i in range(10):
        noisy_scan = randomizer.apply_noise(lidar, clean_scan.copy())
        print(f"Trial {i+1}: {noisy_scan}")

    print("\n✅ SensorNoiseRandomizer test passed!")

if __name__ == "__main__":
    test_sensor_noise()
```

---

### Day 3: 設定ファイルと__init__.pyの作成

#### ステップ 3.1: config.pyの作成

```bash
touch src/domain_randomization/config.py
```

詳細は[01_implementation_details.md](./01_implementation_details.md)のセクション5を参照。

#### ステップ 3.2: __init__.pyの更新

既存の空ファイルを更新:

詳細は[01_implementation_details.md](./01_implementation_details.md)のセクション6を参照。

#### ステップ 3.3: モジュールインポートの確認

```python
# test_module_import.py
from src.domain_randomization import (
    PhysicsRandomizer,
    SensorNoiseRandomizer,
    get_config,
)

def test_imports():
    # mild設定を取得
    config = get_config('mild')
    print("Mild config:", config)

    # randomizer初期化
    physics_randomizer = PhysicsRandomizer(config['physics'])
    sensor_randomizer = SensorNoiseRandomizer(config['sensor'])

    print("\n✅ Module import test passed!")

if __name__ == "__main__":
    test_imports()
```

---

## Phase 2: 環境統合（Day 4-5）

### Day 4: Vehicleクラスの拡張

#### ステップ 4.1: Vehicleの__init__修正

`src/env/vehicle.py`の`__init__`メソッドを修正:

```python
def __init__(
    self,
    world: b2World,
    start_pos: Tuple[float, float],
    start_angle: float = 0.0,
    # Domain Randomization用の追加パラメータ
    mass: float = 1.4,
    friction: float = 0.7,
    linear_damping: float = 0.5,
    angular_damping: float = 0.8,
    max_motor_force: float = 20.0,
    max_lateral_impulse: float = 2.5,
):
```

**変更箇所**:
- 固定値だったパラメータを引数として受け取る
- デフォルト値は従来の値を使用

詳細は[01_implementation_details.md](./01_implementation_details.md)のセクション3を参照。

#### ステップ 4.2: Vehicleのresetメソッド修正

```python
def reset(
    self,
    position: Tuple[float, float],
    angle: float = 0.0,
    # Domain Randomization用パラメータ
    mass: Optional[float] = None,
    friction: Optional[float] = None,
    linear_damping: Optional[float] = None,
    angular_damping: Optional[float] = None,
    max_motor_force: Optional[float] = None,
    max_lateral_impulse: Optional[float] = None,
):
```

#### ステップ 4.3: Vehicleクラスの動作確認

```python
# test_vehicle_randomization.py
from src.physics.box2d_wrapper import PhysicsWorld
from src.env.vehicle import Vehicle

def test_vehicle_params():
    world = PhysicsWorld()

    # ランダム化されたパラメータで車両を作成
    vehicle = Vehicle(
        world.world,
        start_pos=(0, 0),
        start_angle=0.0,
        mass=1.5,  # 通常より重い
        friction=0.6,  # 通常より低い摩擦
        max_motor_force=22.0,  # 通常より強いモーター
    )

    print(f"Mass: {vehicle.mass}")
    print(f"Max motor force: {vehicle.max_motor_force}")
    print(f"Friction: {vehicle.body.fixtures[0].friction}")

    # リセットでパラメータ変更
    vehicle.reset(
        position=(1, 1),
        angle=0.5,
        mass=1.3,
        friction=0.8,
    )

    print(f"\nAfter reset:")
    print(f"Mass: {vehicle.mass}")
    print(f"Friction: {vehicle.body.fixtures[0].friction}")

    print("\n✅ Vehicle randomization test passed!")

if __name__ == "__main__":
    test_vehicle_params()
```

---

### Day 5: MinicarEnvへの統合

#### ステップ 5.1: MinicarEnvの__init__修正

`src/env/minicar_env.py`の`__init__`メソッドに以下を追加:

```python
from src.domain_randomization.physics_randomizer import (
    PhysicsRandomizer,
    PhysicsRandomizationConfig,
    DEFAULT_PHYSICS_CONFIG,
)
from src.domain_randomization.sensor_noise import (
    SensorNoiseRandomizer,
    SensorNoiseConfig,
    DEFAULT_SENSOR_NOISE_CONFIG,
)


class MinicarEnv(gym.Env):
    def __init__(
        self,
        course_file: str = "courses/easy/simple_oval.json",
        render_mode: Optional[str] = None,
        max_steps: int = 2000,
        deployment_mode: bool = False,
        # Domain Randomization用の追加パラメータ
        enable_domain_randomization: bool = False,
        physics_randomization_config: Optional[PhysicsRandomizationConfig] = None,
        sensor_noise_config: Optional[SensorNoiseConfig] = None,
    ):
        # ... 既存の初期化コード ...

        # Domain Randomization設定
        self.enable_domain_randomization = enable_domain_randomization

        if self.enable_domain_randomization:
            physics_config = physics_randomization_config or DEFAULT_PHYSICS_CONFIG
            self.physics_randomizer = PhysicsRandomizer(physics_config)

            sensor_config = sensor_noise_config or DEFAULT_SENSOR_NOISE_CONFIG
            self.sensor_noise_randomizer = SensorNoiseRandomizer(sensor_config)

            print("[INFO] Domain Randomization enabled")
        else:
            self.physics_randomizer = None
            self.sensor_noise_randomizer = None
```

#### ステップ 5.2: MinicarEnvのresetメソッド修正

```python
def reset(
    self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """環境をリセット"""
    super().reset(seed=seed)

    # Domain Randomization: 物理パラメータをランダム化
    if self.enable_domain_randomization and self.physics_randomizer:
        physics_params = self.physics_randomizer.randomize()
    else:
        # デフォルトパラメータを使用
        physics_params = {}

    # 車両をリセット
    start_pos, start_angle = self.course.get_start_pose()

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
    else:
        self.vehicle.reset(start_pos, start_angle)

    # ... 既存のリセットコード ...
```

#### ステップ 5.3: _get_observationメソッド修正

```python
def _get_observation(self) -> np.ndarray:
    """観測を取得（Domain Randomization対応）"""
    # キャッシュされたLiDARスキャンを使用
    lidar_distances = self._cached_lidar_scan.copy()

    # Domain Randomization: センサーノイズを適用
    if self.enable_domain_randomization and self.sensor_noise_randomizer:
        lidar_distances = self.sensor_noise_randomizer.apply_noise(
            self.lidar,
            lidar_distances
        )

    # LiDARの正規化（5次元）
    lidar_normalized = lidar_distances / LIDAR_MAX_RANGE

    # ... 既存の観測構築コード ...
```

#### ステップ 5.4: 環境の動作確認

```python
# test_env_domain_randomization.py
from src.env.minicar_env import MinicarEnv
from src.domain_randomization import get_config

def test_env_with_dr():
    # Domain Randomization有効で環境作成
    config = get_config('mild')

    env = MinicarEnv(
        course_file="courses/easy/simple_oval.json",
        enable_domain_randomization=True,
        physics_randomization_config=config['physics'],
        sensor_noise_config=config['sensor'],
    )

    # リセット
    obs, info = env.reset()
    print(f"Observation shape: {obs.shape}")
    print(f"Observation: {obs}")

    # 数ステップ実行
    for i in range(5):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"\nStep {i+1}:")
        print(f"  Reward: {reward:.3f}")
        print(f"  LiDAR (first 3): {obs[:3]}")

    print("\n✅ Environment with Domain Randomization test passed!")

if __name__ == "__main__":
    test_env_with_dr()
```

```bash
# 実行
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"
python test_env_domain_randomization.py
```

---

## Phase 3: 学習統合（Day 6-7）

### Day 6: 学習スクリプトの更新

#### ステップ 6.1: train.pyにコマンドライン引数追加

`scripts/rl-training/train.py`の`parse_args()`に以下を追加:

```python
def parse_args():
    parser = argparse.ArgumentParser(description="PPO Training for Minicar")

    # ... 既存の引数 ...

    # Domain Randomization設定
    parser.add_argument(
        "--enable-domain-randomization",
        action="store_true",
        help="Enable Domain Randomization for robust policy learning",
    )
    parser.add_argument(
        "--dr-level",
        type=str,
        default="standard",
        choices=["disabled", "mild", "standard", "strong"],
        help="Domain Randomization level (disabled/mild/standard/strong)",
    )

    return parser.parse_args()
```

#### ステップ 6.2: train.pyの環境作成部分を修正

```python
from src.domain_randomization import get_config

def main():
    args = parse_args()

    # ... 既存の設定 ...

    # Domain Randomization設定を取得
    if args.enable_domain_randomization:
        dr_config = get_config(args.dr_level)
        print(f"[INFO] Domain Randomization enabled: level={args.dr_level}")
    else:
        dr_config = get_config('disabled')

    # 環境作成
    env = MinicarEnv(
        course_file=args.course,
        render_mode="human" if args.gui else None,
        max_steps=args.max_steps,
        enable_domain_randomization=args.enable_domain_randomization,
        physics_randomization_config=dr_config['physics'],
        sensor_noise_config=dr_config['sensor'],
    )

    # ... 既存の学習ループ ...
```

#### ステップ 6.3: 学習テスト

```bash
# 軽微なDomain Randomizationで学習テスト
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

python scripts/rl-training/train.py \
  --course courses/easy/simple_oval.json \
  --total-iterations 10 \
  --enable-domain-randomization \
  --dr-level mild \
  --gui
```

---

### Day 7: カリキュラム学習への統合

#### ステップ 7.1: train_curriculum.pyの更新

`scripts/rl-training/train_curriculum.py`にも同様の引数を追加:

```python
from src.domain_randomization import get_config

def main():
    args = parse_args()

    # Domain Randomization設定
    if args.enable_domain_randomization:
        dr_config = get_config(args.dr_level)
    else:
        dr_config = get_config('disabled')

    # カリキュラムマネージャー
    curriculum = CurriculumManager(
        courses=course_files,
        success_threshold=0.8,
        degradation_threshold=0.3,
        # ... その他の設定 ...
    )

    # 環境作成（カリキュラムの最初のコースで）
    env = MinicarEnv(
        course_file=curriculum.get_current_course(),
        render_mode="human" if args.gui else None,
        max_steps=args.max_steps,
        enable_domain_randomization=args.enable_domain_randomization,
        physics_randomization_config=dr_config['physics'],
        sensor_noise_config=dr_config['sensor'],
    )

    # ... 学習ループ内でコース変更時に環境を再作成 ...
```

#### ステップ 7.2: カリキュラム学習テスト

```bash
# カリキュラム学習 + Domain Randomization
python scripts/rl-training/train_curriculum.py \
  --total-iterations 50 \
  --enable-domain-randomization \
  --dr-level standard
```

---

## Phase 4: ドキュメント整備（Day 7）

### ステップ 8.1: README.mdの更新

プロジェクトルートの`README.md`または`CLAUDE.md`に以下を追加:

```markdown
## Domain Randomization

### 概要

Domain Randomizationを使用して、実機転移性能を向上させます。

### 使い方

基本的な学習:
```bash
python scripts/rl-training/train.py \
  --enable-domain-randomization \
  --dr-level standard
```

レベル選択:
- `disabled`: Domain Randomizationなし
- `mild`: 軽微なランダム化（最初のテスト用）
- `standard`: 標準的なランダム化（通常の学習用）
- `strong`: 強めのランダム化（実機転移用）

### 詳細

詳細な実装計画は `doc/plan/domain-random/` を参照してください。
```

---

## チェックリスト

### Phase 1: 基本実装
- [ ] PhysicsRandomizer実装完了
- [ ] SensorNoiseRandomizer実装完了
- [ ] config.py作成完了
- [ ] __init__.py更新完了
- [ ] モジュール単体テストパス

### Phase 2: 環境統合
- [ ] Vehicleクラス拡張完了
- [ ] MinicarEnv.__init__修正完了
- [ ] MinicarEnv.reset修正完了
- [ ] MinicarEnv._get_observation修正完了
- [ ] 環境の統合テストパス

### Phase 3: 学習統合
- [ ] train.py更新完了
- [ ] train_curriculum.py更新完了
- [ ] コマンドライン引数動作確認
- [ ] Domain Randomizationありで学習成功

### Phase 4: ドキュメント
- [ ] README.md更新
- [ ] CLAUDE.md更新（必要に応じて）
- [ ] 実装計画ドキュメント完成

---

## トラブルシューティング

### 問題: 学習が収束しない

**原因**: Domain Randomizationの範囲が広すぎる

**解決策**:
1. `mild`レベルから開始
2. 段階的に`standard`、`strong`へ移行
3. パラメータ範囲をカスタマイズ

### 問題: インポートエラー

**原因**: PYTHONPATHが設定されていない

**解決策**:
```bash
export PYTHONPATH="$(pwd):$PYTHONPATH"
```

### 問題: パラメータが反映されない

**原因**: Vehicleのresetメソッドでパラメータが更新されていない

**解決策**:
- `vehicle.reset()`呼び出し時に全パラメータを渡す
- デバッグプリントでパラメータ値を確認

---

**次**: [03_testing_strategy.md](./03_testing_strategy.md)でテスト戦略を確認してください。
