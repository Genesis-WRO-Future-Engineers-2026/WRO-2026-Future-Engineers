FROM python:3.9-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
RUN pip install --no-cache-dir pytest pytest-cov pytest-mock

# プロジェクトファイルをコピー
COPY *.py ./

# デフォルトコマンドはテスト実行（RPi.GPIOモジュールが不要なテストのみ）
CMD ["pytest", "-v", "test_geometry.py", "test_steering_controller.py"]
