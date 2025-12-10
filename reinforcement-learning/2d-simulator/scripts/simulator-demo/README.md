# 手動制御デモ

ミニカー2Dシミュレーターを手動で操作するデモです。

---

## 🚀 クイックスタート

```bash
# プロジェクトルートから実行
./scripts/simulator-demo/run_manual_control.sh
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

## 📍 コースについて

**現在のコース**: `courses/easy/simple_oval.json`

シンプルな楕円形のコースです。4つのチェックポイントを時計回りに通過してゴールに戻ります。

---

## 🔧 実行方法

### 方法1: シェルスクリプト実行（推奨）

```bash
cd /path/to/minicar-battle/reinforcement-learning/2d-simulator
./scripts/simulator-demo/run_manual_control.sh
```

### 方法2: Pythonスクリプト直接実行

```bash
cd /path/to/minicar-battle/reinforcement-learning/2d-simulator
source venv/bin/activate
python scripts/simulator-demo/manual_control.py
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
