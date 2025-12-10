.PHONY: help setup train train-gui train-curriculum eval test format lint clean

# 仮想環境とPYTHONPATHの設定
VENV = venv
PYTHON = $(VENV)/bin/python
ACTIVATE = . $(VENV)/bin/activate && export PYTHONPATH=$(PWD):$$PYTHONPATH

# デフォルトターゲット
help:
	@echo "利用可能なコマンド:"
	@echo "  make setup              - 仮想環境のセットアップと依存関係のインストール"
	@echo "  make train              - 学習実行（GUIなし）"
	@echo "  make train-gui          - 学習実行（GUI付き）"
	@echo "  make train-curriculum   - カリキュラム学習実行"
	@echo "  make eval               - 学習済みモデルの評価"
	@echo "  make test               - テスト実行"
	@echo "  make format             - コードフォーマット（black）"
	@echo "  make lint               - Linter実行（flake8）"
	@echo "  make clean              - キャッシュファイルの削除"

# 仮想環境のセットアップ
setup:
	python3 -m venv $(VENV)
	$(ACTIVATE) && pip install --upgrade pip
	$(ACTIVATE) && pip install -r requirements.txt
	@echo "セットアップ完了！以下のコマンドで仮想環境に入れます:"
	@echo "  source venv/bin/activate"
	@echo "  export PYTHONPATH=\$$(pwd):\$$PYTHONPATH"

# 開発用シェルを起動（仮想環境とPYTHONPATH設定済み）
dev:
	@echo "仮想環境を有効化したシェルを起動します..."
	@echo "終了するには 'exit' を入力してください"
	@echo 'source venv/bin/activate' > /tmp/.make_dev_init
	@echo 'export PYTHONPATH=$(PWD):$$PYTHONPATH' >> /tmp/.make_dev_init
	@echo 'echo "\n開発環境準備完了！ (仮想環境: venv, PYTHONPATH設定済み)\n"' >> /tmp/.make_dev_init
	@ZDOTDIR=/tmp zsh -c "source /tmp/.make_dev_init && zsh"

# 学習実行（GUIなし）
train:
	$(ACTIVATE) && python scripts/rl-training/train.py --total-iterations 1000

# 学習実行（GUI付き）
train-gui:
	$(ACTIVATE) && python scripts/rl-training/train.py --total-iterations 100 --gui

# カリキュラム学習
train-curriculum:
	$(ACTIVATE) && python scripts/rl-training/train_curriculum.py

# 学習済みモデルの評価
eval:
	$(ACTIVATE) && python scripts/rl-training/test_saved_model.py --model models/checkpoints/final_model.pth

# テスト実行
test:
	$(ACTIVATE) && pytest tests/ -v

# テスト実行（カバレッジ付き）
test-coverage:
	$(ACTIVATE) && pytest tests/ --cov=src --cov-report=html

# コードフォーマット
format:
	$(ACTIVATE) && black src/ tests/ scripts/

# Linter実行
lint:
	$(ACTIVATE) && flake8 src/ tests/ scripts/

# TensorBoard起動
tensorboard:
	$(ACTIVATE) && tensorboard --logdir=logs

# キャッシュファイルの削除
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
