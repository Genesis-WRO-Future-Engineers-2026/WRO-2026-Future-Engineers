# 実コース生成ガイド

## 📋 概要

実物のミニカーコースを2Dシミュレーターに実装するためのガイド。

**アプローチ**: AIで大まかに生成 →  GUIで手動調整 → 高精度なコース

## 🎯 コースの特徴

実コースの設計図より:
- **複雑な不規則形状**
- **分岐あり**: ショートカット vs 安全ルート
- **難度の高い抜け道**: 2箇所
- **ホームストレート**: 高速セクション
- **周回方向**: 反時計回り

## 🚀 クイックスタート

### 1. パッケージのインストール

```bash
source venv/bin/activate
pip install opencv-python numpy matplotlib pygame
```

### 2. 素材を準備

- **実物コースの写真**（iPhone 16で撮影）
- **抽象的な設計図**（提供済み）

### 3. AIで大まかに生成

#### 方法A: ChatGPT/Claude（推奨）

1. 写真と設計図をアップロード
2. プロンプト:
   ```
   この画像からミニカーコースの輪郭座標を抽出してJSON形式で出力してください。
   外周と内周を分けて、頂点数は20-40個程度に簡略化してください。
   完璧でなくてOKです。
   ```
3. 出力をコース定義JSONに変換

#### 方法B: OpenCV画像処理

```bash
python scripts/course-generation/extract_from_image.py \
  data/images/course_photo.png \
  --preview \
  --interactive
```

### 4. GUIで手動調整（重要！）

```bash
python scripts/course-generation/course_editor_gui.py \
  courses/real/generated_course.json
```

**操作**:
- 左クリック: 頂点を移動
- A: 頂点追加
- D: 頂点削除
- S: 保存
- Z/Y: Undo/Redo

### 5. 検証と学習

```bash
# GUIで確認
python scripts/rl-training/train.py \
  --course courses/real/final_course.json \
  --gui

# 学習開始
python scripts/rl-training/train.py \
  --course courses/real/final_course.json \
  --total-iterations 1000
```

## 📁 ドキュメント構成

- **`README.md`**: このファイル（クイックスタート）
- **`complete-workflow.md`**: 🔥 完全なワークフロー（詳細・推奨）
- **`image-extraction-guide.md`**: 画像処理の詳細ガイド

## 🎨 推奨ワークフロー

```
実物写真 + 設計図
     ↓
ChatGPT/Claude or OpenCV
     ↓
大まかなJSON（30分）
     ↓
GUIエディタで調整（1-2時間）
     ↓
最終JSON完成
     ↓
学習開始！
```

**所要時間**: 約3-4時間

## 💡 重要なポイント

### ✅ DO（推奨）

1. **AIを活用**: ChatGPT/Claudeで初期座標を生成
2. **GUIで微調整**: 完璧を目指さず80%の精度でOK
3. **段階的に**: 外周 → 内周 → 細部の順
4. **定期保存**: Sキーで頻繁に保存
5. **複数バージョン**: Easy/Medium/Hard を作成

### ❌ DON'T（避ける）

1. **完璧主義**: 最初から100%を目指さない
2. **手動入力**: 全座標を手打ちしない
3. **一発勝負**: 調整なしで学習開始しない

## 📊 作業の流れ

| ステップ | 方法 | 所要時間 | 精度 |
|----------|------|----------|------|
| 1. 素材準備 | 写真撮影 | 30分 | - |
| 2. AI生成 | ChatGPT | 15分 | 60% |
| 3. GUI調整 | 手動編集 | 1-2時間 | 95% |
| 4. 検証 | テスト | 30分 | 98% |
| 5. 最終調整 | 微調整 | 30分 | 99% |

## 🔧 ツール

### 1. `extract_from_image.py` - 画像処理

```bash
python scripts/course-generation/extract_from_image.py \
  data/images/course.png \
  --width 3.0 \
  --preview
```

### 2. `course_editor_gui.py` - GUIエディタ（重要！）

```bash
python scripts/course-generation/course_editor_gui.py \
  courses/real/course.json
```

**主な機能**:
- ドラッグ＆ドロップで頂点を移動
- 頂点の追加・削除
- リアルタイムプレビュー
- Undo/Redo
- グリッド表示

## 📸 撮影のコツ

### iPhone 16での撮影

```
✅ 良い撮影:
  - 脚立から真上を狙う
  - コース全体が入る
  - 明るい環境
  - 複数角度から

❌ 避ける:
  - 斜めすぎる
  - 一部が切れている
  - 逆光・影が多い
```

## 🤖 ChatGPT/Claude活用例

### プロンプト例

```
【依頼】
添付した2つの画像（実物写真 + 設計図）から、
ミニカーコースの輪郭座標をJSON形式で抽出してください。

【要件】
- 外周壁と内周壁を分ける
- 座標はメートル単位（コース幅: 約3m）
- 頂点数は20-40個に簡略化
- 完璧でなくてOK（後で手動調整）

【出力形式】
{
  "outer_wall": [[x1, y1], [x2, y2], ...],
  "inner_walls": [
    {"name": "obstacle1", "vertices": [[x1, y1], ...]}
  ]
}
```

### 出力の利用

AIの出力をコピーして、簡単なスクリプトでコース定義JSONに変換:

```python
# ai_output.json をコピー&ペースト
import json

ai_data = {...}  # ここにペースト

course = {
    "name": "Real Course",
    "walls": [
        {"type": "polygon", "name": "outer", "vertices": ai_data["outer_wall"]}
    ],
    "start_position": [3.0, 10.0],
    "goal_position": [3.0, 10.0],
    "checkpoints": []
}

for inner in ai_data.get("inner_walls", []):
    course["walls"].append({
        "type": "polygon",
        "name": inner["name"],
        "vertices": inner["vertices"]
    })

with open("courses/real/ai_course.json", "w") as f:
    json.dump(course, f, indent=2)
```

## ✅ チェックリスト

### Phase 1: 準備（30分）
- [ ] 実物コースを撮影（複数角度）
- [ ] 設計図を確認
- [ ] パッケージをインストール

### Phase 2: AI生成（15分）
- [ ] ChatGPT/Claudeに画像をアップロード
- [ ] 座標データを取得
- [ ] 初期JSONを作成

### Phase 3: GUI調整（1-2時間）
- [ ] course_editor_gui.py を起動
- [ ] 外周壁の形状を調整
- [ ] 内周壁・障害物を追加
- [ ] 「分岐」「抜け道」を再現
- [ ] 頂点数を最適化（20-50個）
- [ ] 定期的に保存（Sキー）

### Phase 4: 検証（30分）
- [ ] GUIで可視化
- [ ] スタート/ゴール位置を設定
- [ ] チェックポイントを追加
- [ ] テスト学習で動作確認

### Phase 5: 学習（継続）
- [ ] 短時間のテスト（100回）
- [ ] 本格的な学習（1000回以上）

## 🆘 トラブルシューティング

### Q: ChatGPTの出力座標がおかしい

**A**: スケールが違う可能性。JSONの全座標に係数を掛ける（例: 0.1倍）

### Q: GUIで頂点が選択できない

**A**: マウスホイールでズームして拡大

### Q: 形状が複雑すぎる

**A**: Dキーで不要な頂点を削除。直線は2-3頂点で十分。

### Q: どれくらい正確に作ればいい？

**A**: 80-90%の精度でOK。学習は近似的なコースでも機能する。

## 🎓 詳細ドキュメント

すべての詳細は `complete-workflow.md` を参照してください。

---

**始め方**: まず `complete-workflow.md` を読んで全体を把握してから作業開始！
