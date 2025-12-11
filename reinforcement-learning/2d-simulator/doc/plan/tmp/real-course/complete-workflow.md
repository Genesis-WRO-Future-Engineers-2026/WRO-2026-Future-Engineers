# 実コース生成の完全ワークフロー

## 🎯 目標

実物の写真 + 抽象的な設計図 → **AIで大まかに生成** → **GUIで手動調整** → 高精度なコースJSON

## 📸 Step 1: 素材の準備

### 必要なもの

1. **実物コースの写真**（iPhone 16で撮影可能）
   - できるだけ真上から
   - 複数角度から撮影
   - 照明を均一に

2. **抽象的な設計図**（提供されている画像）
   - コースの大まかな形状
   - 「分岐」「抜け道」などの特徴

### 撮影のコツ

```
✅ 良い撮影方法:
  - 脚立や高い場所から撮影
  - コース全体が入るように
  - 複数枚撮影（異なる角度）
  - 明るい環境で

❌ 避けるべき:
  - 斜めすぎる角度
  - 一部が切れている
  - 逆光・影が多い
```

## 🤖 Step 2: AIで大まかなコースを生成

### 方法A: OpenCV画像処理（基本）

```bash
# 実物写真から輪郭を抽出
python scripts/course-generation/extract_from_image.py \
  data/images/course_photo.png \
  --width 3.0 \
  --preview \
  --interactive

# パラメータ調整例
python scripts/course-generation/extract_from_image.py \
  data/images/course_photo.png \
  --threshold 140 \
  --min-area 10000 \
  --simplify 0.01 \
  --preview
```

**出力**: `courses/real/course_photo_course.json`（大まかな輪郭）

### 方法B: ChatGPT/Claude活用（推奨）

#### 手順1: 画像をアップロード

ChatGPT/Claudeに以下の2つの画像をアップロード:
1. 実物コースの写真
2. 抽象的な設計図

#### 手順2: プロンプト

```
以下の画像からミニカーコースの輪郭座標を抽出してください。

【要件】
1. 外周壁と内周壁を分けて抽出
2. 座標はJSON形式で出力
3. 単位はメートル（実コースの幅は約3m）
4. 以下のフォーマットに従う:

{
  "outer_wall": [
    [x1, y1],
    [x2, y2],
    ...
  ],
  "inner_walls": [
    {
      "name": "central_obstacle",
      "vertices": [[x1, y1], [x2, y2], ...]
    }
  ]
}

【注意点】
- 完璧でなくてOK（後で手動調整します）
- 頂点数は20-40個程度に簡略化
- 「分岐」「抜け道」の形状を大まかに再現
```

#### 手順3: AIの出力を変換

AIが出力したJSONを基に、コース定義JSONを作成:

```python
# scripts/course-generation/ai_output_to_course.py
import json

# AIの出力をコピー
ai_output = {
    "outer_wall": [...],
    "inner_walls": [...]
}

# コース定義に変換
course = {
    "name": "Real Course - AI Generated",
    "description": "ChatGPT/Claudeで生成した初期コース",
    "difficulty": "medium",
    "start_position": [3.0, 10.0],  # TODO: 調整
    "start_angle": 0.0,
    "goal_position": [3.0, 10.0],   # TODO: 調整
    "goal_radius": 1.0,
    "walls": [
        {
            "type": "polygon",
            "name": "outer_wall",
            "vertices": ai_output["outer_wall"]
        }
    ],
    "checkpoints": []  # TODO: 後で追加
}

# 内周を追加
for inner in ai_output.get("inner_walls", []):
    course["walls"].append({
        "type": "polygon",
        "name": inner["name"],
        "vertices": inner["vertices"]
    })

# 保存
with open("courses/real/ai_generated_course.json", "w") as f:
    json.dump(course, f, indent=2)

print("✓ courses/real/ai_generated_course.json を生成しました")
```

## 🎨 Step 3: GUIで手動調整（重要！）

AIで生成したコースは大まかなので、ここで精度を上げます。

### GUIエディタの起動

```bash
# 必要なパッケージをインストール
pip install pygame

# GUIエディタを起動
python scripts/course-generation/course_editor_gui.py \
  courses/real/ai_generated_course.json
```

### GUIでの編集操作

#### 基本操作
```
左クリック + ドラッグ: 頂点を移動
右クリック: 壁を選択
A: 頂点追加モード（クリックで追加）
D: 頂点削除モード（クリックで削除）
S: 保存
Z: Undo
Y: Redo
G: グリッド表示切り替え
←/→: 壁を切り替え
マウスホイール: ズーム
ESC: 編集モードに戻る
```

#### 調整のポイント

1. **外周壁の修正**
   - 写真と見比べながら形状を調整
   - カーブを滑らかに
   - 直線部分を直線に

2. **内周壁の修正**
   - 「分岐」部分を正確に
   - 「抜け道」の幅を調整
   - 中央障害物の形状

3. **頂点の最適化**
   - 不要な頂点を削除（D キー）
   - 足りない部分に追加（A キー）
   - 20-50頂点程度に収める

4. **スタート/ゴール位置**
   - JSONを直接編集して配置
   - 設計図の「周回方向」に従う

### 実物との照らし合わせ

編集中は以下を参照:
- 実物コースの写真（複数角度）
- 抽象的な設計図
- 実測値（メジャーで測定した幅など）

### 保存とバックアップ

```bash
# 定期的に保存（Sキー）
# バックアップを作成
cp courses/real/ai_generated_course.json \
   courses/real/ai_generated_course_backup_$(date +%Y%m%d_%H%M%S).json
```

## ✅ Step 4: 検証とテスト

### GUIで可視化

```bash
python scripts/rl-training/train.py \
  --course courses/real/ai_generated_course.json \
  --gui \
  --total-iterations 1
```

確認ポイント:
- [ ] 外周の形状が実物と一致
- [ ] 内周（障害物）の配置が正確
- [ ] 「分岐」「抜け道」が再現されている
- [ ] スケールが適切（車両が小さすぎない/大きすぎない）

### チェックポイントの追加

JSONを編集:

```json
{
  "checkpoints": [
    {
      "position": [10.0, 5.0],
      "radius": 1.5,
      "index": 0,
      "description": "分岐前"
    },
    {
      "position": [15.0, 15.0],
      "radius": 1.2,
      "index": 1,
      "description": "抜け道"
    },
    {
      "position": [25.0, 10.0],
      "radius": 1.5,
      "index": 2,
      "description": "ホームストレート"
    }
  ]
}
```

### スタート/ゴール位置の調整

設計図の「周回方向」（反時計回り）と「ゴール旗」の位置に従う:

```json
{
  "start_position": [12.0, 8.0],
  "start_angle": 1.57,  // ラジアン（90度 = π/2）
  "goal_position": [12.0, 8.0],
  "goal_radius": 1.0
}
```

## 🚀 Step 5: 学習開始

### テスト学習

```bash
# 短時間のテスト（100イテレーション）
python scripts/rl-training/train.py \
  --course courses/real/ai_generated_course.json \
  --total-iterations 100 \
  --gui
```

確認:
- [ ] 車両が壁に正しく衝突
- [ ] チェックポイントが正しく検知
- [ ] ゴールに到達可能
- [ ] 報酬が妥当な範囲

### 本格的な学習

```bash
# GUI無しで高速学習
python scripts/rl-training/train.py \
  --course courses/real/ai_generated_course.json \
  --total-iterations 2000

# カリキュラム学習
python scripts/rl-training/train_curriculum.py
```

## 📊 ワークフロー図

```
実物写真 + 抽象的設計図
         ↓
    [OpenCV or AI]
         ↓
  大まかなJSON生成
         ↓
   [GUIエディタ]
    ↓        ↓
  調整     確認・微調整
    ↓        ↓
  保存 ← 満足いくまで繰り返し
         ↓
   最終JSON完成
         ↓
     学習開始！
```

## 💡 Tips

### Tip 1: 段階的な調整

```
1. 最初は大まかな形状を合わせる（外周のみ）
2. 次に内周・障害物を追加
3. 最後に細部を調整（頂点の位置）
```

### Tip 2: 複数バージョンを作成

```bash
# Easy版（トラック幅を広げる）
cp courses/real/final_course.json courses/real/final_course_easy.json
# → GUIで編集して幅を1.5倍に

# Medium版（実コース相当）
# → そのまま使用

# Hard版（トラック幅を狭める）
cp courses/real/final_course.json courses/real/final_course_hard.json
# → GUIで編集して幅を0.8倍に
```

### Tip 3: 実測値を活用

コースの主要部分をメジャーで測定:
- ホームストレートの長さ
- カーブの半径
- 「抜け道」の幅

これらの実測値をGUI編集時の参考に。

### Tip 4: ChatGPT/Claudeの活用法

**初回生成時**:
- 「完璧でなくてOK、大まかな形状でOK」と伝える
- 頂点数は20-40個程度に簡略化してもらう

**修正時**:
- 実物写真の特定部分を切り出してアップロード
- 「この部分の形状を修正してください」と依頼

## 🔧 トラブルシューティング

### 問題: AIの出力座標がおかしい

**解決策**:
1. プロンプトを調整（「3m × 2mのコース」と明示）
2. 出力されたJSON単位を確認（ピクセル→メートル変換が必要かも）
3. GUIで全体をスケール調整

### 問題: GUIで頂点が選択できない

**解決策**:
- ズームして拡大（マウスホイール）
- グリッド表示をオン（Gキー）

### 問題: 形状が複雑すぎる

**解決策**:
- 頂点削除モード（Dキー）で不要な頂点を削除
- 直線部分は2-3頂点で十分

### 問題: スケールが合わない

**解決策**:
- JSONの全座標に係数を掛ける（例: 1.2倍）
- または、GUIで一から描き直し

## 📝 チェックリスト

### 素材準備
- [ ] 実物コースを複数角度から撮影
- [ ] 抽象的な設計図を確認
- [ ] 主要部分を実測（オプション）

### AI生成
- [ ] ChatGPT/Claudeで大まかな座標を取得
- [ ] または、OpenCVで輪郭抽出
- [ ] 初期JSONファイルを作成

### GUI調整
- [ ] 外周壁の形状を調整
- [ ] 内周壁・障害物を追加/調整
- [ ] 「分岐」「抜け道」を正確に再現
- [ ] 頂点数を最適化（20-50個）
- [ ] 定期的に保存

### 検証
- [ ] GUIで可視化して確認
- [ ] チェックポイントを追加
- [ ] スタート/ゴール位置を設定
- [ ] テスト学習で動作確認

### 学習
- [ ] 短時間のテスト学習
- [ ] 報酬・ゴール到達を確認
- [ ] 本格的な学習を開始

---

**所要時間の目安**:
- 素材準備: 30分
- AI生成: 15分
- GUI調整: 1-2時間
- 検証・学習: 1時間
- **合計: 3-4時間**

完璧を目指さず、「80%の精度で早く完成させる」を目標に！
