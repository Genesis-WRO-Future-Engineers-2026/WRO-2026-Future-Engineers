# ミニカー2Dシミュレーター - Dockerfile
FROM python:3.9-slim

# 作業ディレクトリ
WORKDIR /app

# システムパッケージの更新とBox2D依存関係のインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    swig \
    git \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libportmidi-dev \
    && rm -rf /var/lib/apt/lists/*

# Pythonパッケージの依存関係をコピー
COPY requirements.txt .

# 依存パッケージのインストール
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# プロジェクトファイルをコピー
COPY . .

# Pythonパスの設定
ENV PYTHONPATH=/app:$PYTHONPATH

# デフォルトコマンド
CMD ["/bin/bash"]
