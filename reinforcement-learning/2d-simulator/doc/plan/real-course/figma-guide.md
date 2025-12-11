# Figmaでコース作成する完全ガイド

## 🎨 Figmaとは？

- ブラウザで動作するデザインツール
- 無料プランで十分
- 直感的なペンツールで正確にトレース可能
- SVGエクスポート対応

**このプロジェクトでの使い方**: 実物写真を背景に配置してコースをトレース → SVGエクスポート → Pythonスクリプトで変換

---

## 🚀 セットアップ（5分）

### 1. Figmaアカウント作成

1. https://figma.com にアクセス
2. 「Get started for free」をクリック
3. メールアドレスで無料アカウント作成
4. ブラウザ版を使用（アプリ不要）

### 2. 新規ファイル作成

1. ログイン後、「+ New design file」をクリック
2. 左上の「Untitled」を「Minicar Course」に変更

### 3. フレーム作成

1. キーボードで **F** を押す（Frameツール）
2. 左サイドバーで「Desktop」→「Desktop」を選択
3. または、カスタムサイズ: **3000 x 2000 px**

**スケール設定**:
- 実コースが3m × 2mの場合
- 1m = 1000px
- 車両（17cm）= 170px

---

## 📸 Step 1: 実物写真の準備と配置（10分）

### 写真撮影のコツ

```
✅ 良い撮影:
  - できるだけ真上から（脚立使用）
  - コース全体が収まる
  - 明るい環境、均一な照明
  - 複数枚撮影して最良の1枚を選ぶ

❌ 避ける:
  - 斜めすぎる角度
  - 一部が切れている
  - 影が多い
  - ぼやけている
```

### Figmaに写真を配置

1. **写真をドラッグ＆ドロップ**
   - デスクトップから直接ドラッグ
   - または、メニュー → Place Image

2. **サイズ調整**
   - フレームいっぱいに拡大
   - 縦横比を維持（Shift+ドラッグ）

3. **レイヤーをロック**
   - 写真レイヤーを選択
   - 右クリック → Lock Layer
   - または Cmd/Ctrl + Shift + L

4. **不透明度を調整**（オプション）
   - 写真を選択
   - 右パネル → Fill → 不透明度を70-80%に
   - トレース線が見やすくなる

---

## ✏️ Step 2: ペンツールでトレース（30-60分）

### 基本操作

#### ペンツールの起動
- キーボードで **P** を押す
- または、左ツールバーの筆アイコン

#### 描画方法

**直線部分**:
1. クリックして頂点を追加
2. 次の頂点をクリック
3. 直線が引かれる

**カーブ部分**:
1. クリック後、**ドラッグ**
2. ベジェハンドルが表示される
3. ハンドルを調整してカーブを作成

**パスを閉じる**:
- 最後の頂点を**最初の頂点にクリック**
- 閉じたパスが完成

### トレースの手順

#### 1. 外周壁をトレース

```
1. ペンツール（P）を選択
2. コースの外周をクリックでトレース
   - 直線: クリック
   - カーブ: クリック+ドラッグ
3. 最初の点に戻って閉じる
4. レイヤー名を「outer_wall」に変更
```

**コツ**:
- 頂点数は20-50個程度
- 細かすぎなくてOK
- 後で調整可能

#### 2. 内周壁・障害物をトレース

```
1. 再度ペンツール（P）
2. 中央障害物や内側の壁をトレース
3. それぞれ閉じる
4. レイヤー名を「inner_wall_1」「obstacle_center」などに変更
```

#### 3. 複数のパスを作成

設計図の特徴に合わせて:
- 「分岐」セクションの壁
- 「抜け道」の入口・出口
- 中央の障害物

各パスは個別のレイヤーとして作成。

---

## 🎯 Step 3: レイヤーの整理（5分）

### レイヤー命名規則

右パネルのLayersで各パスをリネーム:

```
✅ 推奨命名:
  - outer_wall
  - inner_wall_1
  - inner_wall_2
  - obstacle_center
  - branch_wall_left
  - branch_wall_right

❌ 避ける命名:
  - Vector 123
  - Rectangle
  - Path (デフォルト名のまま)
```

**理由**: 名前がJSON変換時にそのまま使われます

### レイヤー構造の確認

```
📁 Frame 1 (または Minicar Course)
  🔒 course_photo.png (ロック)
  ✏️ outer_wall
  ✏️ inner_wall_1
  ✏️ inner_wall_2
  ✏️ obstacle_center
```

---

## 🔧 Step 4: 調整とブラッシュアップ（15分）

### グリッドを表示

1. View → Layout Grids
2. Grid を追加
3. サイズ: 100px（= 10cm）
4. 透明度: 20-30%

グリッドに合わせて頂点をスナップさせると正確。

### 頂点の微調整

**頂点を移動**:
1. ペンツールで描画したパスを選択
2. **A** キーで「Select all vertices」
3. または、直接頂点をクリック
4. ドラッグして移動

**頂点を追加**:
1. パスを選択
2. 線上の追加したい位置をクリック
3. 新しい頂点が追加される

**頂点を削除**:
1. 頂点を選択
2. **Delete** キー

**カーブを調整**:
1. 頂点を選択
2. ベジェハンドルをドラッグ

### 対称性のチェック

- ズームアウト（Cmd/Ctrl + -）
- 全体のバランスを確認
- 左右対称か、不自然な凹凸はないか

---

## 📤 Step 5: SVGエクスポート（2分）

### エクスポート手順

1. **全パスを選択**
   - Cmd/Ctrl + A（全選択）
   - または、Layersパネルで複数選択

2. **写真レイヤーを選択解除**
   - Cmd/Ctrl + クリックで写真を除外
   - パスのみ選択された状態に

3. **エクスポート設定**
   - 右下パネル → Export
   - または、選択した状態でメニュー → File → Export

4. **フォーマットを選択**
   - ドロップダウンから **SVG** を選択
   - 「Include "id" attribute」にチェック（重要！）

5. **エクスポート実行**
   - 「Export <選択したもの>」をクリック
   - ファイル名: `course_design.svg`
   - 保存先: `data/images/` または任意の場所

---

## 🐍 Step 6: Pythonスクリプトで変換（1分）

### 変換コマンド

```bash
cd /Users/akamite/Documents/ichis/minicar-battle/reinforcement-learning/2d-simulator

# 仮想環境をアクティブ化
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

# SVGをJSONに変換
python scripts/course-generation/svg_to_course.py \
  data/images/course_design.svg

# スケール調整が必要な場合
python scripts/course-generation/svg_to_course.py \
  data/images/course_design.svg \
  --scale 0.001
```

### 出力確認

```bash
# 生成されたファイルを確認
ls courses/real/course_design_course.json

# 内容を確認
cat courses/real/course_design_course.json
```

---

## ✅ Step 7: 検証とテスト（10分）

### GUIで可視化

```bash
python scripts/rl-training/train.py \
  --course courses/real/course_design_course.json \
  --gui \
  --total-iterations 1
```

### 確認ポイント

- [ ] コースの形状が実物と一致している
- [ ] 外周壁が正しく閉じている
- [ ] 内周壁・障害物の位置が正確
- [ ] 「分岐」「抜け道」が再現されている
- [ ] スケールが適切（車両サイズとのバランス）

### 問題があった場合

**形状が歪んでいる**:
→ Figmaに戻って頂点を調整 → 再エクスポート

**スケールが違う**:
→ `--scale` パラメータを調整（0.0005 〜 0.002）

**壁が欠けている**:
→ Figmaでレイヤーを確認、エクスポート時に選択漏れ

---

## 🎯 Step 8: チェックポイントとスタート/ゴールの設定（10分）

### JSONを手動編集

生成されたJSONファイルを開く:

```bash
code courses/real/course_design_course.json
# または任意のエディタ
```

### スタート/ゴール位置を設定

設計図の「START」位置に合わせて:

```json
{
  "start_position": [5.0, 10.0],
  "start_angle": 0.0,
  "goal_position": [5.0, 10.0],
  "goal_radius": 1.0
}
```

**角度の指定**:
- 0.0 = 右（0度）
- 1.57 = 上（90度 = π/2）
- 3.14 = 左（180度 = π）
- 4.71 = 下（270度 = 3π/2）

### チェックポイントを追加

コースを4分割して配置:

```json
{
  "checkpoints": [
    {
      "position": [15.0, 5.0],
      "radius": 1.5,
      "index": 0
    },
    {
      "position": [25.0, 10.0],
      "radius": 1.5,
      "index": 1
    },
    {
      "position": [15.0, 18.0],
      "radius": 1.2,
      "index": 2
    },
    {
      "position": [8.0, 10.0],
      "radius": 1.5,
      "index": 3
    }
  ]
}
```

### 再度GUIで確認

```bash
python scripts/rl-training/train.py \
  --course courses/real/course_design_course.json \
  --gui
```

チェックポイントの位置が適切か確認。

---

## 🚀 Step 9: 学習開始！

### テスト学習

```bash
# 短時間のテスト（100イテレーション）
python scripts/rl-training/train.py \
  --course courses/real/course_design_course.json \
  --total-iterations 100 \
  --gui
```

### 本格的な学習

```bash
# GUI無しで高速学習
python scripts/rl-training/train.py \
  --course courses/real/course_design_course.json \
  --total-iterations 2000
```

---

## 💡 Tips & Tricks

### Figmaのショートカット

| キー | 機能 |
|------|------|
| P | ペンツール |
| V | 選択ツール |
| A | 全頂点選択 |
| Cmd/Ctrl + D | 複製 |
| Cmd/Ctrl + G | グループ化 |
| Cmd/Ctrl + Shift + L | レイヤーロック |
| Cmd/Ctrl + E | エクスポート |
| Space + ドラッグ | 画面移動 |
| Cmd/Ctrl + マウスホイール | ズーム |

### ペンツールのコツ

**滑らかなカーブ**:
- クリック後、ドラッグの長さでカーブの大きさを調整
- ベジェハンドルは後から調整可能

**直線に戻す**:
- カーブの頂点を選択
- 右クリック → Flatten
- または、ハンドルを削除

**対称なハンドル**:
- 頂点を選択
- 右クリック → Mirror handles

### 精度を上げる

1. **ズームして作業**
   - カーブ部分は200-400%にズーム
   - 細かい調整がしやすい

2. **グリッドを活用**
   - View → Layout Grids
   - 100px or 50px グリッド
   - Snap to grid を有効化

3. **定規を表示**
   - Shift + R
   - 水平・垂直の基準線

### 複数バージョンを作成

1つのFigmaファイル内で複数のフレームを作成:

```
Frame 1: Easy版（トラック幅 1.5倍）
Frame 2: Medium版（実コース相当）
Frame 3: Hard版（トラック幅 0.8倍）
```

それぞれエクスポートして、Easy/Medium/Hardのコースを用意。

---

## 🔧 トラブルシューティング

### Q: SVGエクスポートでパスが出力されない

**A**:
- 写真レイヤーも選択されていませんか？ → 写真は選択解除
- パスが閉じていますか？ → 最初の点と最後の点を接続
- レイヤーが非表示になっていませんか？ → 目玉アイコンを確認

### Q: 変換後のスケールが合わない

**A**:
```bash
# スケールパラメータを調整
python scripts/course-generation/svg_to_course.py \
  course_design.svg \
  --scale 0.0005  # 小さくなりすぎた場合
# または
  --scale 0.002   # 大きくなりすぎた場合
```

### Q: 形状が歪んでいる

**A**:
- Figmaで写真の縦横比を確認
- エクスポート時の設定を確認（SVG、Include "id"）
- Figmaで再調整 → 再エクスポート

### Q: 壁の数が合わない

**A**:
- Layersパネルで全パスを確認
- エクスポート時に全て選択されているか確認
- グループ化されていないか確認（グループを解除）

---

## ✅ チェックリスト

### 準備
- [ ] Figmaアカウント作成
- [ ] 実物コースを撮影
- [ ] 写真をFigmaに配置

### トレース
- [ ] 外周壁をトレース
- [ ] 内周壁・障害物をトレース
- [ ] レイヤーに適切な名前を付ける
- [ ] 頂点数を最適化（20-50個）

### エクスポート
- [ ] 写真レイヤーを選択解除
- [ ] SVG形式でエクスポート
- [ ] "Include id" にチェック

### 変換
- [ ] svg_to_course.py を実行
- [ ] JSONファイルが生成された
- [ ] スタート/ゴール位置を編集
- [ ] チェックポイントを追加

### 検証
- [ ] GUIで可視化
- [ ] 形状が正確か確認
- [ ] スケールが適切か確認
- [ ] テスト学習で動作確認

### 学習
- [ ] 本格的な学習を開始

---

## 🎓 参考リソース

- **Figma公式チュートリアル**: https://help.figma.com/
- **ペンツール解説**: https://help.figma.com/hc/en-us/articles/360040450213-Pen-tool
- **SVGエクスポート**: https://help.figma.com/hc/en-us/articles/360040028114-Export-from-Figma

---

**所要時間の目安**:
- Figmaセットアップ: 5分
- 写真配置: 10分
- トレース: 30-60分
- エクスポート・変換: 5分
- チェックポイント設定: 10分
- 検証: 10分
- **合計: 約1.5-2時間**

頑張ってください！🚗💨
