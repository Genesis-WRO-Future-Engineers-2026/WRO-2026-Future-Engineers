# 実コース生成ガイド - Figma版

## 📋 概要

実物のミニカーコースを**Figma**でトレースして2Dシミュレーターに実装します。

**方法**: 実物写真 → Figmaでトレース → SVGエクスポート → Python変換 → JSON完成

**所要時間**: 約1.5-2時間

---

## 🎯 コースの特徴

実コースの設計図より:
- **複雑な不規則形状**
- **分岐あり**: ショートカット vs 安全ルート
- **難度の高い抜け道**: 2箇所
- **ホームストレート**: 高速セクション
- **周回方向**: 反時計回り

---

## 🚀 クイックスタート（5ステップ）

### Step 1: 実物写真を撮影（30分）

```
✅ 良い撮影:
  - できるだけ真上から（脚立使用）
  - コース全体が入る
  - 明るい環境、照明均一
  - 複数枚撮影

❌ 避ける:
  - 斜めすぎる
  - 一部が切れている
  - 影が多い
```

### Step 2: Figmaでトレース（30-60分）

1. https://figma.com でアカウント作成（無料）
2. 新規ファイル作成
3. 3000×2000 pxのフレーム作成
4. 実物写真を背景に配置、レイヤーロック
5. ペンツール（P）で外周・内周をトレース
6. レイヤー名を設定（`outer_wall`, `inner_wall_1`, etc.）

### Step 3: SVGエクスポート（2分）

1. トレースしたパスを全選択（写真は除外）
2. File → Export → SVG
3. "Include id attribute" にチェック
4. `course_design.svg` として保存

### Step 4: Python変換（1分）

```bash
cd /Users/akamite/Documents/ichis/minicar-battle/reinforcement-learning/2d-simulator
source venv/bin/activate

python scripts/course-generation/svg_to_course.py \
  data/images/course_design.svg
```

出力: `courses/real/course_design_course.json`

### Step 5: 検証と学習（10分）

```bash
# GUIで確認
python scripts/rl-training/train.py \
  --course courses/real/course_design_course.json \
  --gui

# 学習開始
python scripts/rl-training/train.py \
  --course courses/real/course_design_course.json \
  --total-iterations 1000
```

---

## 📁 ドキュメント構成

- **`README.md`**: このファイル（クイックスタート）
- **`figma-guide.md`**: 🔥 Figma完全ガイド（詳細手順・推奨）

---

## 🎨 ワークフロー図

```
実物コース
    ↓ (iPhone 16で撮影)
写真
    ↓ (Figmaに配置)
ペンツールでトレース
    ↓ (30-60分)
SVGエクスポート
    ↓ (1分)
svg_to_course.py
    ↓ (1分)
courses/real/*.json
    ↓
学習開始！
```

**合計時間**: 約1.5-2時間

---

## 💡 Figmaを使う理由

| 項目 | Figma | 手動JSON作成 | OpenCV |
|------|-------|-------------|--------|
| 難易度 | ★☆☆ | ★★★ | ★★☆ |
| 精度 | ★★★★★ | ★★★ | ★★★☆ |
| 所要時間 | 1.5-2時間 | 5-8時間 | 3-4時間 |
| 直感性 | ★★★★★ | ★☆☆ | ★★☆ |
| 無料 | ✅ | ✅ | ✅ |

**結論**: Figmaが最も効率的で正確！

---

## 🔧 必要なもの

### ソフトウェア
- ブラウザ（Figma用）
- Python 3.x（インストール済み）

### ハードウェア
- iPhone 16または任意のカメラ（実物撮影用）
- Mac/PC

### アカウント
- Figmaアカウント（無料）

---

## ✅ Figma作業のポイント

### 1. 写真配置
- フレーム: 3000×2000 px（実コース3m×2m = 1m=1000px）
- 写真をロック（誤操作防止）
- 不透明度70-80%（トレース線が見やすい）

### 2. トレース
- ペンツール（P）を使用
- 直線: クリック
- カーブ: クリック+ドラッグ
- 頂点数: 20-50個程度

### 3. レイヤー命名
```
✅ 推奨:
  - outer_wall
  - inner_wall_1
  - obstacle_center

❌ 避ける:
  - Vector 123
  - Rectangle (デフォルト名)
```

### 4. エクスポート設定
- 形式: **SVG**
- "Include id attribute": **チェック必須**
- 写真レイヤーは選択しない

---

## 🎯 チェックポイントの追加

生成されたJSONを手動編集:

```json
{
  "start_position": [5.0, 10.0],
  "start_angle": 0.0,
  "goal_position": [5.0, 10.0],
  "goal_radius": 1.0,
  "checkpoints": [
    {"position": [15.0, 5.0], "radius": 1.5, "index": 0},
    {"position": [25.0, 10.0], "radius": 1.5, "index": 1},
    {"position": [15.0, 18.0], "radius": 1.2, "index": 2},
    {"position": [8.0, 10.0], "radius": 1.5, "index": 3}
  ]
}
```

---

## 🔧 トラブルシューティング

### Q: SVGエクスポートでパスが含まれない
**A**: 写真レイヤーも選択されていませんか？写真は選択解除してください。

### Q: スケールが合わない
**A**: `--scale` パラメータを調整:
```bash
python scripts/course-generation/svg_to_course.py \
  course.svg \
  --scale 0.0005  # 小さい場合
# または
  --scale 0.002   # 大きい場合
```

### Q: 形状が歪んでいる
**A**: Figmaに戻って頂点を調整 → 再エクスポート → 再変換

### Q: 壁が足りない
**A**: Figmaのレイヤーパネルで全パスを確認。エクスポート時に全て選択されているか確認。

---

## 📊 作業時間の内訳

| タスク | 所要時間 | 難易度 |
|--------|---------|-------|
| Figmaセットアップ | 5分 | ★☆☆ |
| 写真撮影 | 30分 | ★☆☆ |
| 写真配置 | 10分 | ★☆☆ |
| トレース | 30-60分 | ★★☆ |
| エクスポート | 2分 | ★☆☆ |
| Python変換 | 1分 | ★☆☆ |
| チェックポイント設定 | 10分 | ★☆☆ |
| 検証 | 10分 | ★☆☆ |
| **合計** | **1.5-2時間** | **★★☆** |

---

## 🎓 次のステップ

### 今すぐできること

1. **Figmaアカウント作成**
   - https://figma.com
   - 無料プラン

2. **実物コースを撮影**
   - iPhone 16またはカメラ
   - できるだけ真上から

3. **詳細ガイドを読む**
   - `figma-guide.md` を開く
   - ステップバイステップで作業

### 完成後

1. **複数の難易度を作成**
   - Easy版（トラック幅1.5倍）
   - Medium版（実コース相当）
   - Hard版（トラック幅0.8倍）

2. **カリキュラム学習に統合**
   - `src/curriculum/curriculum_manager.py` を編集

3. **本格的な学習を開始**

---

## 🆘 サポート

### 詳細ガイド
すべての詳細手順は **`figma-guide.md`** に記載されています。

### よくある質問

**Q: Figmaは無料で使えますか？**
A: はい、無料プランで十分です。

**Q: Figmaアプリのインストールは必要？**
A: いいえ、ブラウザ版で完結します。

**Q: ペンツールが難しい...**
A: `figma-guide.md`のTips & Tricksセクションを参照してください。

**Q: どれくらい正確に作ればいい？**
A: 80-90%の精度でOK。学習は近似的なコースでも機能します。

---

**始め方**: まず実物コースを撮影 → `figma-guide.md` を読みながらFigmaで作業開始！

頑張ってください 🚗💨
