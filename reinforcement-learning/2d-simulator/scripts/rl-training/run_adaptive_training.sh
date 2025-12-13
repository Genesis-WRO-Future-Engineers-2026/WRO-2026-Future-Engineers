#!/bin/bash

# 適応的学習スクリプトの実行ヘルパー
# 使い方: ./scripts/rl-training/run_adaptive_training.sh [gui|fast|test]

set -e

# プロジェクトルートに移動
cd "$(dirname "$0")/../.."

# 環境変数の設定
export PYTHONPATH="$(pwd):$PYTHONPATH"

# カラー出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}適応的学習システム${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 引数をチェック
MODE=${1:-gui}

case $MODE in
  gui)
    echo -e "${BLUE}モード: GUI付き学習${NC}"
    echo -e "${YELLOW}TensorBoardを別ターミナルで起動してください:${NC}"
    echo -e "${YELLOW}  tensorboard --logdir=logs${NC}"
    echo ""
    python scripts/rl-training/train_adaptive.py \
      --gui \
      --total-iterations 500 \
      --eval-freq 25 \
      --save-freq 50
    ;;

  fast)
    echo -e "${BLUE}モード: 高速学習（GUI なし）${NC}"
    echo -e "${YELLOW}TensorBoardを別ターミナルで起動してください:${NC}"
    echo -e "${YELLOW}  tensorboard --logdir=logs${NC}"
    echo ""
    python scripts/rl-training/train_adaptive.py \
      --total-iterations 2000 \
      --eval-freq 25 \
      --save-freq 100
    ;;

  test)
    echo -e "${BLUE}モード: テスト学習（短時間）${NC}"
    python scripts/rl-training/train_adaptive.py \
      --gui \
      --total-iterations 50 \
      --eval-freq 10 \
      --save-freq 25
    ;;

  resume)
    if [ -z "$2" ]; then
      echo -e "${YELLOW}使い方: $0 resume <checkpoint_path>${NC}"
      echo -e "${YELLOW}例: $0 resume models/checkpoints_adaptive/checkpoint_100.pth${NC}"
      exit 1
    fi

    CHECKPOINT=$2
    echo -e "${BLUE}モード: チェックポイントから再開${NC}"
    echo -e "${BLUE}Checkpoint: ${CHECKPOINT}${NC}"
    echo ""
    python scripts/rl-training/train_adaptive.py \
      --resume "$CHECKPOINT" \
      --total-iterations 2000 \
      --eval-freq 25 \
      --save-freq 100
    ;;

  *)
    echo -e "${YELLOW}使い方: $0 [gui|fast|test|resume]${NC}"
    echo ""
    echo "  gui     - GUI付き学習（500イテレーション）"
    echo "  fast    - 高速学習（2000イテレーション、GUIなし）"
    echo "  test    - テスト学習（50イテレーション、動作確認用）"
    echo "  resume  - チェックポイントから再開"
    echo ""
    exit 1
    ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}学習完了！${NC}"
echo -e "${GREEN}========================================${NC}"
