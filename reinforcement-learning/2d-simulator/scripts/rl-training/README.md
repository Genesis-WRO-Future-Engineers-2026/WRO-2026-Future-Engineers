# 強化学習デモ - 学習・テスト・評価

PPO（Proximal Policy Optimization）を使った強化学習のデモスクリプト集です。

---

## 🚀 クイックスタート

### 5分で試す

```bash
# 1. テストを実行（動作確認）
./scripts/rl-training/run_tests.sh

# 2. 短時間学習を実行（約1-2分）
./scripts/rl-training/run_train.sh --total-iterations 5 --n-steps 256

# 3. 学習結果を確認
./scripts/rl-training/run_eval.sh
```

---

## 📂 ファイル構成

```
rl-training/
├── README.md                    # このファイル
│
├── 🤖 学習スクリプト
│   ├── train.py                 # PPO学習スクリプト
│   └── run_train.sh             # 学習起動（実行可能）
│
├── 🧪 テストスクリプト
│   ├── test_rl.py               # RLモジュールのテスト
│   └── run_tests.sh             # テスト起動（実行可能）
│
└── 📊 評価スクリプト
    ├── test_saved_model.py      # 保存モデルの評価
    └── run_eval.sh              # 評価起動（実行可能）
```

---

## 🤖 学習（train.py）

PPOアルゴリズムでエージェントを学習させます。

### 基本的な使い方

```bash
# デフォルト設定で学習開始
./scripts/rl-training/run_train.sh

# カスタム設定で学習
./scripts/rl-training/run_train.sh \
  --total-iterations 1000 \
  --n-steps 2048 \
  --lr 3e-4 \
  --experiment-name my_experiment
```

### 主要なオプション

| オプション | 説明 | デフォルト |
|-----------|------|----------|
| `--course` | コースファイル | `courses/easy/simple_oval.json` |
| `--total-iterations` | 総イテレーション数 | 1000 |
| `--n-steps` | 1イテレーションのステップ数 | 2048 |
| `--n-epochs` | 1更新のエポック数 | 10 |
| `--batch-size` | バッチサイズ | 64 |
| `--lr` | 学習率 | 3e-4 |
| `--gamma` | 割引率 | 0.99 |
| `--save-freq` | 保存頻度（イテレーション） | 50 |
| `--eval-freq` | 評価頻度（イテレーション） | 50 |
| `--device` | デバイス（cpu/cuda/mps/auto） | auto |
| `--experiment-name` | 実験名 | 自動生成 |
| `--gui` | GUIで可視化しながら学習 | なし（指定で有効化） |

### 使用例

```bash
# 短時間のテスト実行（約5分）
./scripts/rl-training/run_train.sh \
  --total-iterations 10 \
  --n-steps 512 \
  --experiment-name quick_test

# GUIで可視化しながら学習（動作確認用）
./scripts/rl-training/run_train.sh \
  --total-iterations 5 \
  --n-steps 256 \
  --gui

# 本格的な学習（約2-3時間）
./scripts/rl-training/run_train.sh \
  --total-iterations 1000 \
  --save-freq 100 \
  --experiment-name full_training

# チェックポイントから再開
./scripts/rl-training/run_train.sh \
  --resume models/checkpoints/checkpoint_500.pth \
  --total-iterations 2000
```

### 学習ログの見方

学習中に表示されるログの読み方を説明します。

**ログ例:**
```
Iteration 40/200
  Timesteps: 81920
  Episode Reward (mean): 1641.45
  Episode Length (mean): 448.0
  Policy Loss: -0.0162
  Value Loss: 6.0220
  FPS: 282
  Elapsed Time: 274.5s
```

**各項目の意味:**

| 項目 | 説明 | 良い値の目安 |
|------|------|-------------|
| **Iteration** | 現在のイテレーション数 / 総イテレーション数 | - |
| **Timesteps** | 学習開始からの累積ステップ数（= Iteration × n_steps） | - |
| **Episode Reward (mean)** | このイテレーション中に完了したエピソードの平均報酬<br>- **マイナス**: ゴールに到達できていない、衝突が多い<br>- **小さい正の値（0-500）**: 長時間走行したがゴールできなかった<br>- **大きい正の値（1000以上）**: ゴール到達成功！ | **1000以上**でゴール成功の可能性が高い |
| **Episode Length (mean)** | エピソード終了までの平均ステップ数<br>- **非常に短い（<100）**: 早期に衝突している<br>- **中程度（300-600）**: ゴール到達の可能性あり<br>- **2001（max_steps）**: タイムアウト（ゴール失敗） | **300-800**がゴール成功の目安 |
| **Policy Loss** | 行動選択ネットワークの損失（PPOのクリッピング損失）<br>- 負の値は正常（PPOの目的関数は最大化）<br>- **0に近い**: 学習が停滞している可能性 | **-0.01 ~ -0.02**程度が健全 |
| **Value Loss** | 状態価値予測の誤差<br>- 小さいほど良い<br>- **10以上**: 価値予測が不安定 | **1.0-5.0**程度 |
| **FPS** | 1秒あたりのシミュレーションステップ数<br>- GUIなし: 200-300<br>- GUIあり: 30-60 | - |
| **Elapsed Time** | 学習開始からの経過時間（秒） | - |

**報酬とエピソード長の関係:**
- 高報酬（1500+） × 短いエピソード（300-600）= **ゴール成功**
- 低報酬（<500） × 長いエピソード（2001）= **タイムアウト（ゴール失敗）**
- 負の報酬 × 短いエピソード（<200）= **早期衝突**

**学習の健全性チェック:**
- ✅ Episode Rewardが徐々に増加している → 順調
- ✅ Episode Lengthがばらついている → 探索が機能している
- ❌ Policy Lossが0.0に張り付いている → 学習停滞
- ❌ Value Lossが10以上で変動が激しい → 学習が不安定

### 学習の進捗確認

**GUIでリアルタイム可視化:**
```bash
# 学習中のエージェントの動作を可視化
./scripts/rl-training/run_train.sh --gui --total-iterations 10

# 注意: GUIモードは学習速度が低下するため、動作確認用途での使用を推奨
```

**TensorBoardで可視化:**
```bash
# 別ターミナルで実行
tensorboard --logdir=logs

# ブラウザで http://localhost:6006 を開く
```

**CSVログの確認:**
```bash
cat logs/<experiment_name>/training.csv | column -t -s,
```

---

## 🧪 テスト（test_rl.py）

強化学習モジュールの動作確認を行います。

```bash
./scripts/rl-training/run_tests.sh
```

**テスト内容:**
- ✓ ポリシーネットワークのテスト
- ✓ 価値関数ネットワークのテスト
- ✓ ロールアウトバッファのテスト
- ✓ PPOアルゴリズムのテスト
- ✓ 環境との統合テスト

**実行時間:** 約10-20秒

**用途:**
- 新規実装の動作確認
- 環境セットアップ後の検証
- バグ修正後のサニティチェック

---

## 📊 評価（test_saved_model.py）

学習済みモデルを読み込んで評価します。

### 基本的な使い方

```bash
# デフォルト（final_model.pth）を3エピソード評価
./scripts/rl-training/run_eval.sh

# GUIで可視化しながら評価
./scripts/rl-training/run_eval.sh --gui

# 特定のチェックポイントをGUIで評価
./scripts/rl-training/run_eval.sh \
  --model models/checkpoints/checkpoint_500.pth \
  --n-episodes 5 \
  --gui

# ベストモデルを評価
./scripts/rl-training/run_eval.sh \
  --model models/best/policy.pth \
  --n-episodes 10
```

### オプション

| オプション | 説明 | デフォルト |
|-----------|------|----------|
| `--model` | モデルファイルのパス | `models/checkpoints/final_model.pth` |
| `--n-episodes` | 評価エピソード数 | 3 |
| `--gui`, `--render` | GUIで可視化しながら評価 | なし（指定で有効化） |

### 出力例

```
Episode 1:
  Reward: 245.32
  Length: 856
  Checkpoints: 4
  Final position: (2.15, 5.03)
  Final speed: 1.25 m/s

Summary:
Average Reward: 238.45 ± 12.34
Average Length: 872.3 ± 45.6
Average Checkpoints: 3.7 ± 0.5
```

---

## 📊 学習ワークフロー例

### 1. 初めての学習

```bash
# Step 1: テスト実行（動作確認）
./scripts/rl-training/run_tests.sh

# Step 2: 短時間学習（動作確認）
./scripts/rl-training/run_train.sh \
  --total-iterations 5 \
  --n-steps 256 \
  --experiment-name initial_test

# Step 3: 結果を確認
./scripts/rl-training/run_eval.sh

# Step 4: TensorBoardで可視化
tensorboard --logdir=logs

# Step 5: 問題なければ本格的な学習を開始
./scripts/rl-training/run_train.sh \
  --total-iterations 1000 \
  --experiment-name main_training
```

### 2. 学習の継続

```bash
# チェックポイントから再開
./scripts/rl-training/run_train.sh \
  --resume models/checkpoints/checkpoint_500.pth \
  --total-iterations 1500 \
  --experiment-name continued_training
```

### 3. ハイパーパラメータ調整

```bash
# 学習率を変更
./scripts/rl-training/run_train.sh \
  --lr 1e-4 \
  --experiment-name lr_1e4

# クリッピング範囲を変更
./scripts/rl-training/run_train.sh \
  --clip-range 0.1 \
  --experiment-name clip_01
```

---

## 🔍 トラブルシューティング

### 学習が進まない場合

1. **報酬関数を確認:**
   ```bash
   ./scripts/simulator-demo/run_manual_control.sh
   ```

2. **学習率を調整:**
   ```bash
   ./scripts/rl-training/run_train.sh --lr 1e-4
   ```

3. **ステップ数を増やす:**
   ```bash
   ./scripts/rl-training/run_train.sh --n-steps 4096
   ```

### メモリ不足の場合

```bash
# バッチサイズを減らす
./scripts/rl-training/run_train.sh --batch-size 32

# ステップ数を減らす
./scripts/rl-training/run_train.sh --n-steps 1024
```

### GPU/MPSが使えない場合

```bash
# CPUを強制
./scripts/rl-training/run_train.sh --device cpu
```

---

## ⚡ よく使うコマンド

```bash
# テスト
./scripts/rl-training/run_tests.sh

# 短時間学習（5イテレーション、約1分）
./scripts/rl-training/run_train.sh --total-iterations 5 --n-steps 256

# GUIで可視化しながら学習
./scripts/rl-training/run_train.sh --total-iterations 5 --n-steps 256 --gui

# 中程度学習（100イテレーション、約30分）
./scripts/rl-training/run_train.sh --total-iterations 100

# 本格学習（1000イテレーション、約2-3時間）
./scripts/rl-training/run_train.sh --total-iterations 1000

# モデル評価
./scripts/rl-training/run_eval.sh

# GUIで可視化しながら評価
./scripts/rl-training/run_eval.sh --gui

# TensorBoard
tensorboard --logdir=logs
```

---

## 📁 出力ファイル

### 学習中に生成されるファイル

```
models/checkpoints/
├── checkpoint_50.pth         # 50イテレーション時点
├── checkpoint_100.pth        # 100イテレーション時点
└── final_model.pth           # 最終モデル

logs/<experiment_name>/
├── hyperparameters.json      # ハイパーパラメータ
├── training.csv              # 学習ログ（CSV形式）
└── events.out.tfevents.*     # TensorBoardログ
```

---

## 📚 関連ドキュメント

- [プロジェクトREADME](../../README.md)
- [手動制御デモ](../simulator-demo/README.md)
- [スクリプト全体のREADME](../README.md)
- [クイックスタート](../QUICKSTART.md)
- [設定ファイル](../../configs/ppo_default.yaml)

---

**作成日**: 2025-12-10
**場所**: `scripts/rl-training/`
