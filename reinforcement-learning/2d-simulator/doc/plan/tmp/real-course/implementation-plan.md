# 実際のコースの2Dシミュレーター実装計画

## 1. コース概要分析

### 画像から読み取れるコース特徴

- **コース形状**: 楕円形のオーバルトラック（外周）+ 中央に障害物エリア
- **スタート/ゴール**: 画像左上の「START」地点
- **主要セクション**:
  1. 長い直線セクション（左側）
  2. カーブセクション（上部）
  3. 短い直線セクション（右側）
  4. カーブセクション（下部）
- **中央障害物**: 円形または楕円形の障害物が中央に配置
- **チェックポイント**: 4箇所程度（90度ごと）を想定

### 実寸法（実測値）

画像と実測から確定した情報:
- コースは約3m × 2m程度の楕円形
- **トラック幅（可変）**:
  - スタート位置（左側直線部）: **1.6m**（太い）
  - 上部カーブセクション: **0.6m**（狭い）
  - 下部カーブセクション: 約0.6m（推定）
  - 右側直線部: 約0.8-1.0m（推定）
- 中央障害物の直径: 約80cm-1m

**重要**: トラック幅が場所によって異なる可変幅コース

## 2. スケール変換計画

### 座標系の定義

```
実世界座標系 → シミュレーター座標系
実寸: 3m × 2m → シミュレーター: 30 × 20単位（1単位 = 0.1m = 10cm）
```

**スケーリング理由**:
- シミュレーター内の車両サイズ（約0.4単位）に対して適切なコースサイズ
- LiDARの検知範囲（最大5単位）に適合
- 既存のコース定義と一貫性を保つ

### 主要寸法の変換表

| 要素 | 実寸法 | シミュレーター単位 | 備考 |
|------|--------|-------------------|------|
| コース全体幅 | 3.0m | 30単位 | |
| コース全体高さ | 2.0m | 20単位 | |
| **トラック幅（スタート位置）** | **1.6m** | **16単位** | 最も広い |
| **トラック幅（上部カーブ）** | **0.6m** | **6単位** | 最も狭い |
| トラック幅（下部カーブ）推定 | 0.6m | 6単位 | 上部と同様 |
| トラック幅（右側直線）推定 | 0.8-1.0m | 8-10単位 | 中間的な幅 |
| 中央障害物直径 | 0.8m | 8単位 | |
| 車両サイズ（全長） | 0.17m | 1.7単位 | TT-02実寸 |
| 車両サイズ（全幅） | 0.19m | 1.9単位 | TT-02実寸 |

**重要な考慮点**:
- 車両幅1.9単位に対して、最狭部が6単位しかない
- 安全マージンは両側で約2単位ずつ（非常にタイト！）
- これは実機の難易度を正確に反映している

## 3. コースレイアウト設計（可変幅トラック）

### 設計アプローチ

可変幅トラックを実装するため、コースを4つのセクションに分割:

1. **左側直線（スタート/ゴール）**: 幅16単位
2. **上部カーブ**: 幅6単位（最狭）
3. **右側直線**: 幅8-10単位
4. **下部カーブ**: 幅6単位

各セクションは個別のポリゴンで定義し、滑らかに接続する。

### 3.1 外周壁の定義

外周は楕円形を基本として、セクションごとに調整:

```python
# 外周楕円: 中心(15, 10), 半長軸a=14, 半短軸b=9
# 32個の頂点で滑らかな楕円を近似
def generate_outer_wall():
    vertices = []
    for i in range(32):
        theta = 2 * math.pi * i / 32
        x = 15 + 14 * math.cos(theta)
        y = 10 + 9 * math.sin(theta)
        vertices.append([round(x, 2), round(y, 2)])
    return vertices
```

座標範囲:
- X: 1.0 〜 29.0（幅28単位）
- Y: 1.0 〜 19.0（高さ18単位）

### 3.2 内周壁の定義（可変幅対応）

内周は**セクションごとに異なる距離**で定義:

```python
def generate_inner_wall():
    """可変幅トラックの内周を生成"""
    vertices = []

    for i in range(32):
        theta = 2 * math.pi * i / 32

        # 角度に応じてトラック幅を変化させる
        # theta = 0: 右側 (3時方向)
        # theta = π/2: 上側 (12時方向) - 最狭部
        # theta = π: 左側 (9時方向) - スタート位置（最広部）
        # theta = 3π/2: 下側 (6時方向) - 狭い

        if math.pi * 0.75 <= theta <= math.pi * 1.25:
            # 左側直線（スタート位置）: 幅16単位
            track_width = 16
        elif math.pi * 0.25 <= theta <= math.pi * 0.75:
            # 上部カーブ: 幅6単位（最狭）
            track_width = 6
        elif theta <= math.pi * 0.25 or theta >= math.pi * 1.75:
            # 右側直線: 幅9単位
            track_width = 9
        else:
            # 下部カーブ: 幅6単位
            track_width = 6

        # 外周からtrack_width分内側に配置
        # 楕円の法線方向にオフセット
        outer_a = 14
        outer_b = 9

        # 楕円上の点
        x_outer = 15 + outer_a * math.cos(theta)
        y_outer = 10 + outer_b * math.sin(theta)

        # 内周の楕円パラメータを計算
        inner_a = outer_a - track_width
        inner_b = outer_b - track_width * (outer_b / outer_a)

        x_inner = 15 + inner_a * math.cos(theta)
        y_inner = 10 + inner_b * math.sin(theta)

        vertices.append([round(x_inner, 2), round(y_inner, 2)])

    return vertices
```

**セクション別内周パラメータ**:
- 左側（幅16）: 半長軸 ≈ -2, 半短軸 ≈ -7（外側より広い）
- 上部（幅6）: 半長軸 ≈ 8, 半短軸 ≈ 3
- 右側（幅9）: 半長軸 ≈ 5, 半短軸 ≈ 0
- 下部（幅6）: 半長軸 ≈ 8, 半短軸 ≈ 3

### 3.3 中央障害物の定義

円形障害物（直径8単位、16角形で近似）:

```python
def generate_central_obstacle():
    """中央の円形障害物を生成"""
    vertices = []
    center_x, center_y = 15, 10
    radius = 4  # 直径8単位

    for i in range(16):
        theta = 2 * math.pi * i / 16
        x = center_x + radius * math.cos(theta)
        y = center_y + radius * math.sin(theta)
        vertices.append([round(x, 2), round(y, 2)])

    return vertices
```

### 3.4 実装上の注意点

**可変幅の課題**:
- 単純な楕円オフセットでは、スタート位置で内周が外周より外側になる
- 解決策: スタート位置付近では内周を削除し、外周のみとする
- または: 左側を開放エリア（スタート/ピットエリア）として扱う

**推奨実装方針**:
1. **簡易版**: 内周を完全な楕円とし、幅を平均値（8-10単位）で固定
2. **詳細版**: セクションごとに個別のポリゴンを定義し、滑らかに接続
3. **実機再現版**: スタート位置を開放エリアとし、コース途中から内周を配置

### 3.5 スタート/ゴール位置

```json
"start_position": [3.0, 10.0],
"start_angle": 0.0,
"goal_position": [3.0, 10.0],
"goal_radius": 1.0
```

**配置理由**:
- 画像の「START」位置（左側直線部の中央）に配置
- 左側は最も広い（16単位）ため、安全にスタート可能
- 角度0度で右方向を向いてスタート

### 3.6 チェックポイント配置

コースを4分割してチェックポイントを配置（反時計回り）:

```json
"checkpoints": [
  {
    "position": [15.0, 3.0],
    "radius": 1.2,
    "index": 0,
    "description": "下部カーブ（6時方向）"
  },
  {
    "position": [25.0, 10.0],
    "radius": 1.5,
    "index": 1,
    "description": "右側直線（3時方向）"
  },
  {
    "position": [15.0, 17.0],
    "radius": 1.0,
    "index": 2,
    "description": "上部カーブ（12時方向・最狭部）"
  },
  {
    "position": [8.0, 10.0],
    "radius": 1.5,
    "index": 3,
    "description": "左側直線（9時方向・ゴール手前）"
  }
]
```

**チェックポイント半径の考慮**:
- 狭いセクション（上部カーブ）: 半径1.0（小さめ）
- 広いセクション（左側・右側）: 半径1.5（大きめ）
- トラック幅に応じて調整

## 4. 難易度設定（可変幅トラック対応）

### 4.1 Easy版（練習用）

**トラック幅**（すべて+50%増し）:
- スタート位置: 24単位（実機の1.5倍）
- 上部カーブ: 9単位（実機の1.5倍）
- 右側直線: 14単位
- 下部カーブ: 9単位

**その他の設定**:
- 中央障害物: なし
- チェックポイント半径: 2.5単位（大きめ）
- ゴール半径: 1.5単位

**用途**: 基本的な走行ルート学習、可変幅に慣れる

### 4.2 Medium版（実機相当）

**トラック幅**（実測値を再現）:
- スタート位置: **16単位**（1.6m）
- 上部カーブ: **6単位**（0.6m）← 最狭部
- 右側直線: 9単位（0.9m）
- 下部カーブ: 6単位（0.6m）

**その他の設定**:
- 中央障害物: あり（直径8単位）
- チェックポイント半径: 1.0-1.5単位（セクションにより変動）
- ゴール半径: 1.0単位

**用途**: 実コースと同等の難易度、実機転移を目指す学習

**難易度の特徴**:
- 車両幅1.9単位に対し、最狭部が6単位しかない
- 安全マージンは片側約2単位のみ（非常にタイト）
- スムーズな速度制御とハンドリングが必須

### 4.3 Hard版（上級）

**トラック幅**（実機の-20%）:
- スタート位置: 13単位（実機より狭い）
- 上部カーブ: **5単位**（0.5m）← 極狭
- 右側直線: 7単位
- 下部カーブ: 5単位

**その他の設定**:
- 中央障害物: あり（直径10単位、より大きい）
- 追加障害物: カーブ入口に小さな障害物（直径2単位）を2箇所配置
- チェックポイント半径: 0.8単位（小さめ、通過が難しい）
- ゴール半径: 0.6単位

**用途**: より精密な制御の学習、エキスパート向け

**難易度の特徴**:
- 最狭部5単位に対し車両幅1.9単位（マージン片側1.5単位程度）
- ほぼ完璧な走行ラインが要求される
- 実機よりも難しい設定

### 4.4 難易度比較表

| 項目 | Easy | Medium（実機相当） | Hard |
|------|------|-------------------|------|
| スタート幅 | 24単位 | **16単位** | 13単位 |
| 最狭部幅 | 9単位 | **6単位** | 5単位 |
| 車両幅に対する比率 | 4.7倍 | **3.2倍** | 2.6倍 |
| 中央障害物 | なし | 直径8単位 | 直径10単位 |
| 難易度評価 | ★☆☆ | ★★☆ | ★★★ |

## 5. 実装手順

### Phase 1: Easy版の作成とテスト
1. `courses/real/oval_easy.json` を作成
2. 外周・内周のみのシンプルなコース
3. GUIで可視化してレイアウト確認
4. 車両がスタート位置に正しく配置されるか確認

### Phase 2: Medium版の作成
1. `courses/real/oval_medium.json` を作成
2. 中央障害物を追加
3. チェックポイントの配置を調整
4. 実機相当の難易度になっているか検証

### Phase 3: Hard版の作成
1. `courses/real/oval_hard.json` を作成
2. トラック幅を狭める
3. コーナー部に追加障害物を配置
4. より高度な走行技術が必要になるよう調整

### Phase 4: カリキュラム学習への統合
1. `src/curriculum/curriculum_manager.py` に新コースを追加
2. 難易度順: oval_easy → oval_medium → oval_hard
3. 成功率閾値の調整（各コースで0.8以上で次へ）

### Phase 5: 検証とチューニング
1. 各難易度で学習を実行
2. 学習曲線を確認（TensorBoard）
3. 必要に応じて以下を調整:
   - チェックポイント位置
   - 報酬関数パラメータ
   - トラック幅
   - 障害物サイズ

## 6. 座標計算ツールの作成（可変幅対応）

実装を効率化するため、可変幅トラックに対応した座標計算スクリプトを作成:

```python
# scripts/course-generation/generate_real_course.py

import json
import math
from typing import List, Tuple

def generate_ellipse_vertices(center_x: float, center_y: float,
                              a: float, b: float,
                              num_points: int = 32) -> List[List[float]]:
    """楕円の頂点リストを生成"""
    vertices = []
    for i in range(num_points):
        theta = 2 * math.pi * i / num_points
        x = center_x + a * math.cos(theta)
        y = center_y + b * math.sin(theta)
        vertices.append([round(x, 2), round(y, 2)])
    return vertices

def get_track_width_at_angle(theta: float, difficulty: str) -> float:
    """
    角度に応じた可変トラック幅を返す

    Args:
        theta: 角度（ラジアン）
        difficulty: "easy", "medium", "hard"

    Returns:
        その角度でのトラック幅（シミュレーター単位）
    """
    # 角度を0-2πの範囲に正規化
    theta = theta % (2 * math.pi)

    # 基準幅を難易度別に設定
    if difficulty == "easy":
        widths = {"start": 24, "top": 9, "right": 14, "bottom": 9}
    elif difficulty == "hard":
        widths = {"start": 13, "top": 5, "right": 7, "bottom": 5}
    else:  # medium（実機相当）
        widths = {"start": 16, "top": 6, "right": 9, "bottom": 6}

    # 角度に応じてセクションを判定
    # theta = 0: 右側 (3時)、π/2: 上側 (12時)、π: 左側 (9時)、3π/2: 下側 (6時)

    if 0.75 * math.pi <= theta <= 1.25 * math.pi:
        # 左側直線（スタート位置）: 幅が広い
        return widths["start"]
    elif 0.25 * math.pi <= theta <= 0.75 * math.pi:
        # 上部カーブ: 幅が狭い
        return widths["top"]
    elif theta <= 0.25 * math.pi or theta >= 1.75 * math.pi:
        # 右側直線: 中間的な幅
        return widths["right"]
    else:
        # 下部カーブ: 幅が狭い
        return widths["bottom"]

def generate_variable_width_inner_wall(center_x: float, center_y: float,
                                       outer_a: float, outer_b: float,
                                       difficulty: str,
                                       num_points: int = 32) -> List[List[float]]:
    """
    可変幅トラックの内周壁を生成

    簡易版: 各点で法線方向に幅分だけオフセット
    """
    vertices = []

    for i in range(num_points):
        theta = 2 * math.pi * i / num_points

        # その角度でのトラック幅を取得
        track_width = get_track_width_at_angle(theta, difficulty)

        # 外周上の点
        x_outer = center_x + outer_a * math.cos(theta)
        y_outer = center_y + outer_b * math.sin(theta)

        # 楕円の法線方向の単位ベクトル計算
        # 楕円のパラメトリック表現での法線
        dx = -outer_a * math.sin(theta)
        dy = outer_b * math.cos(theta)
        normal_length = math.sqrt(dx**2 + dy**2)

        if normal_length > 0:
            nx = -dy / normal_length  # 内側を向く法線
            ny = dx / normal_length
        else:
            nx, ny = 0, 0

        # 内周の点 = 外周 - (法線方向 × トラック幅)
        x_inner = x_outer + nx * track_width
        y_inner = y_outer + ny * track_width

        vertices.append([round(x_inner, 2), round(y_inner, 2)])

    return vertices

def generate_course(difficulty: str = "medium") -> dict:
    """
    指定難易度のコース定義JSONを生成

    Args:
        difficulty: "easy", "medium", "hard"

    Returns:
        コース定義辞書
    """
    # コースパラメータ
    center_x, center_y = 15, 10
    outer_a, outer_b = 14, 9

    # 外周壁
    outer_wall = generate_ellipse_vertices(center_x, center_y, outer_a, outer_b, 32)

    # 内周壁（可変幅）
    inner_wall = generate_variable_width_inner_wall(
        center_x, center_y, outer_a, outer_b, difficulty, 32
    )

    # 中央障害物
    if difficulty == "easy":
        central_obstacle = None
    elif difficulty == "hard":
        central_obstacle = generate_ellipse_vertices(center_x, center_y, 5, 5, 16)
    else:  # medium
        central_obstacle = generate_ellipse_vertices(center_x, center_y, 4, 4, 16)

    # チェックポイント
    if difficulty == "easy":
        checkpoint_radii = [2.5, 2.5, 2.5, 2.5]
    elif difficulty == "hard":
        checkpoint_radii = [0.8, 0.8, 0.8, 0.8]
    else:  # medium
        checkpoint_radii = [1.2, 1.5, 1.0, 1.5]

    checkpoints = [
        {"position": [15.0, 3.0], "radius": checkpoint_radii[0], "index": 0},
        {"position": [25.0, 10.0], "radius": checkpoint_radii[1], "index": 1},
        {"position": [15.0, 17.0], "radius": checkpoint_radii[2], "index": 2},
        {"position": [8.0, 10.0], "radius": checkpoint_radii[3], "index": 3},
    ]

    # コース定義を構築
    course = {
        "name": f"Real Oval Track - {difficulty.capitalize()}",
        "description": f"実機コースの{difficulty}版（可変幅トラック）",
        "difficulty": difficulty,
        "start_position": [3.0, 10.0],
        "start_angle": 0.0,
        "goal_position": [3.0, 10.0],
        "goal_radius": 1.5 if difficulty == "easy" else (1.0 if difficulty == "medium" else 0.6),
        "walls": [
            {
                "type": "polygon",
                "name": "outer_wall",
                "vertices": outer_wall
            },
            {
                "type": "polygon",
                "name": "inner_wall",
                "vertices": inner_wall
            }
        ],
        "checkpoints": checkpoints
    }

    # 中央障害物を追加（easyには無し）
    if central_obstacle:
        course["walls"].append({
            "type": "polygon",
            "name": "central_obstacle",
            "vertices": central_obstacle
        })

    return course

if __name__ == "__main__":
    import os

    # 出力ディレクトリを作成
    os.makedirs("courses/real", exist_ok=True)

    # 3つの難易度でコースを生成
    for difficulty in ["easy", "medium", "hard"]:
        course = generate_course(difficulty)

        filename = f"courses/real/oval_{difficulty}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(course, f, indent=2, ensure_ascii=False)

        print(f"✓ {filename} を生成しました")

    print("\n全てのコース定義ファイルを生成しました！")
```

## 7. 検証テスト項目

### 7.1 物理シミュレーション検証
- [ ] 車両が壁に正しく衝突するか
- [ ] LiDARが壁と障害物を正しく検知するか
- [ ] スタート位置が適切か（壁に重ならない、広い部分に配置）
- [ ] チェックポイント通過が正しく検知されるか
- [ ] **可変幅トラック特有**:
  - [ ] 内周壁が滑らかに生成されているか（凹凸や交差がない）
  - [ ] 最狭部（上部カーブ）で車両が物理的に通過可能か
  - [ ] セクション間の接続部分で壁の不連続がないか

### 7.2 学習検証
- [ ] Easy版で100%の成功率を達成できるか
- [ ] Medium版で実機に近い挙動を学習できるか
- [ ] Hard版でより高度な制御を学習できるか
- [ ] カリキュラム学習が段階的に進行するか
- [ ] **可変幅トラック特有**:
  - [ ] 広い部分（スタート）で加速する戦略を学習するか
  - [ ] 狭い部分（上部カーブ）で減速する戦略を学習するか
  - [ ] トラック幅の変化に応じて速度制御を調整できるか

### 7.3 可視化検証
- [ ] GUI表示が実コースのイメージに近いか
- [ ] チェックポイントが視覚的に分かりやすいか
- [ ] 車両のサイズ感が適切か（特に最狭部での余裕）
- [ ] **可変幅トラック特有**:
  - [ ] トラック幅の変化が視覚的に明確か
  - [ ] 最狭部（上部カーブ）の難易度が視覚的に伝わるか
  - [ ] スタート位置の広さが適切に表現されているか

## 8. 実機との対応関係

### 8.1 センサー対応
- シミュレーター: 72方向LiDAR → 実機: ToFセンサーアレイ
- センサーデータの正規化方法を統一

### 8.2 制御パラメータ対応
- シミュレーター: steering [-1, 1] → 実機: サーボ角度 [0, 180]
- シミュレーター: throttle [-1, 1] → 実機: モーター PWM [0, 255]

### 8.3 物理パラメータ対応
- 車両質量: 1.4kg（バッテリー込み）
- 最高速度: 約3m/s
- 旋回半径: 約0.5m

これらは `src/physics/vehicle.py` で既に設定済み。

## 9. 次のステップ

### Phase 1: スクリプト作成と検証
1. ✅ この実装計画をレビュー（可変幅トラック対応）
2. ⬜ `scripts/course-generation/generate_real_course.py` を作成
3. ⬜ スクリプトを実行してJSON生成
4. ⬜ 生成されたJSONファイルの座標をチェック（内周壁の妥当性）

### Phase 2: Easy版でのプロトタイピング
5. ⬜ `courses/real/oval_easy.json` をGUIで可視化
6. ⬜ トラック幅の変化が正しく表現されているか確認
7. ⬜ スタート位置と壁の距離を確認
8. ⬜ 手動操作で一周走行してみる（操作感の確認）

### Phase 3: Medium版（実機相当）の作成と検証
9. ⬜ `courses/real/oval_medium.json` をGUIで可視化
10. ⬜ 最狭部（6単位）で車両が通過可能か確認
11. ⬜ 車両幅1.9単位との比率が適切か検証
12. ⬜ 簡単な学習テスト（100イテレーション程度）

### Phase 4: Hard版の作成
13. ⬜ `courses/real/oval_hard.json` をGUIで可視化
14. ⬜ 最狭部（5単位）での難易度を確認
15. ⬜ 追加障害物の配置を調整

### Phase 5: カリキュラム学習への統合
16. ⬜ `src/curriculum/curriculum_manager.py` を更新
17. ⬜ 新コース（real/oval_easy → medium → hard）を追加
18. ⬜ 成功率閾値を調整（特にmedium版）

### Phase 6: 本格的な学習実行
19. ⬜ カリキュラム学習で3段階すべてをテスト
20. ⬜ TensorBoardで学習曲線を確認
21. ⬜ 可変幅に応じた速度制御を学習できているか分析

### Phase 7: 最終調整
22. ⬜ 報酬関数の調整（必要に応じて）
23. ⬜ トラック幅の微調整（実機により近づける）
24. ⬜ チェックポイント位置の最適化
25. ⬜ ドキュメント更新（CLAUDE.mdにコース情報追加）

## 10. 参考資料

- 既存コース定義: `courses/easy/simple_oval.json`
- 環境実装: `src/env/minicar_env.py`
- 物理エンジン: `src/physics/world.py`
- カリキュラム管理: `src/curriculum/curriculum_manager.py`

---

## 補足: 可変幅トラックの実装上の課題と解決策

### 課題1: 内周壁の生成方法

**問題**: 単純な楕円オフセットでは、幅が広い部分で内周が外側にはみ出す可能性

**解決策**:
- 各点で法線方向にオフセットする方法を採用
- スタート位置（幅16単位）では内周を省略し、開放エリアとすることも検討
- または、スタート位置のみ別のポリゴンで定義

### 課題2: セクション間の滑らかな接続

**問題**: トラック幅が急激に変化すると、壁が不連続になる可能性

**解決策**:
- 32頂点以上で楕円を近似し、滑らかに変化させる
- セクション境界で線形補間を使用
- 生成後のJSONを可視化して確認

### 課題3: 学習の難易度

**問題**: 可変幅トラックは固定幅より学習が難しい可能性

**解決策**:
- カリキュラム学習で段階的に難易度を上げる
- 報酬関数に「トラック幅に応じた速度制御」を組み込む検討
- 狭い部分での減速を促す報酬設計

---

**作成日**: 2025-12-11
**更新日**: 2025-12-11
**対象画像**: 実コースレイアウト写真
**実測コースサイズ**: 約3m × 2m
**トラック幅**: 可変（0.6m - 1.6m）
**最大の特徴**: トラック幅が2.6倍変化する可変幅コース
