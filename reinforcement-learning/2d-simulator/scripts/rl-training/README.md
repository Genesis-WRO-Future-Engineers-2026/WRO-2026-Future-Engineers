# 強化学習スクリプト

PPO（Proximal Policy Optimization）を使った強化学習のスクリプト集です。

---

## 🚀 クイックスタート

### 適応的学習システム（推奨）

```bash
# 1. テストモードで動作確認（50イテレーション、約5-10分）
./scripts/rl-training/run_adaptive_training.sh test

# 2. TensorBoardで学習曲線を確認
tensorboard --logdir=logs

# 3. 本格的な学習（2000イテレーション、約4-6時間）
./scripts/rl-training/run_adaptive_training.sh fast
```

**特徴**:
- ✅ カリキュラム学習（Level 0→5へ自動進行）
- ✅ 適応的報酬スケーリング（学習フェーズに応じて自動調整）
- ✅ 学習安定性が大幅に向上

詳細: [適応的学習システムのドキュメント](../../doc/rl-training/ADAPTIVE_TRAINING.md)

---

## 📂 ファイル構成

```
rl-training/
├── README.md                      # このファイル
├── README_DEPRECATED.md           # 削除したスクリプトの記録
│
├── ⭐ メインスクリプト
│   ├── train_adaptive.py          # 適応的学習（カリキュラム + 報酬スケーリング）
│   └── run_adaptive_training.sh   # 起動スクリプト（実行可能）
│
└── 📊 評価・テスト
    ├── test_saved_model.py        # 学習済みモデルの評価
    ├── test_curriculum_basic.py   # カリキュラムマネージャーのテスト
    └── test_rl.py                 # RLモジュールの動作確認
```

---

## ⭐ 適応的学習（train_adaptive.py）

カリキュラム学習と適応的報酬スケーリングを統合した、学習安定性を重視したスクリプトです。

### 使い方

```bash
# テストモード（50イテレーション、約5-10分）
./scripts/rl-training/run_adaptive_training.sh test

# GUI付き学習（500イテレーション、約1時間）
./scripts/rl-training/run_adaptive_training.sh gui

# 高速学習（2000イテレーション、約4-6時間）
./scripts/rl-training/run_adaptive_training.sh fast

# チェックポイントから再開
./scripts/rl-training/run_adaptive_training.sh resume models/checkpoints_adaptive/checkpoint_100.pth
```

または直接Pythonスクリプトを実行：

```bash
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

python scripts/rl-training/train_adaptive.py \
  --total-iterations 2000 \
  --save-freq 50 \
  --eval-freq 25
```

### 主な特徴

#### 1. カリキュラム学習（6段階）

| Level | コース | 難易度 | 目的 |
|-------|--------|--------|------|
| Level 0 | 直線コース | ★☆☆☆☆☆ | 壁回避と前進の基礎 |
| Level 1 | 単純カーブ | ★★☆☆☆☆ | 基本的な操舵 |
| Level 2 | 標準楕円 | ★★★☆☆☆ | 周回走行の基礎 |
| Level 3 | 狭い楕円 | ★★★★☆☆ | より正確な操舵 |
| Level 4 | S字カーブ | ★★★★★☆ | 複雑な経路 |
| Level 5 | 実コース | ★★★★★★ | 実機転移 |

- Success Rate 80%で自動レベルアップ
- Success Rate < 30%でレベルダウン（オプション）

#### 2. 適応的報酬スケーリング（3フェーズ）

| Phase | 目的 | 報酬係数の特徴 |
|-------|------|---------------|
| Phase 0（基礎） | 壁回避と前進 | 時間ペナルティ弱め、方向報酬強め |
| Phase 1（探索） | チェックポイント通過 | チェックポイント報酬を強化 |
| Phase 2（最適化） | 速度最適化 | 時間ペナルティ強め、時間ボーナス強化 |

- 学習の進捗に応じて自動遷移
- 手動での報酬係数調整が不要

#### 3. 学習監視

- カリキュラムレベルの自動追跡
- 報酬フェーズの自動遷移
- TensorBoardでの詳細な可視化
  - `curriculum/level` - 現在のレベル
  - `curriculum/success_rate` - レベルごとの成功率
  - `reward/phase` - 報酬スケーリングのフェーズ

### 主要なオプション

| オプション | 説明 | デフォルト |
|-----------|------|----------|
| `--total-iterations` | 総イテレーション数 | 2000 |
| `--curriculum-success-threshold` | レベルアップ閾値 | 0.8 (80%) |
| `--curriculum-min-episodes` | レベルアップ前の最低エピソード数 | 50 |
| `--disable-adaptive-reward` | 適応的報酬を無効化 | False |
| `--save-freq` | 保存頻度（イテレーション） | 50 |
| `--eval-freq` | 評価頻度（イテレーション） | 25 |
| `--gui` | GUIで可視化しながら学習 | False |
| `--resume` | チェックポイントから再開 | None |

### 期待される学習曲線

```
Iteration 1-50:    Level 0（直線）       Success Rate 0% → 80%
Iteration 50-150:  Level 1（カーブ）     Success Rate 0% → 80%
Iteration 150-400: Level 2（標準楕円）   Success Rate 20% → 80%, Phase 0→1
Iteration 400-800: Level 3-4（狭い楕円・S字） Success Rate 30% → 80%
Iteration 800-2000: Level 5（実コース）  Success Rate 10% → 50%+, Phase 1→2
```

### 詳細ドキュメント

- [適応的学習システムの詳細](../../doc/rl-training/ADAPTIVE_TRAINING.md)
- [カリキュラムコースの説明](../../courses/curriculum/README.md)
- [カリキュラム全体の概要](../../courses/CURRICULUM_OVERVIEW.md)

---

## 📊 評価（test_saved_model.py）

学習済みモデルを読み込んで評価します。

### 基本的な使い方

```bash
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

# デフォルト（final_model.pth）を3エピソード評価
python scripts/rl-training/test_saved_model.py

# GUIで可視化しながら評価
python scripts/rl-training/test_saved_model.py --gui

# 特定のチェックポイントを評価
python scripts/rl-training/test_saved_model.py \
  --model models/checkpoints_adaptive/checkpoint_500.pth \
  --n-episodes 10 \
  --gui

# 特定のコースで評価
python scripts/rl-training/test_saved_model.py \
  --model models/checkpoints_adaptive/final_model.pth \
  --course courses/curriculum/level5_real_course.json \
  --gui
```

### オプション

| オプション | 説明 | デフォルト |
|-----------|------|----------|
| `--model` | モデルファイルのパス | `models/checkpoints/final_model.pth` |
| `--course` | コースファイルのパス | `courses/curriculum/level2_simple_oval.json` |
| `--n-episodes` | 評価エピソード数 | 3 |
| `--gui`, `--render` | GUIで可視化しながら評価 | False |

### 出力例

```
Episode 1:
  Reward: 2451.32
  Length: 456
  Checkpoints: 4/4
  Goal reached: True
  Final position: (1.05, 1.12)
  Final speed: 0.85 m/s

Summary:
Average Reward: 2384.45 ± 112.34
Average Length: 472.3 ± 45.6
Average Checkpoints: 3.7 ± 0.5
Success Rate: 66.7%
```

---

## 🧪 テスト

### カリキュラムマネージャーのテスト

```bash
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

python scripts/rl-training/test_curriculum_basic.py
```

**テスト内容**:
- カリキュラムマネージャーの基本動作
- レベルアップ/ダウンの判定
- 動的なコース切り替え

### RLモジュールのテスト

```bash
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

python scripts/rl-training/test_rl.py
```

**テスト内容**:
- ポリシーネットワークのテスト
- 価値関数ネットワークのテスト
- ロールアウトバッファのテスト
- PPOアルゴリズムのテスト
- 環境との統合テスト

---

## 📊 学習ワークフロー例

### 初めての学習

```bash
# Step 1: 動作確認（約5-10分）
./scripts/rl-training/run_adaptive_training.sh test

# Step 2: TensorBoardで可視化
tensorboard --logdir=logs
# ブラウザで http://localhost:6006 を開く

# Step 3: 問題なければ本格的な学習を開始（約4-6時間）
./scripts/rl-training/run_adaptive_training.sh fast
```

### 学習の継続

```bash
# チェックポイントから再開
./scripts/rl-training/run_adaptive_training.sh resume \
  models/checkpoints_adaptive/checkpoint_500.pth
```

### 学習結果の評価

```bash
# 最終モデルをGUIで評価
python scripts/rl-training/test_saved_model.py \
  --model models/checkpoints_adaptive/final_model.pth \
  --n-episodes 10 \
  --gui
```

---

## 🔍 トラブルシューティング

### Level 0で進まない場合

```bash
# 学習率とエントロピー係数を上げる
python scripts/rl-training/train_adaptive.py \
  --lr 5e-4 \
  --entropy-coef 0.05 \
  --total-iterations 100
```

### 特定レベルで詰まる場合

```bash
# Success Rate閾値を下げる
python scripts/rl-training/train_adaptive.py \
  --curriculum-success-threshold 0.7 \
  --total-iterations 500
```

### 学習が不安定な場合

```bash
# バッチサイズを増やし、勾配クリッピングを強化
python scripts/rl-training/train_adaptive.py \
  --batch-size 128 \
  --max-grad-norm 0.3 \
  --total-iterations 500
```

### メモリ不足の場合

```bash
# バッチサイズとステップ数を減らす
python scripts/rl-training/train_adaptive.py \
  --batch-size 32 \
  --n-steps 1024 \
  --total-iterations 500
```

---

## ⚡ よく使うコマンド

```bash
# テスト実行（動作確認）
./scripts/rl-training/run_adaptive_training.sh test

# GUI付き学習（動作確認）
./scripts/rl-training/run_adaptive_training.sh gui

# 本格学習（2000イテレーション）
./scripts/rl-training/run_adaptive_training.sh fast

# チェックポイントから再開
./scripts/rl-training/run_adaptive_training.sh resume models/checkpoints_adaptive/checkpoint_100.pth

# モデル評価（GUIで可視化）
python scripts/rl-training/test_saved_model.py --gui

# TensorBoard起動
tensorboard --logdir=logs

# カリキュラムテスト
python scripts/rl-training/test_curriculum_basic.py

# RLモジュールテスト
python scripts/rl-training/test_rl.py
```

---

## 📁 出力ファイル

### 学習中に生成されるファイル

```
models/checkpoints_adaptive/
├── checkpoint_50.pth         # 50イテレーション時点
├── checkpoint_100.pth        # 100イテレーション時点
├── checkpoint_150.pth        # ...
└── final_model.pth           # 最終モデル

logs/<experiment_name>/
├── hyperparameters.json      # ハイパーパラメータ
├── training.csv              # 学習ログ（CSV形式）
└── events.out.tfevents.*     # TensorBoardログ
```

---

## 📚 関連ドキュメント

- [適応的学習システムの詳細](../../doc/rl-training/ADAPTIVE_TRAINING.md)
- [カリキュラムコースの説明](../../courses/curriculum/README.md)
- [カリキュラム全体の概要](../../courses/CURRICULUM_OVERVIEW.md)
- [プロジェクトREADME](../../README.md)
- [手動制御デモ](../simulator-demo/README.md)

---

## 📝 削除したスクリプト

従来の学習スクリプト（`train.py`, `run_train.sh`など）は削除されました。
詳細は [README_DEPRECATED.md](./README_DEPRECATED.md) を参照してください。

---

**更新日**: 2025-12-15
**場所**: `scripts/rl-training/`
