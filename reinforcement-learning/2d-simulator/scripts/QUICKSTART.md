# クイックスタートガイド

このガイドでは、スクリプトを使った最速の開始方法を説明します。

---

## 🚀 30秒で始める

### 1. デモを動かす

```bash
cd /Users/akamite/Documents/ichis/minicar-battle/reinforcement-learning/2d-simulator

# 手動制御デモを起動
./scripts/simulator-demo/run_manual_control.sh
```

**操作:** ↑↓←→キーで車を動かせます。`ESC`で終了。

---

## 🤖 5分で学習を試す

### 1. テストを実行（動作確認）

```bash
# RLモジュールのテスト
./scripts/rl-demo/run_tests.sh
```

### 2. 短時間学習を実行

```bash
# 約1-2分で完了
./scripts/rl-demo/run_train.sh --total-iterations 5 --n-steps 256
```

### 3. 学習結果を確認

```bash
# モデルを評価
./scripts/rl-demo/run_eval.sh
```

---

## 📊 本格的な学習（30分〜2時間）

### 1. 学習を開始

```bash
# デフォルト設定で学習（約2-3時間）
./scripts/rl-demo/run_train.sh

# または、短めの学習（約30分）
./scripts/rl-demo/run_train.sh --total-iterations 100
```

### 2. 別ターミナルでTensorBoardを起動

```bash
source venv/bin/activate
tensorboard --logdir=logs
```

ブラウザで http://localhost:6006 を開く

### 3. 学習完了後、評価

```bash
./scripts/rl-demo/run_eval.sh
```

---

## 📁 ファイル構成

```
scripts/
├── README.md                    # 詳細ドキュメント
├── QUICKSTART.md                # このファイル
│
├── 🎮 simulator-demo/           # シミュレーターデモ
│   ├── README.md
│   ├── manual_control.py
│   └── run_manual_control.sh    # 手動制御デモ
│
└── 🤖 rl-demo/                  # 強化学習デモ
    ├── README.md
    ├── train.py
    ├── run_train.sh             # 学習実行（簡単）
    ├── test_rl.py
    ├── run_tests.sh             # テスト実行（簡単）
    ├── test_saved_model.py
    └── run_eval.sh              # モデル評価（簡単）
```

---

## 🎯 目的別コマンド

### シミュレーターを試したい
```bash
./scripts/simulator-demo/run_manual_control.sh
```

### 動作確認したい
```bash
./scripts/rl-demo/run_tests.sh
```

### すぐに学習を始めたい
```bash
./scripts/rl-demo/run_train.sh --total-iterations 10
```

### 本格的に学習したい
```bash
./scripts/rl-demo/run_train.sh --total-iterations 1000
```

### 学習結果を見たい
```bash
./scripts/rl-demo/run_eval.sh

# または TensorBoard で
tensorboard --logdir=logs
```

---

## ⚡ よく使うコマンド

```bash
# 【シミュレーター】
# 手動制御
./scripts/simulator-demo/run_manual_control.sh

# 【強化学習】
# テスト
./scripts/rl-demo/run_tests.sh

# 短時間学習（5イテレーション、約1分）
./scripts/rl-demo/run_train.sh --total-iterations 5 --n-steps 256

# 中程度学習（100イテレーション、約30分）
./scripts/rl-demo/run_train.sh --total-iterations 100

# 本格学習（1000イテレーション、約2-3時間）
./scripts/rl-demo/run_train.sh --total-iterations 1000

# モデル評価
./scripts/rl-demo/run_eval.sh

# TensorBoard
source venv/bin/activate && tensorboard --logdir=logs
```

---

## 🔧 トラブルシューティング

### 「仮想環境が見つかりません」

```bash
cd /Users/akamite/Documents/ichis/minicar-battle/reinforcement-learning/2d-simulator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install torch torchvision tensorboard
```

### 「モジュールが見つかりません」

```bash
source venv/bin/activate
pip install torch torchvision tensorboard
```

### 学習が遅い

Apple Silicon (M1/M2/M3) の場合、MPSが自動的に使われます。
それでも遅い場合は `--n-steps` を減らしてください：

```bash
./scripts/rl-demo/run_train.sh --n-steps 1024
```

---

## 📚 詳細情報

より詳しい情報は以下を参照してください：

- [scripts/README.md](./README.md) - スクリプト全体の説明
- [simulator-demo/README.md](./simulator-demo/README.md) - シミュレーターデモの詳細
- [rl-demo/README.md](./rl-demo/README.md) - 強化学習デモの詳細

---

**作成日**: 2025-12-10
**バージョン**: 2.0.0
**場所**: `scripts/QUICKSTART.md`
