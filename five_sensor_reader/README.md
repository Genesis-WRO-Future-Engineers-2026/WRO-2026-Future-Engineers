# Five Sensor Reader - Follow the Gap 自動走行システム

5つのVL53L1X ToFセンサーとFollow the Gapアルゴリズムを使用した、Arduino Nano R4向け自動走行制御システム。

---

## システム概要

### アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                    Arduino Nano R4                          │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ SensorReader │───▶│  GapFinder   │───▶│  Steering    │  │
│  │  (I2C読取)   │    │ (ギャップ検出)│    │  Controller  │  │
│  └──────────────┘    └──────────────┘    │  (PD制御)    │  │
│         ▲                                └──────┬───────┘  │
│         │                                       │          │
│  ┌──────┴───────┐                        ┌──────▼───────┐  │
│  │  TCA9548A    │                        │   Actuator   │  │
│  │ マルチプレクサ│                        │  (PWM出力)   │  │
│  └──────────────┘                        └──────────────┘  │
└───────┬─────────────────────────────────────────┬──────────┘
        │                                         │
   ┌────┴────┐                              ┌─────┴─────┐
   │ VL53L1X │ × 5                          │サーボ/ESC │
   └─────────┘                              └───────────┘
```

### センサー配置

```
              正面 (Sensor 2: 0°)
                    │
           -20°     │     +20°
             \      │      /
              \     │     /
    -70°       \    │    /       +70°
  (Sensor 0)   (S1) │ (S3)   (Sensor 4)
     左              │              右
```

| センサー | チャンネル | 角度 | 役割 |
|---------|-----------|------|------|
| Sensor 0 | CH0 | -70° | 左側方 |
| Sensor 1 | CH1 | -20° | 左前方 |
| Sensor 2 | CH2 | 0° | 正面 |
| Sensor 3 | CH3 | +20° | 右前方 |
| Sensor 4 | CH4 | +70° | 右側方 |

---

## ファイル構成

```
five_sensor_reader/
├── five_sensor_reader.ino  # メインスケッチ（エントリーポイント）
├── Config.h                # 全設定値の一元管理
├── SensorReader.cpp/h      # VL53L1Xセンサー読み取り
├── GapFinder.cpp/h         # Follow the Gapアルゴリズム
├── SteeringController.cpp/h # PD制御によるステアリング計算
├── Actuator.cpp/h          # サーボ・ESCへのPWM出力
├── Logger.h                # デバッグ出力（ヘッダーオンリー）
└── README.md               # 本ドキュメント
```

---

## Follow the Gap アルゴリズム

### 概要

センサーデータから「通過可能な空間（ギャップ）」を検出し、最適なギャップ方向へステアリングする障害物回避手法。

### 処理フロー

```
1. センサーデータ取得
      ↓
2. 障害物膨張処理（安全マージン適用）
      ↓
3. ギャップ検出（連続するOPEN空間を検出）
      ↓
4. ギャップスコアリング（幅・距離・前方優先度で評価）
      ↓
5. 最適ギャップ選択
      ↓
6. PD制御でステアリング角度計算
```

### ギャップスコアリング

```
score = GAP_WEIGHT_DISTANCE × (距離スコア)
      + GAP_WEIGHT_WIDTH × (幅スコア)
      + GAP_WEIGHT_FORWARD × (前方優先スコア)
```

- **距離スコア**: ギャップ内の最小距離 / RELIABLE_RANGE
- **幅スコア**: ギャップ幅（度） / 140°
- **前方優先スコア**: 1 - |中心角度| / 70°

---

## PD制御

### 計算式

```
steering = Kp × target_angle + Kd × (target_angle - last_target_angle)
```

- **P項（比例）**: 目標角度に比例したステアリング
- **D項（微分）**: 角度変化率に比例した予測制御（オーバーシュート抑制）

### パラメータ調整

| パラメータ | 推奨範囲 | 効果 |
|-----------|---------|------|
| STEERING_KP | 0.5〜1.0 | 大きいほど反応が鋭敏 |
| STEERING_KD | 0.05〜0.2 | 大きいほど振動を抑制 |

---

## Config.h パラメータ一覧

### デバッグモード

| 定数 | 型 | 値 | 説明 |
|------|----|----|------|
| `DEBUG_MODE` | bool | false | true: PWM無効+シリアル出力、false: PWM有効 |

### ハードウェア設定

| 定数 | 型 | 値 | 説明 |
|------|----|----|------|
| `TCA9548A_ADDR` | uint8_t | 0x70 | I2Cマルチプレクサアドレス |
| `NUM_SENSORS` | uint8_t | 5 | センサー数 |
| `SENSOR_CHANNELS` | uint8_t[] | {0,1,2,3,4} | マルチプレクサチャンネル |
| `SENSOR_ANGLES` | float[] | {-70,-20,0,20,70} | 各センサーの取付角度（度） |
| `SERVO_PIN` | uint8_t | 9 | ステアリングサーボのピン |
| `ESC_PIN` | uint8_t | 10 | ESCのピン |

### センサーパラメータ

| 定数 | 型 | 値 | 説明 |
|------|----|----|------|
| `MIN_VALID_DISTANCE` | uint16_t | 50 | 最小有効測定距離（mm） |
| `RELIABLE_RANGE` | uint16_t | 4000 | 信頼できる測定範囲（mm） |
| `L1X_TIMING_BUDGET_US` | uint32_t | 20000 | VL53L1X測定時間（μs） |
| `L1X_INTER_MEASUREMENT_MS` | uint32_t | 25 | VL53L1X測定間隔（ms） |

### タイミング設定

| 定数 | 型 | 値 | 説明 |
|------|----|----|------|
| `MEASUREMENT_INTERVAL` | unsigned long | 35 | メインループ周期（ms） |

### ステアリングパラメータ

| 定数 | 型 | 値 | 説明 |
|------|----|----|------|
| `MAX_STEERING_ANGLE` | float | 20.0 | 最大操舵角（度） |

### Follow the Gap パラメータ

| 定数 | 型 | 値 | 説明 |
|------|----|----|------|
| `OBSTACLE_THRESHOLD` | float | 1500.0 | 障害物判定閾値（mm） |
| `OBSTACLE_INFLATION_RADIUS` | float | 200.0 | 障害物膨張半径（mm） |
| `MIN_GAP_WIDTH_ANGLE` | float | 30.0 | 最小通過可能ギャップ幅（度） |
| `GAP_WEIGHT_DISTANCE` | float | 0.3 | ギャップ選択時の距離重み |
| `GAP_WEIGHT_WIDTH` | float | 0.4 | ギャップ選択時の幅重み |
| `GAP_WEIGHT_FORWARD` | float | 0.2 | ギャップ選択時の前方優先重み |

### PD制御パラメータ

| 定数 | 型 | 値 | 説明 |
|------|----|----|------|
| `STEERING_KP` | float | 0.9 | 比例ゲイン |
| `STEERING_KD` | float | 0.1 | 微分ゲイン |

### 安全パラメータ

| 定数 | 型 | 値 | 説明 |
|------|----|----|------|
| `EMERGENCY_FRONT_THRESHOLD` | uint16_t | 400 | 前方緊急停止閾値（mm） |

### サーボ設定（μs単位）

| 定数 | 型 | 値 | 説明 |
|------|----|----|------|
| `SERVO_CENTER` | uint16_t | 1510 | 中央位置 |
| `SERVO_MIN` | uint16_t | 600 | 最小パルス幅 |
| `SERVO_MAX` | uint16_t | 2400 | 最大パルス幅 |

### ESC設定（μs単位）

| 定数 | 型 | 値 | 説明 |
|------|----|----|------|
| `ESC_STOP_US` | uint16_t | 1500 | 停止 |
| `ESC_MIN_US` | uint16_t | 1000 | 最小パルス幅 |
| `ESC_MAX_US` | uint16_t | 2000 | 最大パルス幅 |

### ステアリング連動速度制御

| 定数 | 型 | 値 | 説明 |
|------|----|----|------|
| `SPEED_STEERING_LINK_ENABLED` | bool | true | 速度連動の有効/無効 |
| `TOP_SPEED_US` | uint16_t | 1390 | 直進時の最速パルス |
| `CORNER_SPEED_US` | uint16_t | 1440 | 最大ステアリング時の減速パルス |
| `STEERING_DEADZONE` | float | 5.0 | 減速しない角度範囲（度） |

---

## ハードウェア要件

- **マイコン**: Arduino Nano R4
- **センサー**: VL53L1X ToFセンサー × 5
- **I2Cマルチプレクサ**: TCA9548A
- **ステアリング**: サーボモーター
- **駆動**: ESC + ブラシレスモーター
- **通信**: HC-06 Bluetooth（停止用）

### 配線

| 接続元 | 接続先 |
|-------|-------|
| Arduino SDA | TCA9548A SDA |
| Arduino SCL | TCA9548A SCL |
| TCA9548A CH0-4 | VL53L1X × 5 |
| Arduino Pin 9 | サーボ信号線 |
| Arduino Pin 10 | ESC信号線 |
| Arduino Serial1 | HC-06 |

---

## 使用方法

### 1. ライブラリのインストール

Arduino IDEで以下をインストール:
- **VL53L1X** (Pololu)
- **Servo** (Arduino標準)

### 2. 設定

`Config.h` の `DEBUG_MODE` を設定:
- `true`: デバッグモード（PWM無効、シリアル出力有効）
- `false`: 実機モード（PWM有効、シリアル出力無効）

### 3. 書き込み

Arduino IDEでArduino Nano R4に書き込み

### 4. 停止方法

HC-06 Bluetooth経由で任意のデータを送信すると停止

---

## デバッグ出力フォーマット

DEBUG_MODE=true 時のシリアル出力例:

```
S0:1234 | S1:567 | S2:890 | S3:456 | S4:789 | G:2 T:15.0° [C:12.3 W:40.0 D:1200] St:13.5 RR [Servo:1580] [ESC:1400] | T:28000us(S:25000us)
```

| フィールド | 説明 |
|-----------|------|
| S0-S4 | 各センサーの距離（mm） |
| G | 検出ギャップ数 |
| T | 目標角度（度） |
| C/W/D | 最適ギャップの中心角度/幅/最小距離 |
| St | ステアリング角度（度） |
| L/R | ステアリング方向インジケーター |
| Servo/ESC | 出力パルス幅（μs） |
| T | ループ時間（μs） |

---

## 安全機能

1. **緊急停止**: 前方センサー < 400mm で自動停止
2. **Bluetooth停止**: Serial1への入力で即時停止
3. **ギャップなし時**: 最も距離が遠い方向へ回避

---

# Five Sensor Reader - Follow the Gap Autonomous Driving System

An autonomous driving control system for Arduino Nano R4 using five VL53L1X ToF sensors and the Follow the Gap algorithm.

---

## System Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Arduino Nano R4                          │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ SensorReader │───▶│  GapFinder   │───▶│  Steering    │  │
│  │  (I2C Read)  │    │(Gap Detection)│   │  Controller  │  │
│  └──────────────┘    └──────────────┘    │ (PD Control) │  │
│         ▲                                └──────┬───────┘  │
│         │                                       │          │
│  ┌──────┴───────┐                        ┌──────▼───────┐  │
│  │  TCA9548A    │                        │   Actuator   │  │
│  │ Multiplexer  │                        │ (PWM Output) │  │
│  └──────────────┘                        └──────────────┘  │
└───────┬─────────────────────────────────────────┬──────────┘
        │                                         │
   ┌────┴────┐                              ┌─────┴─────┐
   │ VL53L1X │ × 5                          │Servo/ESC  │
   └─────────┘                              └───────────┘
```

### Sensor Layout

```
              Front (Sensor 2: 0°)
                    │
           -20°     │     +20°
             \      │      /
              \     │     /
    -70°       \    │    /       +70°
  (Sensor 0)   (S1) │ (S3)   (Sensor 4)
    Left             │            Right
```

| Sensor | Channel | Angle | Purpose |
|--------|---------|-------|---------|
| Sensor 0 | CH0 | -70° | Left side |
| Sensor 1 | CH1 | -20° | Left front |
| Sensor 2 | CH2 | 0° | Front |
| Sensor 3 | CH3 | +20° | Right front |
| Sensor 4 | CH4 | +70° | Right side |

---

## File Structure

```
five_sensor_reader/
├── five_sensor_reader.ino  # Main sketch (entry point)
├── Config.h                # Centralized configuration
├── SensorReader.cpp/h      # VL53L1X sensor reading
├── GapFinder.cpp/h         # Follow the Gap algorithm
├── SteeringController.cpp/h # PD control for steering
├── Actuator.cpp/h          # PWM output for servo/ESC
├── Logger.h                # Debug output (header-only)
└── README.md               # This document
```

---

## Follow the Gap Algorithm

### Overview

A reactive obstacle avoidance method that detects "passable gaps" from sensor data and steers toward the optimal gap.

### Processing Flow

```
1. Acquire sensor data
      ↓
2. Obstacle inflation (apply safety margin)
      ↓
3. Gap detection (find continuous OPEN spaces)
      ↓
4. Gap scoring (evaluate by width, distance, forward priority)
      ↓
5. Select best gap
      ↓
6. Calculate steering angle with PD control
```

### Gap Scoring

```
score = GAP_WEIGHT_DISTANCE × (distance score)
      + GAP_WEIGHT_WIDTH × (width score)
      + GAP_WEIGHT_FORWARD × (forward priority score)
```

- **Distance score**: min_distance_in_gap / RELIABLE_RANGE
- **Width score**: gap_width_degrees / 140°
- **Forward priority score**: 1 - |center_angle| / 70°

---

## PD Control

### Formula

```
steering = Kp × target_angle + Kd × (target_angle - last_target_angle)
```

- **P term (Proportional)**: Steering proportional to target angle
- **D term (Derivative)**: Predictive control based on angle change rate (reduces overshoot)

### Parameter Tuning

| Parameter | Recommended Range | Effect |
|-----------|------------------|--------|
| STEERING_KP | 0.5 - 1.0 | Higher = more responsive |
| STEERING_KD | 0.05 - 0.2 | Higher = less oscillation |

---

## Config.h Parameters

### Debug Mode

| Constant | Type | Value | Description |
|----------|------|-------|-------------|
| `DEBUG_MODE` | bool | false | true: PWM disabled + serial output, false: PWM enabled |

### Hardware Configuration

| Constant | Type | Value | Description |
|----------|------|-------|-------------|
| `TCA9548A_ADDR` | uint8_t | 0x70 | I2C multiplexer address |
| `NUM_SENSORS` | uint8_t | 5 | Number of sensors |
| `SENSOR_CHANNELS` | uint8_t[] | {0,1,2,3,4} | Multiplexer channels |
| `SENSOR_ANGLES` | float[] | {-70,-20,0,20,70} | Sensor mounting angles (degrees) |
| `SERVO_PIN` | uint8_t | 9 | Steering servo pin |
| `ESC_PIN` | uint8_t | 10 | ESC pin |

### Sensor Parameters

| Constant | Type | Value | Description |
|----------|------|-------|-------------|
| `MIN_VALID_DISTANCE` | uint16_t | 50 | Minimum valid distance (mm) |
| `RELIABLE_RANGE` | uint16_t | 4000 | Reliable measurement range (mm) |
| `L1X_TIMING_BUDGET_US` | uint32_t | 20000 | VL53L1X measurement time (μs) |
| `L1X_INTER_MEASUREMENT_MS` | uint32_t | 25 | VL53L1X measurement interval (ms) |

### Timing Configuration

| Constant | Type | Value | Description |
|----------|------|-------|-------------|
| `MEASUREMENT_INTERVAL` | unsigned long | 35 | Main loop period (ms) |

### Steering Parameters

| Constant | Type | Value | Description |
|----------|------|-------|-------------|
| `MAX_STEERING_ANGLE` | float | 20.0 | Maximum steering angle (degrees) |

### Follow the Gap Parameters

| Constant | Type | Value | Description |
|----------|------|-------|-------------|
| `OBSTACLE_THRESHOLD` | float | 1500.0 | Obstacle detection threshold (mm) |
| `OBSTACLE_INFLATION_RADIUS` | float | 200.0 | Obstacle inflation radius (mm) |
| `MIN_GAP_WIDTH_ANGLE` | float | 30.0 | Minimum passable gap width (degrees) |
| `GAP_WEIGHT_DISTANCE` | float | 0.3 | Distance weight for gap selection |
| `GAP_WEIGHT_WIDTH` | float | 0.4 | Width weight for gap selection |
| `GAP_WEIGHT_FORWARD` | float | 0.2 | Forward priority weight |

### PD Control Parameters

| Constant | Type | Value | Description |
|----------|------|-------|-------------|
| `STEERING_KP` | float | 0.9 | Proportional gain |
| `STEERING_KD` | float | 0.1 | Derivative gain |

### Safety Parameters

| Constant | Type | Value | Description |
|----------|------|-------|-------------|
| `EMERGENCY_FRONT_THRESHOLD` | uint16_t | 400 | Front emergency stop threshold (mm) |

### Servo Configuration (μs)

| Constant | Type | Value | Description |
|----------|------|-------|-------------|
| `SERVO_CENTER` | uint16_t | 1510 | Center position |
| `SERVO_MIN` | uint16_t | 600 | Minimum pulse width |
| `SERVO_MAX` | uint16_t | 2400 | Maximum pulse width |

### ESC Configuration (μs)

| Constant | Type | Value | Description |
|----------|------|-------|-------------|
| `ESC_STOP_US` | uint16_t | 1500 | Stop |
| `ESC_MIN_US` | uint16_t | 1000 | Minimum pulse width |
| `ESC_MAX_US` | uint16_t | 2000 | Maximum pulse width |

### Steering-Linked Speed Control

| Constant | Type | Value | Description |
|----------|------|-------|-------------|
| `SPEED_STEERING_LINK_ENABLED` | bool | true | Enable/disable speed linking |
| `TOP_SPEED_US` | uint16_t | 1390 | Top speed pulse (straight) |
| `CORNER_SPEED_US` | uint16_t | 1440 | Reduced speed pulse (cornering) |
| `STEERING_DEADZONE` | float | 5.0 | Angle range without speed reduction (degrees) |

---

## Hardware Requirements

- **MCU**: Arduino Nano R4
- **Sensors**: VL53L1X ToF sensor × 5
- **I2C Multiplexer**: TCA9548A
- **Steering**: Servo motor
- **Drive**: ESC + Brushless motor
- **Communication**: HC-06 Bluetooth (for stop command)

### Wiring

| From | To |
|------|-----|
| Arduino SDA | TCA9548A SDA |
| Arduino SCL | TCA9548A SCL |
| TCA9548A CH0-4 | VL53L1X × 5 |
| Arduino Pin 9 | Servo signal |
| Arduino Pin 10 | ESC signal |
| Arduino Serial1 | HC-06 |

---

## Usage

### 1. Install Libraries

Install via Arduino IDE:
- **VL53L1X** (Pololu)
- **Servo** (Arduino built-in)

### 2. Configuration

Set `DEBUG_MODE` in `Config.h`:
- `true`: Debug mode (PWM disabled, serial output enabled)
- `false`: Production mode (PWM enabled, serial output disabled)

### 3. Upload

Upload to Arduino Nano R4 via Arduino IDE

### 4. Stop Command

Send any data via HC-06 Bluetooth to stop the system

---

## Debug Output Format

Serial output example when DEBUG_MODE=true:

```
S0:1234 | S1:567 | S2:890 | S3:456 | S4:789 | G:2 T:15.0° [C:12.3 W:40.0 D:1200] St:13.5 RR [Servo:1580] [ESC:1400] | T:28000us(S:25000us)
```

| Field | Description |
|-------|-------------|
| S0-S4 | Distance from each sensor (mm) |
| G | Number of detected gaps |
| T | Target angle (degrees) |
| C/W/D | Best gap center angle/width/min distance |
| St | Steering angle (degrees) |
| L/R | Steering direction indicator |
| Servo/ESC | Output pulse width (μs) |
| T | Loop time (μs) |

---

## Safety Features

1. **Emergency Stop**: Auto-stop when front sensor < 400mm
2. **Bluetooth Stop**: Immediate stop on Serial1 input
3. **No Gap Fallback**: Steer toward the direction with maximum distance
