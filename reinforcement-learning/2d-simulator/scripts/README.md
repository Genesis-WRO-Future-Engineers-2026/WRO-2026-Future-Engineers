# Scripts - 実行スクリプト集

このディレクトリには、2Dシミュレーターを操作・学習・評価するためのスクリプトが含まれています。

---

## 📂 ディレクトリ構成

```
scripts/
├── README.md                    # このファイル
├── QUICKSTART.md                # クイックスタートガイド
│
├── 🎮 simulator-demo/           # シミュレーターデモ
│   ├── README.md
│   ├── manual_control.py        # 手動制御デモ
│   └── run_manual_control.sh    # 起動スクリプト
│
└── 🤖 rl-training/                  # 強化学習デモ
    ├── README.md
    ├── train.py                 # PPO学習スクリプト
    ├── run_train.sh             # 学習起動スクリプト
    ├── test_rl.py               # RLモジュールのテスト
    ├── run_tests.sh             # テスト起動スクリプト
    ├── test_saved_model.py      # モデル評価スクリプト
    └── run_eval.sh              # 評価起動スクリプト
```

---

## 🚀 クイックスタート

### 30秒で始める

```bash
# シミュレーターを手動操作
./scripts/simulator-demo/run_manual_control.sh
```

### 5分で学習を試す

```bash
# 1. テスト実行（動作確認）
./scripts/rl-training/run_tests.sh

# 2. 短時間学習（約1-2分）
./scripts/rl-training/run_train.sh --total-iterations 5 --n-steps 256

# 3. 結果を確認
./scripts/rl-training/run_eval.sh
```

詳細は [QUICKSTART.md](./QUICKSTART.md) を参照してください。

---

## 🎮 シミュレーターデモ（simulator-demo/）

### 手動制御デモ

シミュレーターをキーボードで手動操作できます。

```bash
./scripts/simulator-demo/run_manual_control.sh
```

**操作方法:**
- `↑` / `W`: アクセル
- `↓` / `S`: ブレーキ
- `←` / `A`: 左旋回
- `→` / `D`: 右旋回
- `R`: リセット
- `ESC` / `Q`: 終了

詳細は [simulator-demo/README.md](./simulator-demo/README.md) を参照してください。

---

## 🤖 強化学習デモ（rl-training/）

PPO（Proximal Policy Optimization）を使った強化学習のデモです。

### 学習（train.py）

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

### テスト（test_rl.py）

強化学習モジュールの動作確認を行います。

```bash
./scripts/rl-training/run_tests.sh
```

### 評価（test_saved_model.py）

学習済みモデルを評価します。

```bash
# デフォルトモデルを評価
./scripts/rl-training/run_eval.sh

# 特定のチェックポイントを評価
./scripts/rl-training/run_eval.sh \
  --model models/checkpoints/checkpoint_500.pth \
  --n-episodes 5
```

詳細は [rl-training/README.md](./rl-training/README.md) を参照してください。

---

## 📊 学習ワークフロー例

### 1. 初めての学習

```bash
# Step 1: シミュレーターを試す（手動制御）
./scripts/simulator-demo/run_manual_control.sh

# Step 2: テスト実行（動作確認）
./scripts/rl-training/run_tests.sh

# Step 3: 短時間学習（動作確認）
./scripts/rl-training/run_train.sh \
  --total-iterations 5 \
  --n-steps 256 \
  --experiment-name initial_test

# Step 4: 結果を確認
./scripts/rl-training/run_eval.sh

# Step 5: TensorBoardで可視化
tensorboard --logdir=logs

# Step 6: 問題なければ本格的な学習を開始
./scripts/rl-training/run_train.sh \
  --total-iterations 1000 \
  --experiment-name main_training
```

### 2. 学習の継続

```bash
# チェックポイントから再開
./scripts/rl-training/run_train.sh \
  --resume models/checkpoints/checkpoint_500.pth \
  --total-iterations 1500
```

### 3. モデルの評価

```bash
# 学習済みモデルを評価
./scripts/rl-training/run_eval.sh

# TensorBoardで学習過程を確認
tensorboard --logdir=logs
```

---

## ⚡ よく使うコマンド

```bash
# 【シミュレーター】
# 手動制御デモ
./scripts/simulator-demo/run_manual_control.sh

# 【強化学習】
# テスト実行
./scripts/rl-training/run_tests.sh

# 短時間学習（約1分）
./scripts/rl-training/run_train.sh --total-iterations 5 --n-steps 256

# 中程度学習（約30分）
./scripts/rl-training/run_train.sh --total-iterations 100

# 本格学習（約2-3時間）
./scripts/rl-training/run_train.sh --total-iterations 1000

# モデル評価
./scripts/rl-training/run_eval.sh

# TensorBoard起動
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

## 🔍 トラブルシューティング

### エラー: `仮想環境が見つかりません`

```bash
cd /path/to/2d-simulator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install torch torchvision tensorboard
```

### エラー: `ModuleNotFoundError`

```bash
source venv/bin/activate
pip install torch torchvision tensorboard
```

### 学習が遅い

Apple Silicon (M1/M2/M3) の場合、MPSが自動的に使われます。
それでも遅い場合は `--n-steps` を減らしてください：

```bash
./scripts/rl-training/run_train.sh --n-steps 1024
```

---

## 📚 詳細ドキュメント

### ディレクトリ別

- [シミュレーターデモ](./simulator-demo/README.md) - 手動制御の詳細
- [強化学習デモ](./rl-training/README.md) - 学習・テスト・評価の詳細
- [クイックスタート](./QUICKSTART.md) - 最速で始める方法

### プロジェクト全体

- [プロジェクトREADME](../README.md)
- [実装計画](../doc/plan/init/README.md)
- [設定ファイル](../configs/ppo_default.yaml)

---

## 🎯 目的別ガイド

### シミュレーターを試したい
→ [simulator-demo/README.md](./simulator-demo/README.md)

### 強化学習を試したい
→ [rl-training/README.md](./rl-training/README.md)

### すぐに始めたい
→ [QUICKSTART.md](./QUICKSTART.md)

---

**作成日**: 2025-12-10
**バージョン**: 2.0.0
**場所**: `scripts/`
