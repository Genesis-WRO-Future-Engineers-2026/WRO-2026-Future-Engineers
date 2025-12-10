#!/bin/bash

# ミニカー手動制御デモの実行スクリプト

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "============================================================"
echo "ミニカー2Dシミュレーター - 手動制御デモ"
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
    echo "  pip install pygame gymnasium numpy box2d-py"
    exit 1
fi

# 仮想環境を有効化
echo "仮想環境を有効化中..."
source venv/bin/activate

# Pythonスクリプトを実行（引数をそのまま渡す）
echo "手動制御デモを起動中..."
echo ""
python scripts/simulator-demo/manual_control.py "$@"

# 終了
echo ""
echo "デモを終了しました"
