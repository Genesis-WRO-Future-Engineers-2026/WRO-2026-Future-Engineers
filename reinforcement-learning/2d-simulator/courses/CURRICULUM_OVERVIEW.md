# カリキュラム学習コース構成

適応的学習システムで使用する6段階のカリキュラムコースの概要

## ディレクトリ構成

```
courses/
├── curriculum/              # カリキュラム学習用コース（Level 0-5）
│   ├── level0_straight.json
│   ├── level1_simple_curve.json
│   ├── level2_simple_oval.json
│   ├── level3_narrow_oval.json
│   ├── level4_s_curve.json
│   ├── level5_real_course.json
│   └── README.md
│
├── real/                    # 実コースのオリジナルと派生（参考用）
│   ├── real-course_course.json          # Level 5のコピー元
│   └── variations/                      # 実コースのバリエーション
│       ├── real_course_var1.json
│       └── ...
│
└── CURRICULUM_OVERVIEW.md   # このファイル
```

**注**: easy/medium/hard/ディレクトリは削除されました（curriculum/に統合）

## カリキュラム全体像

```
Level 0: curriculum/level0_straight.json      ★☆☆☆☆☆ (超簡単)
         ↓ Success Rate 80%達成で自動レベルアップ

Level 1: curriculum/level1_simple_curve.json  ★★☆☆☆☆ (簡単)
         ↓

Level 2: easy/simple_oval.json                ★★★☆☆☆ (easy)
         ↓

Level 3: medium/narrow_oval.json              ★★★★☆☆ (medium)
         ↓

Level 4: hard/s_curve.json                    ★★★★★☆ (hard)
         ↓

Level 5: real/real-course_course.json         ★★★★★★ (最終目標)
```

## 各レベルの詳細

### 🟢 Level 0: 直線コース
- **ファイル**: `courses/curriculum/level0_straight.json`
- **ディレクトリ**: curriculum（学習専用）
- **目的**: 壁回避と前進の基礎
- **構成**: 平行な2本の壁の間を直進
- **チェックポイント**: なし
- **期待イテレーション**: 1-50
- **学習内容**: ランダムな動き → 前進

### 🟢 Level 1: 単純カーブ
- **ファイル**: `courses/curriculum/level1_simple_curve.json`
- **ディレクトリ**: curriculum（学習専用）
- **目的**: 基本的な操舵
- **構成**: L字型のコーナー1つ
- **チェックポイント**: 1個
- **期待イテレーション**: 50-150
- **学習内容**: 前進 → カーブ

### 🟡 Level 2: 標準楕円
- **ファイル**: `courses/easy/simple_oval.json`
- **ディレクトリ**: easy（既存コース活用）
- **目的**: 周回走行の基礎
- **構成**: 楕円形の周回コース
- **チェックポイント**: 4個
- **期待イテレーション**: 150-400
- **学習内容**: カーブ → チェックポイント通過

### 🟡 Level 3: 狭い楕円
- **ファイル**: `courses/medium/narrow_oval.json`
- **ディレクトリ**: medium（既存コース活用）
- **目的**: より正確な操舵
- **構成**: 狭い楕円形コース
- **チェックポイント**: 4個
- **期待イテレーション**: 400-600
- **学習内容**: 正確な操舵

### 🔴 Level 4: S字カーブ
- **ファイル**: `courses/hard/s_curve.json`
- **ディレクトリ**: hard（既存コース活用）
- **目的**: 複雑な経路
- **構成**: S字カーブと障害物
- **チェックポイント**: 4個
- **期待イテレーション**: 600-800
- **学習内容**: 複雑な経路選択

### 🔴 Level 5: 実コース
- **ファイル**: `courses/real/real-course_course.json`
- **ディレクトリ**: real（既存コース活用）
- **目的**: 実機転移
- **構成**: 実際のレース場を模したコース
- **チェックポイント**: 5個
- **期待イテレーション**: 800-2000
- **学習内容**: 最終目標、実機で使える走行

## ディレクトリ構成の設計思想

### curriculum/ - カリキュラム学習専用
**役割**: すべてのカリキュラムレベル（Level 0-5）

**特徴**:
- ✅ **1箇所で完結**: Level 0〜5まですべて統一
- ✅ **連番管理**: level0, level1, level2... と直感的
- ✅ **学習最適化**: 段階的な難易度設定

**含まれるコース**:
- Level 0-1: 新規作成（超基礎）
- Level 2-5: 既存コースからコピー（easy/medium/hard/realから）

### real/ - 実コースのオリジナル（参考用）
**役割**: 実際のレース場データの保管

**特徴**:
- 📁 **オリジナルデータ**: 実コースの元ファイル
- 🔄 **派生バリエーション**: variations/に12種類のバリエーション
- 🎯 **Level 5のコピー元**: curriculum/level5_real_course.jsonのソース

**使い方**:
- カリキュラム学習では `curriculum/level5_real_course.json` を使用
- このディレクトリは参考・バックアップ用
- 実コースが更新された場合、`cp real/real-course_course.json curriculum/level5_real_course.json`でコピー

## ディレクトリの整理履歴

### ✅ 統合完了（2025-12-13）

**整理前**:
```
courses/easy/simple_oval.json
courses/medium/narrow_oval.json
courses/hard/s_curve.json
courses/hard/tight_oval.json
courses/real/real-course_course.json
courses/curriculum/level0_straight.json
courses/curriculum/level1_simple_curve.json
```

**整理後**:
```
courses/curriculum/level0_straight.json      (新規)
courses/curriculum/level1_simple_curve.json  (新規)
courses/curriculum/level2_simple_oval.json   (easy/からコピー)
courses/curriculum/level3_narrow_oval.json   (medium/からコピー)
courses/curriculum/level4_s_curve.json       (hard/からコピー)
courses/curriculum/level5_real_course.json   (real/からコピー)
courses/real/                                (オリジナル保管用)
```

### ❌ 削除したディレクトリ
- `courses/easy/` - curriculum/level2にコピー後削除
- `courses/medium/` - curriculum/level3にコピー後削除
- `courses/hard/` - curriculum/level4にコピー後削除（tight_oval.jsonは未使用のため削除）

### ✅ 残したディレクトリ
- `courses/curriculum/` - カリキュラム学習用（Level 0-5）
- `courses/real/` - 実コースのオリジナルとバリエーション（参考用）

## 学習の流れ

### 自動レベルアップ
```python
# カリキュラムマネージャーが自動的に管理
if success_rate >= 0.8 and episodes >= 50:
    curriculum.advance_level()  # 次のレベルへ
```

### 期待される学習時間
- **Level 0**: 5-10分（50イテレーション）
- **Level 1**: 10-20分（100イテレーション）
- **Level 2**: 30-60分（250イテレーション）
- **Level 3**: 30-60分（200イテレーション）
- **Level 4**: 30-60分（200イテレーション）
- **Level 5**: 2-4時間（1200イテレーション）

**合計**: 約4-6時間で全レベル完了（M4チップ、GUIなし）

## 使い方

### 自動カリキュラム学習
```bash
# すべてのレベルを自動的に進める
./scripts/rl-training/run_adaptive_training.sh fast
```

### 個別レベルのテスト
```bash
# Level 0のみ
python scripts/rl-training/train.py \
  --course courses/curriculum/level0_straight.json \
  --gui

# Level 5（実コース）のみ
python scripts/rl-training/train.py \
  --course courses/real/real-course_course.json \
  --gui
```

## トラブルシューティング

### Level 0で進まない
**症状**: 50イテレーション経ってもSuccess Rate < 30%

**原因**: 基本的な学習の問題
- 学習率が低すぎる
- Entropy係数が低すぎる（探索不足）

**対策**:
```bash
python scripts/rl-training/train_adaptive.py \
  --lr 5e-4 \
  --entropy-coef 0.05
```

### Level 1以降に進まない
**症状**: Success Rate 80%に到達しない

**対策**:
```bash
# 閾値を下げる
python scripts/rl-training/train_adaptive.py \
  --curriculum-success-threshold 0.7
```

### 特定のレベルで詰まる
**対策**: そのレベルのコースで個別に学習
```bash
python scripts/rl-training/train.py \
  --course courses/medium/narrow_oval.json \
  --total-iterations 500
```

## 関連ドキュメント

- [適応的学習システム全体](../doc/rl-training/ADAPTIVE_TRAINING.md)
- [curriculum/ディレクトリの詳細](curriculum/README.md)
- [カリキュラムマネージャー実装](../src/curriculum/curriculum_manager.py)

## 更新履歴

- **2025-12-13**: カリキュラム構成を整理
  - curriculum/ディレクトリをLevel 0-1専用に
  - Level 2以降は既存コース活用
  - 重複コースを削除
