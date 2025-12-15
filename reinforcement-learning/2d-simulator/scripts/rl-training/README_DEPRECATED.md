# 非推奨・削除されたスクリプト

このドキュメントは、適応的学習システムの導入に伴って削除されたスクリプトの記録です。

---

## 削除されたスクリプト（2025-12-15）

### 1. `train.py` - 単一コース学習スクリプト

**削除理由**: 適応的学習システム（`train_adaptive.py`）に完全に置き換えられました。

**従来の役割**:
- 単一コースでPPO学習を実行
- 基本的な学習ループの提供

**代替方法**:
```bash
# 従来: 単一コースで学習
python scripts/rl-training/train.py --course courses/curriculum/level2_simple_oval.json

# 新: 適応的学習システムを使用（自動的に全レベルを進める）
./scripts/rl-training/run_adaptive_training.sh fast
```

---

### 2. `run_train.sh` - 学習起動スクリプト

**削除理由**: `run_adaptive_training.sh`に置き換えられました。

**従来の役割**:
- `train.py`を起動するためのシェルラッパー

**代替方法**:
```bash
# 従来
./scripts/rl-training/run_train.sh --total-iterations 1000

# 新
./scripts/rl-training/run_adaptive_training.sh fast
```

---

### 3. `train_curriculum.py.old` - 旧カリキュラム学習スクリプト

**削除理由**: 適応的報酬スケーリングが統合された新しいカリキュラムシステムに置き換えられました。

**従来の役割**:
- カリキュラム学習の初期実装
- 手動で報酬係数を調整する必要があった

**代替方法**:
```bash
# 新: カリキュラム学習 + 適応的報酬スケーリング
./scripts/rl-training/run_adaptive_training.sh fast
```

**主な改善点**:
- ✅ 適応的報酬スケーリングの統合（自動調整）
- ✅ 6段階のカリキュラム（Level 0-5）
- ✅ 学習監視とTensorBoard統合
- ✅ より安定した学習曲線

---

### 4. `run_eval.sh` - 評価起動スクリプト

**削除理由**: シェルラッパーが不要。Pythonスクリプトを直接実行する方がシンプル。

**従来の役割**:
- `test_saved_model.py`を起動するためのシェルラッパー

**代替方法**:
```bash
# 直接Pythonスクリプトを実行
python scripts/rl-training/test_saved_model.py --gui
```

---

### 5. `run_tests.sh` - テスト起動スクリプト

**削除理由**: シェルラッパーが不要。Pythonスクリプトを直接実行する方がシンプル。

**従来の役割**:
- `test_rl.py`を起動するためのシェルラッパー

**代替方法**:
```bash
# 直接Pythonスクリプトを実行
python scripts/rl-training/test_rl.py
python scripts/rl-training/test_curriculum_basic.py
```

---

## マイグレーションガイド

### 従来の学習ワークフロー → 適応的学習システム

#### 従来（削除済み）

```bash
# Step 1: テスト実行
./scripts/rl-training/run_tests.sh

# Step 2: 短時間学習
./scripts/rl-training/run_train.sh \
  --total-iterations 100 \
  --course courses/easy/simple_oval.json

# Step 3: 評価
./scripts/rl-training/run_eval.sh --gui
```

#### 新システム（推奨）

```bash
# Step 1: 動作確認（テストモード）
./scripts/rl-training/run_adaptive_training.sh test

# Step 2: TensorBoardで可視化
tensorboard --logdir=logs

# Step 3: 本格学習
./scripts/rl-training/run_adaptive_training.sh fast

# Step 4: 評価
python scripts/rl-training/test_saved_model.py --gui
```

---

## 削除されたスクリプトの詳細

### 設計上の問題点

**従来システム**:
1. **手動での報酬係数調整が必要**
   - v3.0 → v3.1 → v3.2と試行錯誤
   - 学習が不安定（Success Rate 0%が続く）

2. **単一コースのみ**
   - カリキュラム学習が別スクリプト
   - 統合されていない

3. **シェルラッパーの乱立**
   - `run_train.sh`, `run_eval.sh`, `run_tests.sh`
   - 各スクリプトがPythonスクリプトを呼び出すだけ

**新システムの改善**:
1. ✅ **適応的報酬スケーリング**
   - 学習の進捗に応じて自動調整
   - 3フェーズ（基礎 → 探索 → 最適化）

2. ✅ **統合されたカリキュラム学習**
   - 6段階のレベル（Level 0-5）
   - Success Rate 80%で自動レベルアップ

3. ✅ **シンプルなインターフェース**
   - 1つのメインスクリプト（`train_adaptive.py`）
   - 1つのシェルラッパー（`run_adaptive_training.sh`）

---

## 削除日

**2025年12月15日**: 適応的学習システムへの移行完了に伴い、従来のスクリプトを削除

---

## 関連ドキュメント

- [適応的学習システムの詳細](../../doc/ADAPTIVE_TRAINING.md)
- [現在のREADME](./README.md)
- [カリキュラムコースの説明](../../doc/ADAPTIVE_TRAINING.md)

---

**場所**: `scripts/rl-training/README_DEPRECATED.md`
