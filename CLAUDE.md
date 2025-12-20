# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

自動運転ミニカーバトルプロジェクト - Tamiya TT-02シャーシを使った競技用自動運転システムの開発。以下の2つの主要コンポーネントで構成:

1. **ハードウェア制御システム** (`AutoDriveCode/`) - Raspberry Pi + Arduino + ToFセンサーを使った実機制御
2. **強化学習シミュレーター** (`reinforcement-learning/2d-simulator/`) - PPO強化学習による走行戦略の開発

### 競技目標
- **タイムトライアル**: 9秒以下のラップタイムを目指す
- **エンデュランス**: 6分間の連続周回レース（壁衝突なし、チェックポイント順番通過）

## Repository Structure

```
minicar-battle/
├── AutoDriveCode/               # 実機制御システム（幾何計算ベース）
│   ├── VL53L0X_raspi/          # 5センサー制御コード（Raspberry Pi）
│   │   └── src/                # Python実装（main, sensors, actuators, etc.）
│   ├── arduino/                # Arduino PWM生成
│   │   └── pulse_generator.ino
│   ├── ARDUINO_SYSTEM_PLAN.md  # 壁追従アルゴリズムの数式と設計
│   └── SERIAL_PWM_SYSTEM.md    # Raspi-Arduino通信プロトコル
│
└── reinforcement-learning/
    └── 2d-simulator/           # 強化学習システム（Sim2Real）
        ├── src/                # シミュレーター本体
        │   ├── env/           # Gymnasium互換環境
        │   ├── physics/       # Box2D物理エンジン
        │   ├── rl/            # PPO実装
        │   └── curriculum/    # カリキュラム学習
        ├── scripts/           # 学習・評価スクリプト
        ├── courses/           # コース定義（JSON）
        └── CLAUDE.md          # シミュレーター専用ドキュメント
```

---

## AutoDriveCode: Hardware Control System

### System Architecture

```
┌────────────────────────────────┐
│ Raspberry Pi (計算処理)         │
│  - VL53L0X距離センサー読取 (I2C)│
│  - 壁検出・交点計算             │
│  - ステアリング角度決定          │
│  - パルス幅計算                 │
└──────────┬─────────────────────┘
           │ Serial (115200bps)
           │ GPIO14/15
┌──────────▼─────────────────────┐
│ Arduino Nano (PWM生成)          │
│  - 高精度PWMパルス出力 (50Hz)   │
│  - サーボ制御 (Pin 9)           │
│  - ESC制御 (Pin 10)             │
│  - 通信タイムアウト検知 (200ms) │
└──────────┬─────────────────────┘
           │
    ┌──────┴───────┐
    ▼              ▼
 サーボ          ESC/モーター
```

### Hardware Requirements

- **Raspberry Pi**: GPIO & I2Cが使用可能なモデル
- **Arduino Nano R4**: PWM生成専用
- **センサー**: VL53L0X ToFセンサー × 5個
  - I2Cアドレス: 0x2B, 0x2D, 0x2E, 0x2F, 0x30
  - GPIO Shutdown ピン: 2, 3, 4, 5, 6
- **アクチュエーター**: サーボモーター（ステアリング）、ESC（速度制御）

### Sensor Layout

```
        正面 (Sensor 3: 0°)
              |
       -20°   |   +20°
         \    |    /
          \   |   /
-70°       \  |  /       +70°
(S1 左)     \ | /     (S5 右)
           (S2) (S4)
```

### Wall Following Algorithm

**核心ロジック**: 左右2つのセンサーペアで壁の直線を検出し、y軸（車体正面方向）との交点差からステアリング角度を決定。

**数式詳細**: `AutoDriveCode/ARDUINO_SYSTEM_PLAN.md`を参照。

**制御状態**:
1. 両壁検出 → 交点差に比例したステアリング
2. 左壁のみ → 左へステアリング（開けた方向へ）
3. 右壁のみ → 右へステアリング
4. 壁なし → 直進

### Running the Hardware System

#### Setup (初回のみ)

```bash
# Raspberry Piのシリアルポート有効化
sudo raspi-config
# Interface Options → Serial Port → No (login shell), Yes (hardware)
sudo reboot

# Pythonライブラリインストール
pip3 install pyserial

# Arduinoプログラム書き込み（Arduino IDEまたはarduino-cli使用）
arduino-cli compile --fqbn arduino:avr:nano AutoDriveCode/arduino/pulse_generator.ino
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:nano AutoDriveCode/arduino/pulse_generator.ino
```

#### Run

```bash
cd AutoDriveCode/VL53L0X_raspi/src

# メインプログラム実行（Raspberry Pi上、sudo必須）
make run
# または
sudo python3 main.py

# テスト（Dockerコンテナ内で実行）
make test
make test-cov

# アクチュエーターテスト（Raspberry Pi上）
python3 test_serial_actuator.py
```

### Serial Communication Protocol

Raspberry Pi → Arduino間の通信フォーマット:

```
S<pulse_width_us>\n  # サーボ制御（例: S1500 = 中央）
E<pulse_width_us>\n  # ESC制御（例: E1500 = 停止）
```

**パルス幅範囲**:
- サーボ: 500-2400μs（-90°～+90°）
- ESC: 1000-2000μs（後退～前進）
  - 注意: 実際の最大前進速度は1.4ms（1400μs）

**安全機能**: Arduino側で200ms通信途絶時に自動停止（中央ステアリング + ESC停止）

### Key Configuration Parameters

`AutoDriveCode/VL53L0X_raspi/src/config.py`で設定:

```python
# ステアリングパラメータ
MAX_STEER_ANGLE = 30.0           # 最大操舵角（度）
INTERSECTION_DIFF_GAIN = 0.1     # 交点差のゲイン
ONE_SIDE_OPEN_STEER_RATIO = 0.5  # 片側開放時の操舵比率

# センサー信頼性パラメータ
RELIABLE_RANGE = 700             # 信頼できる測定範囲（mm）
MAX_SENSOR_DIFF = 200            # センサーペア間の最大許容差（mm）

# 速度パラメータ（ESCパルス幅, ms）
BASE_SPEED_PULSE = 1.52          # 基本速度
MAX_SPEED_PULSE = 1.4            # 最大速度（実機制約）
```

---

## Reinforcement Learning Simulator

### Overview

Box2D物理エンジンを使った2Dシミュレーターで、PPO強化学習によりSim2Real転移を目指す。

**詳細は `reinforcement-learning/2d-simulator/CLAUDE.md` を参照。**

### Quick Start

```bash
cd reinforcement-learning/2d-simulator

# 環境構築
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 重要: PYTHONPATHを設定（常に必要）
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 適応的学習開始（カリキュラム学習 + 自動報酬調整）
python scripts/rl-training/train_adaptive.py --total-iterations 2000 --gui

# TensorBoardで進捗確認
tensorboard --logdir=logs
```

### Training Commands

```bash
# 適応的学習（推奨）
python scripts/rl-training/train_adaptive.py --total-iterations 2000

# GUIで可視化
python scripts/rl-training/train_adaptive.py --gui --total-iterations 500

# チェックポイントから再開
python scripts/rl-training/train_adaptive.py \
  --resume models/checkpoints_adaptive/checkpoint_500.pth \
  --total-iterations 2000
```

### Testing

```bash
# すべてのテスト実行
pytest tests/

# カバレッジ付き
pytest tests/ --cov=src --cov-report=html

# 特定のテスト
pytest tests/test_env.py -v
```

### Observation Space (10 dimensions)

- **LiDAR**: 5方向（-60°, -30°, 0°, +30°, +60°）
- **速度**: vx, vy
- **角速度**: 1次元
- **前回の行動**: steering, throttle

**重要**: チェックポイント情報は観測空間に含まれない（Sim2Real対応のため）。エージェントはLiDARと速度情報のみで走行を学習。

### Reward Design

`src/env/minicar_env.py`の`_compute_reward()`メソッドで実装:

- 速度報酬: `speed * 0.03`
- 時間ペナルティ: `-0.2`（探索時間を許容）
- 壁接近ペナルティ: 距離 < 0.3m で発動
- 衝突ペナルティ: `-100.0`（Box2D物理衝突検出）
- チェックポイント報酬: `+200.0`（偶然の通過を強く評価）
- ゴール到達報酬: `+500.0`
- 時間ボーナス: `(max_steps - current_step) * 1.5`

---

## Development Workflow

### Hardware Development

1. **アルゴリズム変更**: `AutoDriveCode/VL53L0X_raspi/src/steering_controller.py`を編集
2. **パラメータ調整**: `config.py`のゲイン値や閾値を調整
3. **テスト実行**: Dockerコンテナ内で`make test`（単体テスト）
4. **実機テスト**: Raspberry Pi上で`make run`

### Simulation Development

1. **報酬関数変更**: `src/env/minicar_env.py`の`_compute_reward()`を編集
2. **コース追加**: `courses/`に新しいJSON定義を追加
3. **学習実行**: `train_adaptive.py`でカリキュラム学習
4. **モデル評価**: `test_saved_model.py`でGUI可視化

### Testing Strategy

- **AutoDriveCode**: Dockerコンテナでユニットテスト（実機センサーなしでテスト可能）
- **Simulator**: pytestで物理エンジン、環境、PPOの動作を検証

---

## Common Issues

### AutoDriveCode

**Q: "Failed to open serial port"**
→ ユーザーをdialoutグループに追加: `sudo usermod -a -G dialout $USER` → 再ログイン

**Q: サーボやESCが動かない**
→ ESCキャリブレーション: `test_serial_actuator.py`でESCテスト実行（停止→最高速→停止の順）

**Q: センサーが初期化できない**
→ I2C接続確認: `i2cdetect -y 1`（Raspberry Pi上）

### Simulator

**Q: "ModuleNotFoundError: No module named 'src'"**
→ `export PYTHONPATH="$(pwd):$PYTHONPATH"`を実行

**Q: Box2Dインストールエラー**
→ macOS: `brew install swig`, Linux: `sudo apt-get install swig`

**Q: 学習が進まない**
→ 報酬関数をデバッグ（`info['total_reward']`を確認）、ハイパーパラメータ調整

---

## Key Documents

- `AutoDriveCode/ARDUINO_SYSTEM_PLAN.md` - 壁追従アルゴリズムの数学的基礎（極座標変換、直線方程式、交点計算）
- `AutoDriveCode/SERIAL_PWM_SYSTEM.md` - Raspberry Pi-Arduino間のシリアル通信詳細
- `AutoDriveCode/VL53L0X_raspi/src/README.md` - 5センサーシステムの概要
- `reinforcement-learning/2d-simulator/CLAUDE.md` - シミュレーター専用の詳細ドキュメント
- `reinforcement-learning/2d-simulator/doc/ADAPTIVE_TRAINING.md` - カリキュラム学習の詳細
- `reinforcement-learning/2d-simulator/doc/REWARD_DESIGN.md` - 報酬設計の思想と履歴

---

## Branch Strategy

- `main` - メインブランチ（プロダクション）
- `feat/*` - 新機能開発用ブランチ

現在のブランチ: `feat/5sensors_raspi`

---

## Language

コードベース、コメント、ドキュメントは日本語で記述。新しいコードやコメントも日本語を使用すること。
