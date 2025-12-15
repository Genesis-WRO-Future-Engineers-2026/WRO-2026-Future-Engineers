# カリキュラム学習用コース

このディレクトリには、カリキュラム学習で使用する**すべてのレベル（Level 0-5）**のコースが含まれています。

## 設計思想

### なぜすべてcurriculum/ディレクトリに？

**一貫性と管理のしやすさ**を重視した設計です。

#### メリット
1. ✅ **1箇所で完結**: すべてのカリキュラムコースが1ディレクトリに
2. ✅ **明確な分離**: カリキュラム学習用 vs その他のコース
3. ✅ **メンテナンス性**: 変更が1ディレクトリで完結
4. ✅ **わかりやすさ**: level0〜level5の連番で直感的

#### 以前の構成（複雑）
```
courses/curriculum/level0_straight.json
courses/curriculum/level1_simple_curve.json
courses/easy/simple_oval.json          # Level 2
courses/medium/narrow_oval.json        # Level 3
courses/hard/s_curve.json              # Level 4
courses/real/real-course_course.json   # Level 5
```
→ 複数ディレクトリに分散、管理が煩雑

#### 現在の構成（シンプル）
```
courses/curriculum/level0_straight.json
courses/curriculum/level1_simple_curve.json
courses/curriculum/level2_simple_oval.json
courses/curriculum/level3_narrow_oval.json
courses/curriculum/level4_s_curve.json
courses/curriculum/level5_real_course.json
```
→ 1ディレクトリで完結、管理が簡単

## コース一覧

### Level 0: 直線コース (level0_straight.json)
- **目的**: 壁回避と前進の基礎
- **構成**: 2本の平行な壁の間を直進
- **チェックポイント**: なし
- **難易度**: ★☆☆☆☆☆（最も簡単）
- **期待イテレーション**: 1-50

### Level 1: 単純カーブ (level1_simple_curve.json)
- **目的**: 基本的な操舵
- **構成**: L字型のコーナー1つ
- **チェックポイント**: 1個
- **難易度**: ★★☆☆☆☆（簡単）
- **期待イテレーション**: 50-150

### Level 2: 標準楕円 (level2_simple_oval.json)
- **目的**: 周回走行の基礎
- **構成**: 楕円形の周回コース
- **チェックポイント**: 4個
- **難易度**: ★★★☆☆☆（easy）
- **期待イテレーション**: 150-400
- **元ファイル**: `easy/simple_oval.json`

### Level 3: 狭い楕円 (level3_narrow_oval.json)
- **目的**: より正確な操舵
- **構成**: 狭い楕円形コース
- **チェックポイント**: 4個
- **難易度**: ★★★★☆☆（medium）
- **期待イテレーション**: 400-600
- **元ファイル**: `medium/narrow_oval.json`

### Level 4: S字カーブ (level4_s_curve.json)
- **目的**: 複雑な経路
- **構成**: S字カーブと障害物
- **チェックポイント**: 4個
- **難易度**: ★★★★★☆（hard）
- **期待イテレーション**: 600-800
- **元ファイル**: `hard/s_curve.json`

### Level 5: 実コース (level5_real_course.json)
- **目的**: 実機転移
- **構成**: 実際のレース場を模したコース
- **チェックポイント**: 5個
- **難易度**: ★★★★★★（最終目標）
- **期待イテレーション**: 800-2000
- **元ファイル**: `real/real-course_course.json`

## 使い方

### 自動カリキュラム学習（推奨）
```bash
# すべてのレベルを自動的に進める
./scripts/rl-training/run_adaptive_training.sh test   # テスト
./scripts/rl-training/run_adaptive_training.sh fast   # 本番
```

### 個別レベルのテスト
```bash
# Level 0のみ
python scripts/rl-training/train.py \
  --course courses/curriculum/level0_straight.json --gui

# Level 5（実コース）のみ
python scripts/rl-training/train.py \
  --course courses/curriculum/level5_real_course.json --gui
```

## レベルアップ条件

各レベルで以下の条件を満たすと、自動的に次のレベルへ：

- **Success Rate ≥ 80%**
- **最低50エピソード完了**

条件を満たさない場合は、現在のレベルで学習を継続します。

## ファイル命名規則

```
level{N}_{コース名}.json

N: レベル番号（0-5）
コース名: 内容を表す簡潔な名前
```

例：
- `level0_straight.json` - Level 0、直線コース
- `level5_real_course.json` - Level 5、実コース

## 新しいレベルの追加

中間レベルを追加したい場合：

1. **コースファイルを作成**
   ```bash
   # 例: Level 1.5を追加
   cp level1_simple_curve.json level1_5_wide_curve.json
   # 内容を編集
   ```

2. **train_adaptive.pyを更新**
   ```python
   curriculum_courses = [
       "courses/curriculum/level0_straight.json",
       "courses/curriculum/level1_simple_curve.json",
       "courses/curriculum/level1_5_wide_curve.json",  # 追加
       "courses/curriculum/level2_simple_oval.json",
       # ...
   ]
   ```

3. **ドキュメントを更新**
   - このREADME.md
   - `doc/rl-training/ADAPTIVE_TRAINING.md`

## 既存コースとの関係

### Level 2-5は既存コースのコピー

以下のコースは既存ディレクトリからコピーされたものです：

| カリキュラム | 元ファイル | 備考 |
|-------------|-----------|------|
| level2_simple_oval.json | easy/simple_oval.json | easy難易度 |
| level3_narrow_oval.json | medium/narrow_oval.json | medium難易度 |
| level4_s_curve.json | hard/s_curve.json | hard難易度 |
| level5_real_course.json | real/real-course_course.json | 実コース |

### コースの更新

元ファイルが更新された場合、curriculum/内のファイルも更新する必要があります：

```bash
# 例: 実コースが更新された場合
cp ../real/real-course_course.json level5_real_course.json
```

## トラブルシューティング

### Level 0で進まない
```bash
# 学習率とentropy係数を上げる
python scripts/rl-training/train_adaptive.py \
  --lr 5e-4 --entropy-coef 0.05
```

### 特定レベルで詰まる
```bash
# Success Rate閾値を下げる
python scripts/rl-training/train_adaptive.py \
  --curriculum-success-threshold 0.7
```

### コースが見つからない
```bash
# ファイルの存在確認
ls -lh courses/curriculum/level*.json
```

## 関連ドキュメント

- [適応的学習システム全体](../../doc/rl-training/ADAPTIVE_TRAINING.md)
- [カリキュラム全体の概要](../CURRICULUM_OVERVIEW.md)
- [カリキュラムマネージャー実装](../../src/curriculum/curriculum_manager.py)

## 更新履歴

- **2025-12-13**: すべてのレベルをcurriculum/ディレクトリに統一
  - Level 0-5まですべて1ディレクトリで管理
  - 既存コースからLevel 2-5をコピー
  - 管理の一貫性と簡潔性を向上
