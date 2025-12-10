#!/bin/bash

# RLモジュールテストの実行スクリプト

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "============================================================"
echo "強化学習モジュール テストスイート"
echo "============================================================"
echo ""
echo "プロジェクトルート: $PROJECT_ROOT"
echo ""

# 仮想環境の確認
if [ ! -d "venv" ]; then
    echo "エラー: 仮想環境が見つかりません"
    echo "以下のコマンドで仮想環境を作成してください："
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# 仮想環境を有効化
echo "仮想環境を有効化中..."
source venv/bin/activate

# Pythonスクリプトを実行
echo "テストを実行中..."
echo ""
python scripts/test_rl.py

# 終了コードを保存
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ すべてのテストが成功しました"
else
    echo "✗ テストが失敗しました（終了コード: $EXIT_CODE）"
fi

exit $EXIT_CODE
