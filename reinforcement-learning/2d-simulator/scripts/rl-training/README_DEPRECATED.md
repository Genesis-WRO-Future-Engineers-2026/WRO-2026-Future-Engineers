# 非推奨スクリプト

以下のスクリプトは非推奨です。新しい適応的学習システムを使用してください。

## 非推奨

### train_curriculum.py.old
**非推奨理由**: `train_adaptive.py`に統合されました

**旧機能**:
- カリキュラム学習のみ
- 固定の報酬係数（v3.2）
- 設定ファイル（YAML）ベース

**新スクリプト**: `train_adaptive.py`
- カリキュラム学習
- 適応的報酬スケーリング
- コマンドライン引数ベース
- 学習監視

**移行方法**:
```bash
# 旧
python scripts/rl-training/train_curriculum.py

# 新
./scripts/rl-training/run_adaptive_training.sh fast
# または
python scripts/rl-training/train_adaptive.py
```

## 現在使用するスクリプト

### メイン学習スクリプト

1. **train_adaptive.py** - カリキュラム学習 + 適応的報酬スケーリング（推奨）
   ```bash
   ./scripts/rl-training/run_adaptive_training.sh test
   ./scripts/rl-training/run_adaptive_training.sh fast
   ```

2. **train.py** - 単一コースでの学習（デバッグ用）
   ```bash
   python scripts/rl-training/train.py --course courses/curriculum/level0_straight.json --gui
   ```

### その他のスクリプト

- **test_saved_model.py** - 学習済みモデルのテスト
- **test_rl.py** - 強化学習の動作確認
- **test_curriculum_basic.py** - カリキュラムマネージャーのテスト

## ファイル管理

`.old`拡張子のファイルは削除してもOKです（バックアップ用に残しています）。
