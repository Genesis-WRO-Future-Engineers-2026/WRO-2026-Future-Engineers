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
- 🔄 **Domain Randomization**: 実機転移を促進
- 📊 **可視化ツール**: Pygame、TensorBoard統合

---

## クイックスタート（Docker）

### 前提条件
- Docker Desktop
- Docker Compose V2以上

### 1. リポジトリのクローンと移動

```bash
cd /Users/akamite/Documents/ichis/minicar-battle/reinforcement-learning/2d-simulator
```

### 2. Dockerイメージのビルド

```bash
docker compose build
```

### 3. 開発環境の起動

```bash
# 開発環境に入る
docker compose run --rm dev

# コンテナ内でPythonバージョン確認
python --version
```

### 4. その他のサービス

```bash
# Jupyter Notebook起動 → http://localhost:8888
docker compose up jupyter

# TensorBoard起動 → http://localhost:6006
docker compose up tensorboard
```

詳細は [doc/DOCKER_SETUP.md](./doc/DOCKER_SETUP.md) を参照してください。

---

## ローカル環境でのセットアップ（Docker不使用）

### 1. 仮想環境の作成

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# または
venv\Scripts\activate  # Windows
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. プロジェクト構造の作成

```bash
# 必要なディレクトリを作成
mkdir -p src/{env,physics,rl,curriculum,domain_randomization,utils,deploy}
mkdir -p courses/{easy,medium,hard}
mkdir -p configs scripts tests notebooks
mkdir -p models/{checkpoints,best}
mkdir -p logs/{tensorboard,training}
```

---

## プロジェクト構造

```
2d-simulator/
├── Dockerfile              # Dockerイメージ定義
├── docker-compose.yml      # Docker Compose設定
├── requirements.txt        # Python依存パッケージ
├── README.md              # このファイル
│
├── doc/                   # ドキュメント
│   ├── DOCKER_SETUP.md    # Docker環境セットアップガイド
│   └── plan/init/         # 実装計画書（8ファイル）
│
├── src/                   # ソースコード（今後実装）
│   ├── env/              # シミュレーション環境
│   ├── physics/          # 物理演算
│   ├── rl/               # 強化学習
│   ├── curriculum/       # カリキュラム学習
│   ├── domain_randomization/  # Domain Randomization
│   ├── utils/            # ユーティリティ
│   └── deploy/           # 実機デプロイ
│
├── courses/              # コース定義（JSON）
├── configs/              # 設定ファイル（YAML）
├── scripts/              # 実行スクリプト
├── tests/                # テストコード
├── notebooks/            # Jupyter Notebooks
├── models/               # 学習済みモデル
└── logs/                 # ログファイル
```

---

## 実装計画

詳細な実装計画は `doc/plan/init/` に8つのドキュメントとして保存されています：

1. **00_overview.md** - プロジェクト概要
2. **01_project_structure.md** - ディレクトリ構造設計
3. **02_tech_stack.md** - 技術スタック
4. **03_implementation_phases.md** - 実装フェーズ（8-10週間）
5. **04_component_design.md** - コンポーネント詳細設計
6. **05_config_and_testing.md** - 設定とテスト戦略
7. **06_sim_to_real.md** - 実機転移戦略
8. **07_getting_started.md** - 実装開始ガイド

### 実装スケジュール（予定）

| フェーズ | 期間 | 内容 |
|---------|------|------|
| Phase 1 | 2-3週 | 2Dシミュレーター基盤構築 |
| Phase 2 | 2-3週 | PPO強化学習統合 |
| Phase 3 | 2-3週 | カリキュラム学習、Domain Randomization |
| Phase 4 | 1-2週 | 実機転移準備と検証 |

---

## 技術スタック

- **Python**: 3.9
- **物理エンジン**: Box2D (pybox2d==2.3.10)
- **強化学習**: PyTorch (2.0.0)
- **環境**: Gymnasium (0.29.0)
- **可視化**: Pygame (2.5.0), Matplotlib, TensorBoard
- **設定管理**: PyYAML
- **テスト**: pytest
- **コード品質**: Black, flake8
- **デプロイ**: ONNX Runtime

---

## 開発ワークフロー

### Dockerを使う場合

```bash
# 1. コードを編集（ホスト側）
vim src/env/vehicle.py

# 2. テストを実行（コンテナ内）
docker compose run --rm dev pytest tests/test_vehicle.py

# 3. コードフォーマット
docker compose run --rm dev black src/

# 4. Linter実行
docker compose run --rm dev flake8 src/
```

### ローカル環境の場合

```bash
# 1. テスト実行
pytest tests/

# 2. コードフォーマット
black src/ tests/

# 3. Linter実行
flake8 src/ tests/
```

---

## トレーニング（実装後）

### Docker環境

```bash
# TensorBoardを起動
docker compose up -d tensorboard

# トレーニング実行
docker compose up train

# ブラウザで http://localhost:6006 を開いて進捗確認
```

### ローカル環境

```bash
# トレーニング実行
python scripts/train.py --config configs/training_config.yaml

# 別ターミナルでTensorBoard起動
tensorboard --logdir=logs/tensorboard
```

---

## 評価と可視化（実装後）

```bash
# モデルの評価
docker compose run --rm dev python scripts/evaluate.py --model models/best/policy.pth

# 軌跡の可視化
docker compose run --rm dev python scripts/visualize.py --model models/best/policy.pth
```

---

## テスト

```bash
# すべてのテストを実行
docker compose run --rm dev pytest tests/

# カバレッジ付き
docker compose run --rm dev pytest tests/ --cov=src --cov-report=html

# 特定のテストファイルだけ
docker compose run --rm dev pytest tests/test_vehicle.py -v
```

---

## 実機デプロイ（実装後）

### モデル変換（PyTorch → ONNX）

```bash
docker compose run --rm dev python src/deploy/model_converter.py \
  --input models/best/policy.pth \
  --output models/best/policy.onnx
```

### Raspberry Piでの推論

```bash
# Raspberry Pi上で
python src/deploy/rpi_inference.py --model models/best/policy.onnx
```

詳細は [doc/plan/init/06_sim_to_real.md](./doc/plan/init/06_sim_to_real.md) を参照。

---

## トラブルシューティング

### Docker関連
- [doc/DOCKER_SETUP.md](./doc/DOCKER_SETUP.md) のトラブルシューティングセクション参照

### 学習関連
- [doc/plan/init/05_config_and_testing.md](./doc/plan/init/05_config_and_testing.md) のデバッグセクション参照

---

## ライセンス

社内プロジェクト

---

## 作成日

2025-12-09

---

## 次のステップ

1. **環境セットアップ**: Docker環境のビルドと動作確認
2. **実装計画の確認**: `doc/plan/init/README.md` から読み始める
3. **Phase 1開始**: `doc/plan/init/07_getting_started.md` に従って実装開始

開発を始める準備ができました！
