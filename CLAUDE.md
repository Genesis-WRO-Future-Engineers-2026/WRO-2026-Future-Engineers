# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

自動運転ミニカーバトルプロジェクト - Tamiya TT-02シャーシを使った競技用自動運転システムの開発。

**ハードウェア制御システム** (`seven/`) - Arduino Nano R4 + VL53L1X ToFセンサー7個による自動走行システム

### 競技目標
- **タイムトライアル**: 9秒以下のラップタイムを目指す
- **エンデュランス**: 6分間の連続周回レース（壁衝突なし、チェックポイント順番通過）

### 現在の記録
- **3周**: 24.11秒（1周平均8.04秒）
- **1周最速**: 8.3秒

## Repository Structure

```
minicar-battle/
├── seven/                           # Arduino自動走行システム
│   ├── seven.ino                   # メインスケッチ（エントリーポイント）
│   ├── Config.h                    # 全設定値の一元管理
│   ├── SensorReader.cpp/h          # VL53L1Xセンサー読み取り
│   ├── GapFinder.cpp/h             # 最遠+隣接センサー方式による目標角度決定
│   ├── SteeringController.cpp/h    # PD制御によるステアリング計算
│   ├── AcceleratorController.cpp/h # 距離連動速度制御
│   ├── Actuator.cpp/h              # サーボ・ESCへのPWM出力
│   └── Logger.h                    # デバッグ出力（ヘッダーオンリー）
├── CLAUDE.md                       # 本ドキュメント
└── README.md                       # プロジェクト詳細ドキュメント
```

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       Arduino Nano R4                            │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ SensorReader │───▶│  GapFinder   │───▶│ SteeringController│   │
│  │  (I2C読取)   │    │(目標角度決定) │    │    (PD制御)       │   │
│  └──────────────┘    └──────────────┘    └────────┬─────────┘   │
│         │                                         │             │
│         │            ┌───────────────────┐        │             │
│         └───────────▶│AcceleratorController│       │             │
│                      │  (距離連動速度)    │       │             │
│                      └────────┬──────────┘        │             │
│                               │                   │             │
│  ┌──────────────┐      ┌──────▼───────────────────▼──────┐      │
│  │  TCA9548A    │      │            Actuator             │      │
│  │ マルチプレクサ│      │          (PWM出力)              │      │
│  └──────────────┘      └──────────────────────────────────┘      │
└───────┬──────────────────────────────────────────┬───────────────┘
        │                                          │
   ┌────┴────┐                               ┌─────┴─────┐
   │ VL53L1X │ × 7                           │サーボ/ESC │
   └─────────┘                               └───────────┘
```

### Hardware Requirements

- **マイコン**: Arduino Nano R4
- **センサー**: VL53L1X ToFセンサー × 7
- **I2Cマルチプレクサ**: TCA9548A（アドレス: 0x70）
- **アクチュエーター**: サーボモーター（ステアリング）、ESC（速度制御）
- **通信**: HC-06 Bluetooth（緊急停止用、オプション）

### Sensor Layout

```
                   正面 (Sensor 3: 0°)
                         │
              -20°       │       +20°
               (S2)      │      (S4)
         -40°     \      │      /     +40°
          (S1)     \     │     /     (S5)
    -60°            \    │    /            +60°
  (Sensor 0)             │             (Sensor 6)
     左                   │                   右
```

| センサー | チャンネル | 角度 | 役割 |
|---------|-----------|------|------|
| Sensor 0 | CH0 | -60° | 左側方 |
| Sensor 1 | CH1 | -40° | 左斜め前 |
| Sensor 2 | CH2 | -20° | 左前方 |
| Sensor 3 | CH3 | 0° | 正面 |
| Sensor 4 | CH4 | +20° | 右前方 |
| Sensor 5 | CH5 | +40° | 右斜め前 |
| Sensor 6 | CH6 | +60° | 右側方 |

---

## Control Algorithm: Follow the Gap + PD制御

### 最遠+隣接センサー方式

1. 有効な7センサーから距離が最も遠い1つを選択
2. その隣接センサー（左右）を取得（端の場合は片側のみ）
3. 最遠センサー+隣接センサーの距離で重み付けした角度をtarget_angleとする

### PD制御

```
steering = Kp × target_angle - Kd × (target_angle - last_target_angle)
```

- **P項（比例）**: 目標角度に比例したステアリング
- **D項（微分）**: 角度変化率に基づく急変動抑制

### 制御フロー

```
1. センサーデータ取得（5センサー同時読み取り）
      ↓
2. 緊急停止チェック（前方 < 400mm）
      ↓
3. 最遠センサー特定 + 隣接センサーで目標角度計算
      ↓
4. PD制御でステアリング角度を決定
      ↓
5. 距離連動速度制御（前方距離に応じて減速）
      ↓
6. PWM出力（サーボ + ESC）
```

---

## Running the System

### 1. ライブラリのインストール

Arduino IDEで以下をインストール:
- **VL53L1X** (Pololu)
- **Servo** (Arduino標準)

### 2. 設定

`Config.h` の `RUN_MODE` を設定:
```cpp
#define MODE_DEBUG 0       // デバッグ専用（PWMなし、シリアルあり）
#define MODE_PRODUCTION 1  // 本番走行（PWMあり、シリアルなし）
#define MODE_DEBUG_RUN 2   // デバッグ走行（PWMあり、シリアルあり）

#define RUN_MODE MODE_PRODUCTION  // ← ここで動作モードを選択
```

### 3. 書き込み

```bash
# Arduino CLIを使用する場合
arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi seven
arduino-cli upload -p /dev/cu.usbmodem* --fqbn arduino:renesas_uno:unor4wifi seven
```

### 4. 停止方法

`ENABLE_BLUETOOTH_EMERGENCY=true` の場合、HC-06 Bluetooth経由で任意のデータを送信すると緊急停止

---

## Key Configuration Parameters

`seven/Config.h` で設定:

```cpp
// タイミング設定
const unsigned long MEASUREMENT_INTERVAL = 50;  // メインループ周期（ms）

// PD制御パラメータ
const float STEERING_KP = 1.0;  // 比例ゲイン
const float STEERING_KD = 0.0;  // 微分ゲイン

// 直進モード
const uint16_t STRAIGHT_MODE_THRESHOLD = 1500;  // 正面がこの距離以上なら直進（mm）

// 安全パラメータ
const uint16_t EMERGENCY_FRONT_THRESHOLD = 400;  // 前方緊急閾値（mm）

// 距離連動速度制御
const uint16_t DECEL_START_DISTANCE = 3000;  // 減速開始距離（mm）
const float DECEL_CURVE_EXPONENT = 0.5;      // 減速カーブ指数（小さいほど急）
const uint16_t MAX_SPEED_US = 1640;          // 最高速度パルス（μs）
const uint16_t MIN_SPEED_US = 1580;          // 最低速度パルス（μs）

// サーボ設定（μs単位）
const uint16_t SERVO_CENTER = 1425;  // 中央位置
const uint16_t SERVO_MIN = 1225;     // 最小パルス幅（右）
const uint16_t SERVO_MAX = 1625;     // 最大パルス幅（左）
```

---

## Debug Output Format

`RUN_MODE=MODE_DEBUG_RUN` 時のシリアル出力例:

```
S0:1234 | S1:567 | S2:890 | S3:456 | S4:789 | G:1 T:15.0° [C:12.3 W:40.0 D:1200] St:13.5 RR | T:28000us(S:25000us)
```

| フィールド | 説明 |
|-----------|------|
| S0-S4 | 各センサーの距離（mm） |
| T | 目標角度（度） |
| St | ステアリング角度（度） |
| L/R | ステアリング方向インジケーター |
| T | ループ時間（μs） |

---

## Safety Features

1. **緊急停止**: 前方センサー < 400mm で自動停止
2. **Bluetooth停止**: Serial1への入力で即時停止（`ENABLE_BLUETOOTH_EMERGENCY=true`時）

---

## Common Issues

**Q: センサーが初期化できない**
→ I2C接続確認、TCA9548Aのアドレス（0x70）確認、VL53L1Xの電源確認

**Q: サーボやESCが動かない**
→ `RUN_MODE` が `MODE_PRODUCTION` または `MODE_DEBUG_RUN` になっているか確認
→ ESCキャリブレーション実行

**Q: ステアリングが逆方向**
→ `Config.h` の `SERVO_MIN` / `SERVO_MAX` を入れ替え

---

## Branch Strategy

- `main` - メインブランチ（プロダクション）
- `feat/*` - 新機能開発用ブランチ

現在のブランチ: `feat/search_best_speed`

---

## Language

コードベース、コメント、ドキュメントは日本語で記述。新しいコードやコメントも日本語を使用すること。
