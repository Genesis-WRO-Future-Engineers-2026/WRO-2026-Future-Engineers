# 手動制御デモ

ミニカー2Dシミュレーターを手動で操作するデモです。

## 前提条件

ローカル環境（macOS/Linux）での実行を想定しています。

### 必要なもの

- Python 3.9以上（Python 3.13で動作確認済み）
- 仮想環境（venv）
- 以下のパッケージ：
  - pygame
  - gymnasium
  - numpy
  - box2d-py

## セットアップ

### 1. 仮想環境の作成

プロジェクトルートで以下を実行：

```bash
cd /path/to/minicar-battle/reinforcement-learning/2d-simulator
python3 -m venv venv
```

### 2. 依存パッケージのインストール

```bash
source venv/bin/activate
pip install --upgrade pip
pip install pygame gymnasium numpy box2d-py
```

**注意**: `box2d-py`のインストールには`swig`が必要です。インストールされていない場合：

```bash
# macOSの場合
brew install swig

# Linuxの場合
sudo apt-get install swig
```

## 実行方法

### 方法1: 実行スクリプトを使う（推奨）

```bash
cd /path/to/minicar-battle/reinforcement-learning/2d-simulator
./scripts/demo/run_manual_control.sh
```

### 方法2: 直接Pythonスクリプトを実行

```bash
cd /path/to/minicar-battle/reinforcement-learning/2d-simulator
source venv/bin/activate
python scripts/demo/manual_control.py
```

## 操作方法

Pygameウィンドウが開いたら、以下のキーで車を操作できます：

| キー | 動作 |
|------|------|
| ↑ / W | 前進 |
| ↓ / S | 後退 |
| ← / A | 左旋回 |
| → / D | 右旋回 |
| R | リセット |
| ESC / Q | 終了 |

## ゲームのルール

1. **目的**: 4つのチェックポイントを順番に通過して、ゴールに戻る
2. **チェックポイント**: 黄色の円で表示されます
3. **ゴール**: 緑色の円で表示されます（スタート地点）
4. **制限時間**: 2000ステップ（約66秒）
5. **失格条件**:
   - 壁に衝突（LiDARの最小距離が0.1m以下）
   - 制限時間超過

## トラブルシューティング

### ウィンドウが表示されない

- Pygameが正しくインストールされているか確認してください
- macOSの場合、セキュリティ設定でPythonの画面録画権限が許可されているか確認してください

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

### Python 3.13での互換性問題

requirements.txtの古いバージョン指定では動作しない可能性があります。
最新版のパッケージを個別にインストールしてください（上記「依存パッケージのインストール」を参照）。

## 画面の見方

- **車両**: 白い三角形（進行方向を向いている）
- **LiDAR**: 車両から放射状に伸びる赤い線（障害物検知）
- **チェックポイント**: 黄色の円
- **ゴール**: 緑色の円
- **壁**: 白い線

画面上部にデバッグ情報が表示されます：
- **Speed**: 現在の速度 (m/s)
- **Step**: 現在のステップ数
- **Reward**: 累積報酬
- **CPs**: チェックポイント通過数 / 総数
- **Min Dist**: 最も近い壁までの距離 (m)

## コースについて

現在のコース: `courses/easy/simple_oval.json`

シンプルな楕円形のコースです。4つのチェックポイントを時計回りに通過してゴールに戻ります。
