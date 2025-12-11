# 設計図画像からコース生成する方法（LiDARなし）

## 📋 概要

iPhone ProのLiDARが使えない場合の代替方法です。設計図の画像をOpenCVで処理してコースJSONを生成します。

## 🎯 この方法のメリット/デメリット

### ✅ メリット
- iPhone Proは不要（通常のカメラでOK）
- 設計図PDFがあれば今すぐ実行可能
- 完全無料

### ⚠️ デメリット
- 画像の品質に依存（白黒がはっきりしている必要がある）
- 手動調整が必要な場合がある
- 3Dスキャンより精度は若干劣る

## 📸 必要なもの

1. **設計図の画像ファイル**
   - PNG, JPG, PDF（PDFは画像に変換）
   - できるだけ高解像度
   - コントラストがはっきりしていること

2. **Python環境**
   - OpenCV
   - NumPy
   - Matplotlib

## 🛠️ セットアップ

### パッケージのインストール

```bash
cd /Users/akamite/Documents/ichis/minicar-battle/reinforcement-learning/2d-simulator
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

# OpenCVと必要なパッケージをインストール
pip install opencv-python numpy matplotlib
```

### インストール確認

```bash
python -c "import cv2, numpy, matplotlib; print('✓ 全パッケージ正常にインストールされました')"
```

## 📷 画像の準備

### 方法1: 設計図PDFをスクリーンショット

```
1. 設計図PDFを開く
2. コース部分を画面いっぱいに表示
3. スクリーンショット撮影（Mac: Cmd+Shift+4）
4. data/images/course_design.png として保存
```

### 方法2: 実物のコースを真上から撮影（iPhone 16で可能）

```
1. できるだけ高い位置から撮影
   - 脚立を使う
   - 2階から撮影
   - 手を伸ばして真上から
2. コース全体が入るように
3. 照明を均一に（影を減らす）
4. 複数枚撮影して一番良いものを選ぶ
```

### 画像品質のポイント

✅ **良い画像**:
- コース（グレー）と背景（白）のコントラストがはっきり
- 全体が均一な明るさ
- ピントが合っている
- 歪みが少ない

❌ **悪い画像**:
- コントラストが低い
- 影が多い
- ぼやけている
- 斜めから撮影（遠近感がある）

## 🚀 使用方法

### 基本的な使い方

```bash
# 設計図画像からコースを生成
python scripts/course-generation/extract_from_image.py data/images/course_design.png

# 実物の幅を指定（例: 3.5m）
python scripts/course-generation/extract_from_image.py data/images/course_design.png \
  --width 3.5

# 出力先を指定
python scripts/course-generation/extract_from_image.py data/images/course_design.png \
  --output courses/real/my_course.json
```

### プレビュー表示付きで実行（推奨）

```bash
# プレビューを見ながら調整
python scripts/course-generation/extract_from_image.py data/images/course_design.png \
  --preview

# 対話的に輪郭を選択
python scripts/course-generation/extract_from_image.py data/images/course_design.png \
  --preview \
  --interactive
```

### パラメータ調整

画像によって最適なパラメータが異なります：

```bash
# 二値化の閾値を調整（0-255）
python scripts/course-generation/extract_from_image.py data/images/course_design.png \
  --threshold 150

# 検出する最小面積を調整（小さいノイズを除去）
python scripts/course-generation/extract_from_image.py data/images/course_design.png \
  --min-area 10000

# 輪郭の簡略化レベルを調整（小さいほど詳細）
python scripts/course-generation/extract_from_image.py data/images/course_design.png \
  --simplify 0.002
```

## 🎛️ パラメータガイド

| パラメータ | 説明 | デフォルト | 調整方法 |
|-----------|------|-----------|---------|
| `--threshold` | 二値化の閾値 | 127 | 輪郭が検出されない→小さく<br>ノイズが多い→大きく |
| `--min-area` | 最小面積 | 5000 | 小さいノイズが多い→大きく |
| `--simplify` | 簡略化係数 | 0.005 | 頂点が多すぎる→大きく<br>形状が粗い→小さく |
| `--width` | 実物の幅(m) | 3.0 | 実測値を指定 |
| `--scale` | シミュレーターのスケール | 10.0 | 通常変更不要 |

## 📊 ワークフロー

```
設計図画像/実物写真
    ↓
[OpenCVで輪郭抽出]
    ↓
[簡略化・スケール変換]
    ↓
courses/real/*.json
    ↓
[GUIで可視化]
    ↓
[手動調整（必要なら）]
    ↓
[学習開始！]
```

## 🔍 トラブルシューティング

### 問題: 輪郭が検出されない

**症状**: "輪郭が検出できませんでした" エラー

**解決策**:
```bash
# 閾値を調整（明るい画像は値を上げる）
python scripts/course-generation/extract_from_image.py data/images/course_design.png \
  --threshold 100 \
  --preview

# 最小面積を小さくする
python scripts/course-generation/extract_from_image.py data/images/course_design.png \
  --min-area 1000 \
  --preview
```

### 問題: 外周と内周が逆に検出される

**症状**: 生成されたコースで内外が反転

**解決策**:
```bash
# 対話的モードで手動選択
python scripts/course-generation/extract_from_image.py data/images/course_design.png \
  --interactive
```

### 問題: ノイズが多すぎる

**症状**: 小さな輪郭がたくさん検出される

**解決策**:
```bash
# 閾値を調整 + 最小面積を大きく
python scripts/course-generation/extract_from_image.py data/images/course_design.png \
  --threshold 150 \
  --min-area 20000
```

### 問題: 輪郭が複雑すぎる（頂点が多い）

**症状**: 生成されたJSONの頂点数が数百個

**解決策**:
```bash
# 簡略化係数を大きく
python scripts/course-generation/extract_from_image.py data/images/course_design.png \
  --simplify 0.01
```

### 問題: 画像が斜めで歪んでいる

**症状**: 生成されたコースが歪んでいる

**解決策**:
1. 画像を回転・トリミング（Photoshop, GIMPなど）
2. または、真上から再撮影

## 💡 Tips

### Tip 1: 画像の前処理

画像編集ソフトで前処理すると精度が上がります：

```
1. トリミング（コース部分のみ）
2. コントラスト調整
3. 明るさ調整
4. 回転補正
```

macOSの「プレビュー」アプリでも可能です。

### Tip 2: 複数の閾値を試す

```bash
# for文で複数の閾値を試す
for t in 100 120 140 160; do
  python scripts/course-generation/extract_from_image.py \
    data/images/course_design.png \
    --threshold $t \
    --output courses/real/course_t${t}.json
done
```

### Tip 3: ChatGPTで画像の前処理

ChatGPTに画像をアップロードして：
```
「この設計図画像から、コース部分だけを白黒画像で抽出してください。
コース（走行可能エリア）を黒、背景を白にしてください。」
```

## 📝 生成後の手動調整

生成されたJSONは完璧ではないため、手動調整が必要な場合があります：

### 1. GUIで確認

```bash
python scripts/rl-training/train.py \
  --course courses/real/course_design_course.json \
  --gui \
  --total-iterations 1
```

### 2. チェックポイントを追加

JSONを編集：

```json
{
  "checkpoints": [
    {
      "position": [15.0, 5.0],
      "radius": 1.5,
      "index": 0
    },
    {
      "position": [25.0, 15.0],
      "radius": 1.5,
      "index": 1
    }
  ]
}
```

### 3. スタート位置を調整

```json
{
  "start_position": [3.0, 10.0],  // 適切な位置に調整
  "start_angle": 0.0,             // 進行方向（ラジアン）
  "goal_position": [3.0, 10.0],
  "goal_radius": 1.0
}
```

## 🎨 代替案: 手動でトレース

画像処理がうまくいかない場合、完全手動も可能です：

### 方法1: Webツール

1. https://www.image-map.net/ などのツールを使用
2. 画像をアップロードして輪郭をクリック
3. 座標をコピー

### 方法2: GIMPでパス作成

1. GIMPで設計図を開く
2. パスツールで輪郭をトレース
3. パスをSVGエクスポート
4. SVGをパース（別途スクリプトが必要）

## 📋 チェックリスト

### 画像準備
- [ ] 高解像度の画像を用意（推奨: 1920x1080以上）
- [ ] コントラストがはっきりしている
- [ ] 全体が入っている
- [ ] 歪みがない

### スクリプト実行
- [ ] OpenCVをインストール
- [ ] --preview で結果を確認
- [ ] パラメータ調整（必要に応じて）
- [ ] JSONファイルが生成された

### 検証
- [ ] GUIで可視化して確認
- [ ] 形状が実物/設計図と一致
- [ ] スケールが適切
- [ ] チェックポイントを追加

---

**次のステップ**: 生成したコースで学習を開始しましょう！
