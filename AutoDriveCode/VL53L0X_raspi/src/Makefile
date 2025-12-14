.PHONY: help run test test-cov docker-build docker-shell clean docker-clean

# デフォルトターゲット
.DEFAULT_GOAL := help

# ヘルプ
help:
	@echo "使用可能なコマンド:"
	@echo ""
	@echo "  make run              - メインプログラムを実行（Raspberry Pi上）"
	@echo ""
	@echo "  make test             - Docker でテストを実行"
	@echo "  make test-cov         - Docker でテスト（カバレッジ付き）"
	@echo "  make docker-shell     - Docker コンテナに入る（デバッグ用）"
	@echo ""
	@echo "  make clean            - キャッシュファイルを削除"
	@echo "  make docker-clean     - Docker イメージを削除"

# メインプログラムの実行（Raspberry Pi上で）
run:
	sudo python3 main.py

# Docker イメージをビルド
docker-build:
	docker build -t minicar-test .

# Docker でテストを実行
test: docker-build
	docker run --rm minicar-test

# Docker でテスト（カバレッジ付き）
test-cov: docker-build
	docker run --rm minicar-test pytest --cov=. --cov-report=term

# Docker コンテナに入る（デバッグ用）
docker-shell: docker-build
	docker run --rm -it minicar-test /bin/bash

# クリーンアップ
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage

# Docker イメージを削除
docker-clean:
	docker rmi minicar-test 2>/dev/null || true
