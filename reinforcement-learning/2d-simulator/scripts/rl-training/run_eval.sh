#!/bin/bash

# 保存モデル評価の実行スクリプト

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "============================================================"
echo "保存モデル評価スクリプト"
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

# macOSでPygameのネイティブウィンドウを使用するためDISPLAY変数を解除
unset DISPLAY

# デフォルトのモデルパス
DEFAULT_MODEL="models/checkpoints/final_model.pth"

# 引数がない場合
if [ $# -eq 0 ]; then
    if [ -f "$DEFAULT_MODEL" ]; then
        echo "デフォルトモデルを評価します: $DEFAULT_MODEL"
        echo ""
        MODEL_PATH="$DEFAULT_MODEL"
    else
        echo "デフォルトモデルが見つかりません: $DEFAULT_MODEL"
        echo ""
        echo "利用可能なモデルを検索中..."

        # モデルファイルを探す
        MODELS=($(find models/checkpoints -name "*.pth" 2>/dev/null | sort -r))

        if [ ${#MODELS[@]} -eq 0 ]; then
            echo "エラー: モデルファイルが見つかりません"
            echo "先に学習を実行してください："
            echo "  ./scripts/run_train.sh"
            exit 1
        fi

        echo "見つかったモデル:"
        for i in "${!MODELS[@]}"; do
            echo "  $((i+1)). ${MODELS[$i]}"
        done
        echo ""

        # 最新のモデルを使用
        MODEL_PATH="${MODELS[0]}"
        echo "最新のモデルを使用します: $MODEL_PATH"
        echo ""
    fi
else
    # 引数がある場合はそのまま渡す
    MODEL_PATH=""
fi

# Pythonスクリプトを実行
echo "モデルを評価中..."
echo ""

if [ -n "$MODEL_PATH" ]; then
    python scripts/rl-training/test_saved_model.py --model "$MODEL_PATH" "$@"
else
    python scripts/rl-training/test_saved_model.py "$@"
fi

# 終了
echo ""
echo "評価を終了しました"
