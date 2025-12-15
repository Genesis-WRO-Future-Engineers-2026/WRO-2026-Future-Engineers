# ミニカー2Dシミュレーター - 強化学習環境

特定のコースを自動運転で最速タイムを目指すミニカーレースのための2D強化学習シミュレーター。

## プロジェクト概要

- **目的**: ミニカー自動運転の強化学習環境構築
- **センサー**: LiDAR（72方向スキャン）
- **学習手法**: PPO（Proximal Policy Optimization）
- **物理エンジン**: Box2D（2D高速シミュレーション）
- **実機転移**: Domain Randomizationによる実機転移

## 主な特徴

- 🚗 **軽量な2Dシミュレーション**: リアルタイムの10倍以上の速度
- 🎯 **ショートカット学習**: チェックポイントシステムで柔軟なルート選択
- 📈 **カリキュラム学習**: 段階的な難易度調整
- 🎮 **GUI可視化**: Pygameによるリアルタイム可視化
- 📊 **TensorBoard統合**: 学習進捗の可視化

---

## クイックスタート

### 前提条件
- Python 3.9以上
- macOS / Linux / Windows

### 1. 仮想環境の作成

```bash
cd /Users/akamite/Documents/ichis/minicar-battle/reinforcement-learning/2d-simulator
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# または
venv\Scripts\activate  # Windows
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

```bash
export PYTHONPATH="$(pwd):$PYTHONPATH"
```

### 4. 学習開始（GUI付き）

```bash
python scripts/rl-training/train.py --total-iterations 100 --gui
```

これでPygameウィンドウが開き、車両がコースを走る様子をリアルタイムで確認できます！

---

## プロジェクト構造

```
2d-simulator/
├── requirements.txt        # Python依存パッケージ
├── README.md              # このファイル
│
├── src/                   # ソースコード
│   ├── env/              # シミュレーション環境
│   ├── physics/          # 物理演算（Box2D）
│   ├── rl/               # 強化学習（PPO）
│   ├── curriculum/       # カリキュラム学習
│   ├── utils/            # ユーティリティ
│   └── deploy/           # 実機デプロイ（未実装）
│
├── courses/              # コース定義（JSON）
├── configs/              # 設定ファイル（YAML）
├── scripts/              # 実行スクリプト
│   └── rl-training/     # 学習スクリプト
├── tests/                # テストコード
├── models/               # 学習済みモデル
│   └── checkpoints/     # チェックポイント
└── logs/                 # ログファイル
```

---

## 技術スタック

- **Python**: 3.9以上
- **物理エンジン**: Box2D (box2d-py)
- **強化学習**: PyTorch (2.1.0以降)
- **環境**: Gymnasium (0.29.0)
- **可視化**: Pygame (2.5.0), TensorBoard
- **設定管理**: PyYAML
- **テスト**: pytest

---

## トレーニング

### 適応的学習システム（推奨）

```bash
# 環境をアクティベート
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 適応的学習を開始（カリキュラム学習 + 自動報酬調整）
python scripts/rl-training/train_adaptive.py --total-iterations 2000

# GUIで可視化しながら学習
python scripts/rl-training/train_adaptive.py --gui --total-iterations 500

# 便利なシェルスクリプト
./scripts/rl-training/run_adaptive_training.sh fast  # 本番学習
./scripts/rl-training/run_adaptive_training.sh test  # テスト学習

# TensorBoardで進捗を確認（別ターミナルで）
source venv/bin/activate
tensorboard --logdir=logs
# ブラウザで http://localhost:6006 を開く
```

### 個別コースでの学習

```bash
# 特定のコースで学習（カリキュラムなし）
python scripts/rl-training/train.py \
  --course courses/curriculum/level2_simple_oval.json \
  --total-iterations 1000 \
  --gui
```

### 主要なオプション

```bash
--course              # コースファイル（デフォルト: courses/curriculum/level2_simple_oval.json）
--total-iterations    # 総イテレーション数（デフォルト: 1000）
--n-steps             # 1イテレーションあたりのステップ数（デフォルト: 2048）
--n-epochs            # 1更新あたりのエポック数（デフォルト: 10）
--batch-size          # バッチサイズ（デフォルト: 64）
--lr                  # 学習率（デフォルト: 3e-4）
--gamma               # 割引率（デフォルト: 0.99）
--save-freq           # 保存頻度（デフォルト: 50）
--eval-freq           # 評価頻度（デフォルト: 50）
--device              # デバイス（cpu, cuda, mps, または auto）
--gui                 # GUI可視化を有効化
--experiment-name     # 実験名（自動生成されます）
```

### チェックポイントから再開

```bash
# 適応的学習を再開
python scripts/rl-training/train_adaptive.py \
  --resume models/checkpoints_adaptive/checkpoint_500.pth \
  --total-iterations 2000

# 個別コース学習を再開
python scripts/rl-training/train.py \
  --resume models/checkpoints/checkpoint_500.pth \
  --total-iterations 2000
```

---

## 開発ワークフロー

### テスト実行

```bash
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

# すべてのテストを実行
pytest tests/

# カバレッジ付き
pytest tests/ --cov=src --cov-report=html

# 特定のテストファイルだけ
pytest tests/test_vehicle.py -v
```

### コードフォーマット

```bash
# コードフォーマット
black src/ tests/

# Linter実行
flake8 src/ tests/
```

---

## 学習済みモデルの評価

```bash
# モデルをGUI付きで再生（デフォルトコース）
python scripts/rl-training/test_saved_model.py \
  --model models/checkpoints/final_model.pth \
  --gui

# 特定のコースで評価
python scripts/rl-training/test_saved_model.py \
  --model models/checkpoints/final_model.pth \
  --course courses/curriculum/level5_real_course.json \
  --gui

# 複数エピソード実行
python scripts/rl-training/test_saved_model.py \
  --model models/checkpoints/final_model.pth \
  --course courses/curriculum/level2_simple_oval.json \
  --n-episodes 5 \
  --gui

# 便利なシェルスクリプトでも実行可能
./scripts/rl-training/run_eval.sh --course courses/curriculum/level2_simple_oval.json --gui
```

### 評価オプション

```bash
--model          # モデルファイル（デフォルト: models/checkpoints/final_model.pth）
--course         # コースファイル（デフォルト: courses/curriculum/level2_simple_oval.json）
--n-episodes     # テストエピソード数（デフォルト: 3）
--gui / --render # GUI可視化を有効化
```

---

## 便利なエイリアス設定（オプション）

`~/.zshrc` または `~/.bashrc` に以下を追加：

```bash
# ミニカープロジェクト用
alias minicar='cd /Users/akamite/Documents/ichis/minicar-battle/reinforcement-learning/2d-simulator && source venv/bin/activate && export PYTHONPATH="$(pwd):$PYTHONPATH"'
```

設定後：

```bash
minicar
python scripts/rl-training/train.py --gui
```

---

## トラブルシューティング

### ModuleNotFoundError: No module named 'src'

```bash
# 必ずPYTHONPATHを設定してください
export PYTHONPATH="$(pwd):$PYTHONPATH"
```

### Box2Dのインストールエラー

```bash
# macOSの場合
brew install swig

# Linuxの場合
sudo apt-get install swig
```

### TensorBoardが起動しない

```bash
# tensorboardが見つからない場合
pip install tensorboard

# 起動
tensorboard --logdir=logs --port=6006
```

---

## 実装状況

| コンポーネント | 状態 | 完成度 |
|--------------|------|--------|
| 物理エンジン | ✅ 完成 | 100% |
| Gym環境 | ✅ 完成 | 100% |
| PPO実装 | ✅ 完成 | 100% |
| カリキュラム学習 | ✅ 完成 | 100% |
| GUI可視化 | ✅ 完成 | 100% |
| TensorBoard | ✅ 完成 | 100% |
| Domain Randomization | ⚠️ 未実装 | 0% |
| 実機デプロイ | ⚠️ 未実装 | 0% |

---

## ドキュメント

### 主要ドキュメント

- **[適応的学習システム](doc/ADAPTIVE_TRAINING.md)** - カリキュラム学習（Level 0-5）と自動報酬調整の詳細
- **[報酬設計](doc/REWARD_DESIGN.md)** - 報酬関数の設計思想と履歴
- **[車両仕様](doc/vehicle-specifications.md)** - TT-02実機スペック

### アーカイブ

過去の計画文書は `doc/archive/` に保存されています

---

## 更新履歴

### 2025-12-15: ドキュメント統合・整理
- すべての説明文書を`doc/`に統合
- `courses/curriculum/README.md`を`doc/ADAPTIVE_TRAINING.md`に統合（重複削除）
- `courses/CURRICULUM_OVERVIEW.md`を削除
- 古い計画文書を`doc/archive/`に移動
- README.mdに適応的学習システムの説明を追加

### 2025-12-13: 適応的学習システム実装
- カリキュラム学習（Level 0-5）を実装
- 適応的報酬スケーリング（3フェーズ）を実装
- すべてのカリキュラムコースを`courses/curriculum/`に統一

### 2025-12-12: 実コース（real-course）のチェックポイント配置最適化
- CP2-CP5の位置を調整し、ショートカット削減（40% → 21.1%に改善）
- コース可視化・診断ツールを追加

---

## ライセンス

社内プロジェクト

---

## 次のステップ

1. **学習開始**: `python scripts/rl-training/train.py --gui` で車両の動きを確認
2. **パラメータ調整**: 報酬関数やハイパーパラメータの最適化
3. **コース追加**: medium, hard難易度のコースを作成
4. **Domain Randomization実装**: 実機転移のための環境ランダム化

開発を始める準備ができました！
