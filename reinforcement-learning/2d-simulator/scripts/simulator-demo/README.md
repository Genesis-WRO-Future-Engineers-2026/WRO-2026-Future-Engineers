# 手動制御デモ

ミニカー2Dシミュレーターを手動で操作するデモです。

---

## 🚀 クイックスタート

```bash
# プロジェクトルートから実行（デフォルト: easyコース）
./scripts/simulator-demo/run_manual_control.sh

# 利用可能なコース一覧を表示
./scripts/simulator-demo/run_manual_control.sh --list

# 特定のコースを指定して実行
./scripts/simulator-demo/run_manual_control.sh --course courses/medium/narrow_oval.json
./scripts/simulator-demo/run_manual_control.sh --course courses/hard/tight_oval.json
./scripts/simulator-demo/run_manual_control.sh --course courses/hard/s_curve.json
```

**操作:** ↑↓←→キーで車を動かせます。`ESC`で終了。

---

## 📂 ファイル構成

```
simulator-demo/
├── README.md                # このファイル
├── manual_control.py        # 手動制御スクリプト
└── run_manual_control.sh    # 起動スクリプト（実行可能）
```

---

## 🎮 操作方法

| キー | 動作 |
|------|------|
| `↑` / `W` | アクセル |
| `↓` / `S` | ブレーキ |
| `←` / `A` | 左旋回 |
| `→` / `D` | 右旋回 |
| `R` | リセット |
| `ESC` / `Q` | 終了 |

---

## 🎯 ゲームのルール

1. **目的**: 4つのチェックポイントを順番に通過して、ゴールに戻る
2. **チェックポイント**: 緑色の円で表示
3. **ゴール**: 金色の円で表示（スタート地点）
4. **制限時間**: 2000ステップ（約66秒）
5. **失格条件**:
   - 壁に衝突（LiDARの最小距離が0.1m以下）
   - 制限時間超過

---

## 🖥️ 画面の見方

- **車両**: 青い矩形（赤い線が前方向）
- **LiDAR**: 黄色い線（障害物検知、72方向）
- **チェックポイント**: 緑色の円
- **ゴール**: 金色の円
- **壁**: グレーのポリゴン

### デバッグ情報（画面左上）

- **Speed**: 現在の速度 (m/s)
- **Step**: 現在のステップ数
- **Reward**: 累積報酬
- **CPs**: チェックポイント通過数 / 総数
- **Min Dist**: 最も近い壁までの距離 (m)

---

## 📍 利用可能なコース

### Easy（初級）
- **simple_oval.json**: シンプルな楕円形コース。4つのチェックポイントを時計回りに通過してゴールに戻ります。

### Medium（中級）
- **narrow_oval.json**: 幅が狭い楕円形コース。より正確な操作が求められます。

### Hard（上級）
- **tight_oval.json**: カーブの曲率が大きい楕円形コース。急カーブでの速度調整が重要です。
- **s_curve.json**: S字カーブを含む複雑なコース。高度な操作テクニックが必要です。

### コース選択方法

```bash
# コース一覧を表示
./scripts/simulator-demo/run_manual_control.sh --list

# 特定のコースで実行
./scripts/simulator-demo/run_manual_control.sh --course courses/medium/narrow_oval.json
```

---

## 🔧 実行方法

### 方法1: シェルスクリプト実行（推奨）

```bash
cd /path/to/minicar-battle/reinforcement-learning/2d-simulator

# デフォルトコース（easy/simple_oval.json）で実行
./scripts/simulator-demo/run_manual_control.sh

# 特定のコースを指定
./scripts/simulator-demo/run_manual_control.sh --course courses/hard/s_curve.json

# 利用可能なコース一覧を表示
./scripts/simulator-demo/run_manual_control.sh --list
```

### 方法2: Pythonスクリプト直接実行

```bash
cd /path/to/minicar-battle/reinforcement-learning/2d-simulator
source venv/bin/activate

# デフォルトコース
python scripts/simulator-demo/manual_control.py

# コース指定
python scripts/simulator-demo/manual_control.py --course courses/medium/narrow_oval.json

# コース一覧表示
python scripts/simulator-demo/manual_control.py --list
```

---

## 🔍 トラブルシューティング

### ウィンドウが表示されない

- Pygameが正しくインストールされているか確認してください
- macOSの場合、セキュリティ設定でPythonの画面録画権限が許可されているか確認してください

### エラー: `ModuleNotFoundError: No module named 'pygame'`

```bash
source venv/bin/activate
pip install pygame gymnasium numpy box2d-py
```

### エラー: `command 'swig' failed`

SWIGをインストールしてください：

```bash
brew install swig  # macOS
```

その後、再度パッケージをインストール：

```bash
source venv/bin/activate
pip install box2d-py
```

---

## 📚 関連ドキュメント

- [プロジェクトREADME](../../README.md)
- [強化学習デモ](../rl-training/README.md)
- [スクリプト全体のREADME](../README.md)

---

**作成日**: 2025-12-10
**場所**: `scripts/simulator-demo/`
