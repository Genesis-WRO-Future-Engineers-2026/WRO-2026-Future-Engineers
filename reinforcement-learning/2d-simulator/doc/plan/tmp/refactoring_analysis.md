# コードベースリファクタリング分析レポート

**作成日**: 2025-12-13
**対象**: 2D Simulator - PPO強化学習プロジェクト

## 概要

このレポートは、プロジェクト全体の技術的負債、肥大化したファイル、可読性の問題、およびアーキテクチャ上の改善点を特定し、具体的な修正提案をまとめたものです。

---

## 1. 肥大化しているファイル

### 1.1 主要な問題ファイル（行数順）

| ファイル | 行数 | 問題の深刻度 | 主な問題 |
|---------|------|------------|---------|
| `src/env/minicar_env.py` | 554 | ⚠️ 高 | 責務の肥大化、過度な機能統合 |
| `scripts/course-generation/svg_with_width_to_course.py` | 514 | ⚠️ 高 | 長大な処理スクリプト |
| `scripts/course-generation/centerline_to_walls.py` | 434 | ⚠️ 中 | 複雑なジオメトリ処理 |
| `src/env/vehicle.py` | 380 | ⚠️ 中 | 物理計算の密結合 |
| `src/rl/trainer.py` | 365 | ⚠️ 中 | 学習ループの複雑化 |
| `src/rl/ppo.py` | 332 | ⚠️ 中 | アルゴリズム実装の肥大化 |
| `src/rl/buffer.py` | 304 | ⚠️ 低 | 2つのバッファクラスの重複 |
| `src/env/renderer.py` | 292 | ⚠️ 低 | 描画ロジックの集中 |
| `src/curriculum/curriculum_manager.py` | 287 | ⚠️ 低 | 良好だが改善の余地あり |

---

## 2. 各ファイルの詳細分析と改善提案

### 2.1 `src/env/minicar_env.py` (554行) - 最優先改善対象

#### 問題点

1. **単一責任原則の違反**
   - 環境管理、報酬計算、終了判定、レンダリング、Domain Randomizationなど、複数の責務が混在

2. **報酬関数の肥大化**
   - `_compute_reward()` メソッドが80行近く（L297-378）
   - 適応的報酬スケーリング、チェックポイント管理、ゴール判定が混在
   - 報酬設計の変更が困難

3. **Domain Randomizationの不適切な統合**
   - 初期化時の条件分岐が複雑（L73-93）
   - センサーノイズとLiDAR取得が密結合（L273-277）

4. **キャッシング機構の過度な使用**
   - `_cached_lidar_scan`と`_cached_vehicle_state`が複数メソッドで共有
   - デバッグ時の理解が困難

5. **観測空間の説明とコードの不一致**
   - コメントでは「10次元」と記載されているが、実装が散在している

#### 改善提案

```python
# 推奨構造:
src/env/
├── minicar_env.py          # 軽量化: 環境のコア管理のみ
├── observation.py          # 観測空間の構築（NEW）
├── reward_functions.py     # 報酬関数の分離（NEW）
│   ├── BaseRewardFunction
│   ├── CheckpointRewardFunction
│   ├── TimeBasedRewardFunction
│   └── CompositeRewardFunction
├── termination.py          # 終了条件の分離（NEW）
└── domain_randomization/   # 既存のモジュール化
```

**具体的な修正アクション**:

1. **報酬関数の抽出**
   ```python
   # reward_functions.py
   class RewardFunction:
       def compute(self, state, action, env_info) -> float:
           pass

   class CompositeRewardFunction(RewardFunction):
       def __init__(self, functions: List[RewardFunction]):
           self.functions = functions

       def compute(self, state, action, env_info) -> float:
           return sum(f.compute(state, action, env_info) for f in self.functions)
   ```

2. **観測空間の抽出**
   ```python
   # observation.py
   class ObservationBuilder:
       def __init__(self, lidar_sensor, normalize=True):
           self.lidar = lidar_sensor
           self.normalize = normalize

       def build(self, vehicle_state, lidar_scan, last_action) -> np.ndarray:
           # 観測の構築ロジック
           pass
   ```

3. **MinicarEnvの簡素化**
   ```python
   class MinicarEnv(gym.Env):
       def __init__(self, ...):
           self.reward_fn = CompositeRewardFunction([...])
           self.obs_builder = ObservationBuilder(...)
           self.termination_checker = TerminationChecker(...)

       def step(self, action):
           # シンプルなステップ処理
           obs = self.obs_builder.build(...)
           reward = self.reward_fn.compute(...)
           terminated = self.termination_checker.check(...)
   ```

**期待される効果**:
- ファイルサイズ: 554行 → 250行程度
- 報酬関数の変更が容易（実験しやすい）
- テストの記述が容易
- Domain Randomizationの影響範囲が明確化

---

### 2.2 `src/env/vehicle.py` (380行)

#### 問題点

1. **定数の過度な詳細コメント**
   - L12-43で定数定義に30行のコメント
   - 可読性向上の意図は良いが、冗長

2. **メソッドの責務分離が不十分**
   - `apply_control()`が制御入力の正規化、ホイール位置計算、タイヤ摩擦、駆動力適用、角速度減衰をすべて実行

3. **Domain Randomization対応による複雑化**
   - `reset()`メソッドが多数のOptionalパラメータを持つ（L325-336）

#### 改善提案

1. **定数をConfigクラスに移動**
   ```python
   # vehicle_config.py
   @dataclass
   class VehicleConfig:
       """車両パラメータの設定"""
       steering_threshold_straight: float = 0.001
       steering_threshold_damping: float = 0.05
       angular_damping_strong: float = 0.8
       angular_damping_normal: float = 0.1
       # ... その他のパラメータ
   ```

2. **制御システムの分離**
   ```python
   # vehicle_control.py
   class BicycleModelController:
       """Bicycle Modelベースの制御システム"""
       def apply_control(self, vehicle, steering, throttle):
           # 制御ロジック
           pass
   ```

3. **Domain Randomization用ファクトリパターン**
   ```python
   # vehicle_factory.py
   class VehicleFactory:
       @staticmethod
       def create(world, start_pos, start_angle, config=None):
           # 車両生成ロジック
           pass
   ```

**期待される効果**:
- ファイルサイズ: 380行 → 200行程度
- 物理計算ロジックの理解が容易
- テストの記述が容易

---

### 2.3 `src/rl/trainer.py` (365行)

#### 問題点

1. **GUIイベント処理の重複**
   - `collect_rollouts()`と`evaluate()`で同一のGUIイベント処理コードが重複（L104-115, L314-323）

2. **統計情報の散在**
   - エピソード報酬、長さ、成功率などが複数箇所で計算

3. **カリキュラム学習との密結合**
   - カリキュラム学習のロジックがTrainerに直接埋め込まれている（L149-158, L226-247）

4. **評価ロジックの肥大化**
   - `evaluate()`メソッドが70行近く（L295-355）

#### 改善提案

1. **GUIマネージャーの分離**
   ```python
   # gui_manager.py
   class GUIManager:
       def __init__(self, enabled=False):
           self.enabled = enabled
           self.visible = enabled

       def handle_events(self):
           """Pygameイベントを処理し、表示状態を返す"""
           if not self.enabled:
               return self.visible

           for event in pygame.event.get():
               if event.type == pygame.KEYDOWN and event.key == pygame.K_g:
                   self.visible = not self.visible
               elif event.type == pygame.QUIT:
                   self.visible = False
           return self.visible
   ```

2. **統計収集の抽出**
   ```python
   # training_stats.py
   class TrainingStatistics:
       def __init__(self):
           self.episode_rewards = []
           self.episode_lengths = []
           # ...

       def record_episode(self, reward, length, success):
           # 記録
           pass

       def get_summary(self) -> Dict:
           # 統計サマリーを返す
           pass
   ```

3. **Evaluatorの分離**
   ```python
   # evaluator.py
   class PPOEvaluator:
       def __init__(self, env, n_episodes=5):
           self.env = env
           self.n_episodes = n_episodes

       def evaluate(self, ppo_agent) -> Dict[str, float]:
           # 評価ロジック
           pass
   ```

**期待される効果**:
- ファイルサイズ: 365行 → 200行程度
- 学習ループの可読性向上
- 評価ロジックの再利用性向上

---

### 2.4 `src/rl/ppo.py` (332行)

#### 問題点

1. **共有ネットワークと独立ネットワークの条件分岐**
   - `__init__`, `get_action`, `update`, `save`, `load`の全メソッドで条件分岐
   - コードの重複が多い

2. **updateメソッドの肥大化**
   - 145行にわたる複雑なロジック（L146-288）
   - ミニバッチ処理、損失計算、勾配更新が混在

3. **SquashとUnsquashの不自然な実装**
   - L195-201で行動の逆変換を手動で実装
   - PolicyクラスとPPOクラスの責務が不明確

#### 改善提案

1. **Strategy Patternの適用**
   ```python
   # ppo_strategy.py
   class PPOStrategy(ABC):
       @abstractmethod
       def get_action(self, obs, deterministic=False):
           pass

       @abstractmethod
       def update(self, rollout_buffer, n_epochs, batch_size):
           pass

   class SharedNetworkPPO(PPOStrategy):
       # 共有ネットワーク用の実装
       pass

   class SeparateNetworkPPO(PPOStrategy):
       # 独立ネットワーク用の実装
       pass
   ```

2. **Updateロジックの分割**
   ```python
   # ppo_updater.py
   class PPOUpdater:
       def __init__(self, config):
           self.config = config

       def compute_policy_loss(self, ...):
           # ポリシー損失計算
           pass

       def compute_value_loss(self, ...):
           # 価値損失計算
           pass

       def perform_update_step(self, ...):
           # 勾配更新
           pass
   ```

**期待される効果**:
- ファイルサイズ: 332行 → 150行程度（PPO本体）
- アルゴリズムの変更が容易
- テストの記述が容易

---

### 2.5 `scripts/course-generation/` の巨大スクリプト群

#### 問題点

1. **svg_with_width_to_course.py (514行)**
   - SVGパース、幾何計算、JSON出力が単一ファイル

2. **centerline_to_walls.py (434行)**
   - 複雑なジオメトリ処理が1ファイルに集約

3. **重複コードの存在**
   - SVG処理スクリプト間で類似コードが散見される

#### 改善提案

1. **共通ライブラリの作成**
   ```python
   scripts/course-generation/
   ├── lib/
   │   ├── svg_parser.py          # SVGパース処理
   │   ├── geometry_utils.py      # ジオメトリ計算
   │   ├── course_builder.py      # コース生成
   │   └── json_exporter.py       # JSON出力
   ├── svg_with_width_to_course.py  # 簡素化
   ├── centerline_to_walls.py       # 簡素化
   └── svg_direct_to_course.py      # 簡素化
   ```

2. **処理のパイプライン化**
   ```python
   # course_pipeline.py
   class CourseGenerationPipeline:
       def __init__(self):
           self.parsers = []
           self.processors = []
           self.exporters = []

       def add_parser(self, parser):
           self.parsers.append(parser)

       def execute(self, input_file, output_file):
           # パイプライン実行
           pass
   ```

**期待される効果**:
- 各スクリプト: 500行 → 150行程度
- コードの再利用性向上
- メンテナンス性向上

---

### 2.6 `src/rl/buffer.py` (304行)

#### 問題点

1. **2つのバッファクラスの共存**
   - `RolloutBuffer` (GAE付き)
   - `SimpleBuffer` (GAE無し)
   - `SimpleBuffer`は未使用の可能性が高い

2. **責務の混在**
   - データ保存とGAE計算が同一クラス

#### 改善提案

1. **未使用クラスの削除**
   - `SimpleBuffer`が使用されていない場合は削除

2. **GAE計算の分離**
   ```python
   # gae_calculator.py
   class GAECalculator:
       def __init__(self, gamma, gae_lambda):
           self.gamma = gamma
           self.gae_lambda = gae_lambda

       def compute(self, rewards, values, dones, last_value):
           # GAE計算
           pass
   ```

**期待される効果**:
- ファイルサイズ: 304行 → 150行程度
- GAEアルゴリズムの理解が容易

---

## 3. 可読性の問題

### 3.1 過度なコメント

**問題箇所**:
- `src/env/vehicle.py` L12-43: 30行にわたる定数の説明コメント
- `src/env/minicar_env.py` L34-38: 衝突判定パラメータの長大なコメント

**改善提案**:
- Docstring形式に統一
- 詳細な説明は別途ドキュメント化（README.md）
- コード自体を自己説明的にする（命名の改善）

### 3.2 マジックナンバー

**問題箇所**:
- `src/env/minicar_env.py` L343: `max_distance = 20.0` (ハードコード)
- `src/env/renderer.py` L277: `y_offset += 25` (ハードコード)

**改善提案**:
- 定数化または設定ファイルに移動
- 計算ロジックを明示

### 3.3 長いメソッド

**問題箇所**:
- `MinicarEnv._compute_reward()`: 80行
- `PPO.update()`: 145行
- `Vehicle.apply_control()`: 30行（複数のサブシステム呼び出し）

**改善提案**:
- メソッドの分割（1メソッド = 1責務）
- Extract Methodリファクタリング

---

## 4. アーキテクチャ上の問題

### 4.1 循環依存の懸念

**現状**:
```python
# src/env/renderer.py
if TYPE_CHECKING:
    from src.env.vehicle import Vehicle
```

- 循環依存を避けるためのTYPE_CHECKINGの使用
- 設計上の密結合を示唆

**改善提案**:
- インターフェース（Protocol）の導入
- 依存性の逆転（Dependency Inversion）

```python
# vehicle_protocol.py
from typing import Protocol

class VehicleProtocol(Protocol):
    def get_state(self) -> Dict:
        ...

    @property
    def length(self) -> float:
        ...

    @property
    def width(self) -> float:
        ...

# renderer.py
class Renderer:
    def draw_vehicle(self, vehicle: VehicleProtocol):
        # VehicleProtocolに依存
        pass
```

### 4.2 設定管理の不在

**問題点**:
- ハイパーパラメータがコード中に散在
- 実験時の再現性が低い

**改善提案**:

1. **設定ファイルの導入**
   ```python
   # config/
   ├── env_config.yaml
   ├── ppo_config.yaml
   ├── training_config.yaml
   └── domain_randomization_config.yaml
   ```

2. **Hydra等の設定管理ライブラリの活用**
   ```python
   import hydra
   from omegaconf import DictConfig

   @hydra.main(config_path="config", config_name="training_config")
   def train(cfg: DictConfig):
       env = MinicarEnv(**cfg.env)
       ppo = PPO(**cfg.ppo)
       trainer = PPOTrainer(env, ppo, **cfg.trainer)
       trainer.train(cfg.total_iterations)
   ```

### 4.3 テストコードの不足

**問題点**:
- `tests/`ディレクトリには3つのテストファイルのみ
- 報酬関数、観測空間、PPOアルゴリズムの単体テストが不在

**改善提案**:
- リファクタリング後に単体テストを追加
- CI/CDパイプラインの整備

---

## 5. スクリプトディレクトリの整理

### 5.1 現状の問題

```
scripts/
├── analysis/               # 3ファイル
├── course-generation/      # 8ファイル（巨大）
├── deploy/                 # 2ファイル
├── rl-training/            # 5ファイル
└── simulator-demo/         # デバッグスクリプト6個
```

**問題点**:
1. `simulator-demo/debug/`に古いデバッグスクリプトが残存
2. `course-generation/`のスクリプトが重複・肥大化
3. 命名規則が不統一（snake_case, キャメルケース混在）

### 5.2 改善提案

1. **デバッグスクリプトのアーカイブ化**
   ```bash
   scripts/
   ├── archive/debug/  # 使用頻度の低いデバッグスクリプト
   ```

2. **スクリプトの統合**
   - SVG変換スクリプトを統合CLI化
   ```bash
   python scripts/course-generation/convert_svg.py \
       --mode with_width \
       --input input.svg \
       --output output.json
   ```

---

## 6. 改善の優先順位

### Phase 1: 最優先 (1-2週間)

1. ✅ **`src/env/minicar_env.py`のリファクタリング**
   - 報酬関数の抽出
   - 観測空間の抽出
   - 期待効果: 最も影響の大きいファイルの簡素化

2. ✅ **設定管理の導入**
   - YAMLベースの設定ファイル
   - 期待効果: 実験の再現性向上

### Phase 2: 高優先 (2-3週間)

3. ✅ **`src/rl/trainer.py`のリファクタリング**
   - GUIマネージャーの分離
   - Evaluatorの分離

4. ✅ **`src/rl/ppo.py`のリファクタリング**
   - Strategy Patternの適用
   - Updateロジックの分割

### Phase 3: 中優先 (1-2週間)

5. ✅ **`scripts/course-generation/`の整理**
   - 共通ライブラリの作成
   - スクリプトの簡素化

6. ✅ **`src/env/vehicle.py`のリファクタリング**
   - Configクラスの導入
   - 制御システムの分離

### Phase 4: 低優先 (継続的)

7. ✅ **テストコードの追加**
   - 単体テストの整備
   - カバレッジ目標: 70%以上

8. ✅ **ドキュメントの整備**
   - アーキテクチャ図の更新
   - API仕様書の作成

---

## 7. リファクタリング時の注意事項

### 7.1 後方互換性の維持

- 既存のチェックポイント（.pthファイル）との互換性を保つ
- 既存のコース定義ファイル（JSONファイル）との互換性を保つ

### 7.2 段階的な移行

- すべてを一度に変更しない
- 機能ごとに分割してリファクタリング
- 各段階でテストを実行

### 7.3 パフォーマンスの検証

- リファクタリング前後でベンチマーク測定
- 学習速度（FPS）の低下がないことを確認

---

## 8. 期待される効果のまとめ

### 8.1 定量的効果

| 指標 | リファクタリング前 | リファクタリング後 |
|-----|----------------|----------------|
| `minicar_env.py`の行数 | 554行 | ~250行 (-55%) |
| `trainer.py`の行数 | 365行 | ~200行 (-45%) |
| `ppo.py`の行数 | 332行 | ~150行 (-55%) |
| `vehicle.py`の行数 | 380行 | ~200行 (-47%) |
| コードの総行数 | ~5,000行 | ~3,500行 (-30%) |
| テストカバレッジ | 未測定 | 70%以上 |

### 8.2 定性的効果

1. **保守性の向上**
   - 新しい報酬関数の追加が容易
   - 新しいアルゴリズムの実装が容易

2. **可読性の向上**
   - 各ファイルの責務が明確
   - 新規メンバーのオンボーディングが容易

3. **テスト容易性の向上**
   - 単体テストの記述が容易
   - バグの早期発見

4. **実験効率の向上**
   - 設定ファイルによる実験管理
   - ハイパーパラメータ探索の効率化

---

## 9. 次のアクションアイテム

### 即座に実施可能

- [ ] `SimpleBuffer`の使用箇所調査（未使用なら削除）
- [ ] デバッグスクリプトのアーカイブ化
- [ ] マジックナンバーの定数化

### 設計が必要

- [ ] 報酬関数のインターフェース設計
- [ ] 設定ファイルのスキーマ設計
- [ ] Strategy Patternの詳細設計

### 長期的施策

- [ ] CI/CDパイプラインの構築
- [ ] ドキュメント自動生成の導入
- [ ] パフォーマンスプロファイリングの自動化

---

## 10. 結論

このプロジェクトは、機能的には十分に動作しているものの、以下の技術的負債が蓄積しています:

1. **単一責任原則の違反** - 特に`minicar_env.py`
2. **コードの重複** - GUI処理、SVG変換スクリプト
3. **設定管理の不在** - ハードコードされたパラメータ
4. **テストコードの不足** - 単体テストの欠如

これらの問題は、**段階的なリファクタリング**によって解決可能です。特に、Phase 1の`minicar_env.py`のリファクタリングと設定管理の導入は、プロジェクト全体の保守性を大幅に向上させます。

リファクタリングを進める際は、**後方互換性の維持**と**パフォーマンスの検証**を常に意識し、小さな変更を積み重ねていくことが重要です。
