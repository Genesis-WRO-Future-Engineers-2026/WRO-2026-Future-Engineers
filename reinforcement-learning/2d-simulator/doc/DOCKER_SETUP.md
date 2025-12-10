# Docker環境セットアップガイド

## 概要

このプロジェクトではDocker Composeを使用して、開発環境、トレーニング環境、Jupyter Notebook、TensorBoardを提供しています。

## 前提条件

- Docker Desktop（最新版推奨）
- Docker Compose V2以上

### Dockerのインストール確認

```bash
docker --version
docker compose version
```

## 提供されるサービス

### 1. dev - 開発環境
インタラクティブな開発用のコンテナ。コードの実装、テスト、デバッグに使用。

### 2. train - トレーニング環境
強化学習の学習を実行するためのコンテナ。

### 3. jupyter - Jupyter Notebook
データ分析や可視化用のJupyter Notebook環境。

### 4. tensorboard - TensorBoard
学習過程をリアルタイムで可視化。

---

## クイックスタート

### 1. Dockerイメージのビルド

```bash
cd /Users/akamite/Documents/ichis/minicar-battle/reinforcement-learning/2d-simulator

# すべてのサービスをビルド
docker compose build

# 特定のサービスだけビルド
docker compose build dev
```

### 2. 開発環境の起動

```bash
# 開発環境コンテナを起動してシェルに入る
docker compose run --rm dev

# コンテナ内で作業
root@xxx:/app# python --version
root@xxx:/app# pytest tests/
root@xxx:/app# exit
```

### 3. トレーニングの実行

```bash
# トレーニングを実行（scripts/train.pyが実装された後）
docker compose up train

# バックグラウンドで実行
docker compose up -d train

# ログを確認
docker compose logs -f train
```

### 4. Jupyter Notebookの起動

```bash
# Jupyter Notebookを起動
docker compose up jupyter

# ブラウザでアクセス
# http://localhost:8888
```

### 5. TensorBoardの起動

```bash
# TensorBoardを起動
docker compose up tensorboard

# ブラウザでアクセス
# http://localhost:6006
```

---

## よく使うコマンド

### コンテナの起動と停止

```bash
# すべてのサービスを起動
docker compose up

# バックグラウンドで起動
docker compose up -d

# 特定のサービスだけ起動
docker compose up dev

# すべてのサービスを停止
docker compose down

# ボリュームも削除して停止
docker compose down -v
```

### コンテナ内でコマンド実行

```bash
# 開発環境でPythonスクリプトを実行
docker compose run --rm dev python scripts/train.py

# テストを実行
docker compose run --rm dev pytest tests/

# コードフォーマット
docker compose run --rm dev black src/ tests/

# Linter実行
docker compose run --rm dev flake8 src/ tests/
```

### ログの確認

```bash
# すべてのサービスのログ
docker compose logs

# 特定のサービスのログ
docker compose logs train

# リアルタイムでログを表示（-f）
docker compose logs -f train
```

### コンテナの状態確認

```bash
# 起動中のコンテナを確認
docker compose ps

# すべてのコンテナを確認
docker compose ps -a
```

---

## ボリュームマウント

以下のディレクトリがホストとコンテナ間で共有されています：

| ホスト | コンテナ | 用途 |
|--------|----------|------|
| `.` | `/app` | プロジェクト全体 |
| `./logs` | `/app/logs` | ログファイル |
| `./models` | `/app/models` | 学習済みモデル |

これにより、コンテナ内での変更がホストに反映され、コンテナを削除してもデータが保持されます。

---

## 開発ワークフロー

### パターン1: インタラクティブ開発

```bash
# 開発環境に入る
docker compose run --rm dev

# コンテナ内で作業
root@xxx:/app# python src/env/vehicle.py
root@xxx:/app# pytest tests/test_vehicle.py
root@xxx:/app# exit
```

### パターン2: ワンショットコマンド

```bash
# テスト実行
docker compose run --rm dev pytest tests/

# コードフォーマット
docker compose run --rm dev black src/

# 特定のスクリプト実行
docker compose run --rm dev python scripts/evaluate.py
```

### パターン3: 継続的な学習

```bash
# TensorBoardを起動（別ターミナル）
docker compose up tensorboard

# トレーニングを実行
docker compose up train

# ブラウザでhttp://localhost:6006を開いて進捗確認
```

---

## トラブルシューティング

### 問題1: Dockerイメージのビルドが失敗する

**原因:** 依存パッケージのインストールエラー

**解決策:**
```bash
# キャッシュを使わずに再ビルド
docker compose build --no-cache dev

# ログを詳細に確認
docker compose build --progress=plain dev
```

### 問題2: ポートが既に使用されている

**症状:** `port is already allocated`

**解決策:**
```bash
# 使用中のポートを確認
lsof -i :8888
lsof -i :6006

# 既存のコンテナを停止
docker compose down

# ポート番号を変更（docker-compose.ymlを編集）
ports:
  - "8889:8888"  # 8888 → 8889に変更
```

### 問題3: コンテナ内でファイルが見えない

**原因:** ボリュームマウントの問題

**解決策:**
```bash
# 現在のディレクトリを確認
pwd
# /Users/akamite/Documents/ichis/minicar-battle/reinforcement-learning/2d-simulator

# docker-compose.ymlの場所で実行しているか確認
ls docker-compose.yml

# コンテナを再起動
docker compose down
docker compose up dev
```

### 問題4: GPU対応が必要

**Dockerfileの修正:**
```dockerfile
# CUDAベースイメージに変更
FROM pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime
```

**docker-compose.ymlの修正:**
```yaml
services:
  train:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

## 環境変数の設定

`.env`ファイルを作成して環境変数を管理できます。

```bash
# .envファイル作成
cat > .env << 'EOF'
# TensorBoard設定
TENSORBOARD_PORT=6006

# Jupyter設定
JUPYTER_PORT=8888

# 学習設定
LEARNING_RATE=3e-4
BATCH_SIZE=256
EOF
```

docker-compose.ymlで使用:
```yaml
services:
  tensorboard:
    ports:
      - "${TENSORBOARD_PORT}:6006"
```

---

## パフォーマンス最適化

### ビルドキャッシュの活用

```bash
# 依存関係だけを先にインストール
# Dockerfileで COPY requirements.txt を先に行う
```

### マルチステージビルド（本番環境用）

```dockerfile
# Dockerfile.prod
FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "scripts/train.py"]
```

---

## セキュリティ

### 本番環境での注意点

1. **rootユーザーを避ける**
```dockerfile
# Dockerfileに追加
RUN useradd -m -u 1000 appuser
USER appuser
```

2. **Jupyter Notebookのトークン設定**
```yaml
# docker-compose.ymlで本番用設定
command: jupyter notebook --ip=0.0.0.0 --NotebookApp.token='your-secure-token'
```

---

## まとめ

Docker環境が正しくセットアップできたら、以下のコマンドで確認してください：

```bash
# 1. ビルド
docker compose build dev

# 2. 動作確認
docker compose run --rm dev python --version

# 3. 依存パッケージの確認
docker compose run --rm dev pip list

# 4. プロジェクト構造の確認
docker compose run --rm dev ls -la
```

これで開発環境の準備が完了です！
