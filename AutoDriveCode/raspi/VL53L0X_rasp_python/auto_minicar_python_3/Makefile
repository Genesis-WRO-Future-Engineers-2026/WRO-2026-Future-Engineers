.PHONY: run test clean

# メインプログラムの実行
run:
	sudo python3 main.py

# テストの実行
test:
	pytest -v

# テスト（カバレッジ付き）
test-cov:
	pytest --cov=. --cov-report=html --cov-report=term

# クリーンアップ
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage

# ヘルプ
help:
	@echo "使用可能なコマンド:"
	@echo "  make run       - メインプログラムを実行"
	@echo "  make test      - テストを実行"
	@echo "  make test-cov  - テストをカバレッジ付きで実行"
	@echo "  make clean     - キャッシュファイルを削除"
	@echo "  make help      - このヘルプを表示"
