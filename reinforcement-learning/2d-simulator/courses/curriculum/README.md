# カリキュラム学習用コース

このディレクトリには、適応的学習システムで使用する**すべてのレベル（Level 0-5）**のコースが含まれています。

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
│   └── README.md (このファイル)
│
├── real/                    # 実コースのオリジナルと派生（参考用）
│   ├── real-course_course.json
│   └── variations/          # 実コースのバリエーション
```

### 設計思想

**すべてのカリキュラムコースを1ディレクトリに統一**することで、一貫性と管理のしやすさを実現:

- ✅ **1箇所で完結**: すべてのカリキュラムコースが1ディレクトリに
- ✅ **明確な分離**: カリキュラム学習用 vs その他のコース
- ✅ **メンテナンス性**: 変更が1ディレクトリで完結
- ✅ **わかりやすさ**: level0〜level5の連番で直感的

**注**: easy/medium/hard/ディレクトリは削除されました（curriculum/に統合済み）

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

## Level 2-5について

以下のコースは既存ディレクトリからコピーされたものです（元のeasy/medium/hard/は削除済み）：

| カリキュラム | 元ファイル | 備考 |
|-------------|-----------|------|
| level2_simple_oval.json | easy/simple_oval.json（削除済み） | easy難易度 |
| level3_narrow_oval.json | medium/narrow_oval.json（削除済み） | medium難易度 |
| level4_s_curve.json | hard/s_curve.json（削除済み） | hard難易度 |
| level5_real_course.json | real/real-course_course.json | 実コース（参考用に保持） |

**実コースの更新**: courses/real/が更新された場合は、`cp ../real/real-course_course.json level5_real_course.json`でコピー

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

## 学習の期待時間

- **Level 0**: 5-10分（50イテレーション）
- **Level 1**: 10-20分（100イテレーション）
- **Level 2**: 30-60分（250イテレーション）
- **Level 3**: 30-60分（200イテレーション）
- **Level 4**: 30-60分（200イテレーション）
- **Level 5**: 2-4時間（1200イテレーション）

**合計**: 約4-6時間で全レベル完了（M4チップ、GUIなし）

## 関連ドキュメント

- [適応的学習システム（メインドキュメント）](../../doc/ADAPTIVE_TRAINING.md)
- [報酬設計](../../doc/REWARD_DESIGN.md)
- [カリキュラムマネージャー実装](../../src/curriculum/curriculum_manager.py)
- [適応的報酬スケーラー実装](../../src/rl/adaptive_reward.py)

## 更新履歴

- **2025-12-15**: ドキュメント統合・整理
  - courses/CURRICULUM_OVERVIEW.mdの内容を統合
  - 関連ドキュメントのパスを更新
- **2025-12-13**: すべてのレベルをcurriculum/ディレクトリに統一
  - Level 0-5まですべて1ディレクトリで管理
  - 既存コースからLevel 2-5をコピー
  - 管理の一貫性と簡潔性を向上
