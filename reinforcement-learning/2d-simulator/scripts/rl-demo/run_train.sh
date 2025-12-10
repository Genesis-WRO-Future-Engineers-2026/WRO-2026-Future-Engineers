#!/bin/bash

# PPO学習の実行スクリプト

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "============================================================"
echo "PPO学習スクリプト"
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

# PYTHONPATHを設定
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 引数がない場合はヘルプを表示
if [ $# -eq 0 ]; then
    echo "学習スクリプトを起動します（デフォルト設定）"
    echo ""
    echo "カスタム設定で実行する場合は引数を指定してください："
    echo "  ./scripts/run_train.sh --total-iterations 100 --experiment-name my_exp"
    echo ""
    read -p "このまま実行しますか？ (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "キャンセルしました"
        exit 0
    fi
fi

# Pythonスクリプトを実行
echo "学習を開始します..."
echo ""
python scripts/rl-demo/train.py "$@"

# 終了
echo ""
echo "学習スクリプトを終了しました"
