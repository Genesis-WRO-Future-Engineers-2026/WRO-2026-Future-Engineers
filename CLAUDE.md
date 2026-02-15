# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

自動運転ミニカーバトルプロジェクト - Tamiya TT-02シャーシを使った競技用自動運転システムの開発。

**ハードウェア制御システム** (`seven/`) - Arduino Nano R4 + VL53L1X ToFセンサー7個による自動走行システム

### 競技目標
- **タイムトライアル**: 9秒以下のラップタイムを目指す
- **エンデュランス**: 6分間の連続周回レース（壁衝突なし、チェックポイント順番通過）

### 競技結果
- **決勝**: 3周17.5秒（優勝）

## Repository Structure

```
minicar-battle/
├── seven/                           # Arduino自動走行システム
│   ├── seven.ino                   # メインスケッチ（エントリーポイント）
│   ├── Config.h                    # 全設定値の一元管理
│   ├── SensorReader.cpp/h          # VL53L1Xセンサー読み取り
│   ├── GapFinder.cpp/h             # 最遠+隣接センサー方式による目標角度決定
│   ├── SteeringController.cpp/h    # Pure Pursuit制御によるステアリング計算
│   ├── Actuator.cpp/h              # サーボ・ESCへのPWM出力
│   └── Logger.h                    # デバッグ出力（ヘッダーオンリー）
├── CLAUDE.md                       # 本ドキュメント
├── README.md                       # プロジェクト詳細ドキュメント
└── LICENSE                         # MITライセンス
```

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       Arduino Nano R4                            │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ SensorReader │───▶│  GapFinder   │───▶│ SteeringController│   │
│  │  (I2C読取)   │    │(目標角度決定) │    │  (Pure Pursuit)   │   │
│  └──────────────┘    └──────────────┘    └────────┬─────────┘   │
│                                                   │             │
│  ┌──────────────┐      ┌─────────────────────────▼──────┐      │
│  │  TCA9548A    │      │            Actuator             │      │
│  │ マルチプレクサ│      │    (PWM出力 + 定速走行)         │      │
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

### Sensor Layout

```
                   正面 (Sensor 3: 0°)
                         │
              -15°       │       +15°
               (S2)      │      (S4)
         -30°     \      │      /     +30°
          (S1)     \     │     /     (S5)
    -60°            \    │    /            +60°
  (Sensor 0)             │             (Sensor 6)
     左                   │                   右
```

| センサー | チャンネル | 角度 | 役割 |
|---------|-----------|------|------|
| Sensor 0 | CH0 | -60° | 左側方 |
| Sensor 1 | CH1 | -30° | 左斜め前 |
| Sensor 2 | CH2 | -15° | 左前方 |
| Sensor 3 | CH3 | 0° | 正面 |
| Sensor 4 | CH4 | +15° | 右前方 |
| Sensor 5 | CH5 | +30° | 右斜め前 |
| Sensor 6 | CH6 | +60° | 右側方 |

---

## Control Algorithm: Follow the Gap + Pure Pursuit

### 最遠+隣接センサー方式（GapFinder）

1. 有効な7センサーから距離が最も遠い1つを選択（ヒステリシス付き）
2. その隣接センサー（左右）を取得（端の場合は片側のみ）
3. 最遠センサー+隣接センサーの距離で重み付けした角度をtarget_angleとする

### Pure Pursuit制御（SteeringController）

```
steering_angle = atan2(2 × L × sin(α), Ld)
```

- **L**: ホイールベース（mm）- MF-01X = 210mm
- **α**: 目標点への角度（ラジアン）- GapFinderのtarget_angle
- **Ld**: ルックアヘッド距離（mm）- **正面センサー(S3)の距離 - 車体長(1200mm)**

### 制御フロー

```
1. センサーデータ取得（7センサー同時読み取り）
      ↓
2. 緊急停止チェック（前方 < 400mm）
      ↓
3. 最遠センサー特定 + 隣接センサーで目標角度計算（GapFinder）
      ↓
4. Ld = 正面センサー距離 - 車体長（SteeringController）
      ↓
5. Pure Pursuitでステアリング角度を決定
      ↓
6. PWM出力（サーボ + ESC定速）
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

---

## Key Configuration Parameters

`seven/Config.h` で設定:

```cpp
// タイミング設定
const unsigned long MEASUREMENT_INTERVAL = 40;  // メインループ周期（ms）

// Pure Pursuitパラメータ
const float WHEELBASE_MM = 210.0;       // ホイールベース（mm）- MF-01X
const float LOOKAHEAD_OFFSET_MM = 1200.0;    // 車体長（mm）- センサー位置〜後輪軸

// 安全パラメータ
const uint16_t EMERGENCY_FRONT_THRESHOLD = 400;  // 前方緊急閾値（mm）

// 速度設定（定速走行）
const uint16_t SPEED_US = 1680;  // 走行速度パルス（μs）

// サーボ設定（μs単位）
const uint16_t SERVO_CENTER = 1415;  // 中央位置
const uint16_t SERVO_MIN = 1115;     // 最小パルス幅（右）
const uint16_t SERVO_MAX = 1715;     // 最大パルス幅（左）
```

---

## Debug Output Format

`RUN_MODE=MODE_DEBUG_RUN` 時のシリアル出力例:

```
S0:1234 | S1:567 | S2:890 | S3:456 | S4:789 | S5:321 | S6:654 | T:15.0° Ld:600 St:13.5 RR | T:28000us(S:25000us)
```

| フィールド | 説明 |
|-----------|------|
| S0-S6 | 各センサーの距離（mm） |
| T | 目標角度（度） |
| Ld | ルックアヘッド距離（mm） |
| St | ステアリング角度（度） |
| L/R | ステアリング方向インジケーター |
| T | ループ時間（μs） |

---

## Safety Features

1. **緊急停止**: 前方センサー < 400mm で自動停止

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

## Collaboration Guidelines（対話時のガイドライン）

このプロジェクトでは、以下の観点を対話の中で自然に確認・促進すること。

### 1. 変更前の影響シーン確認

パラメータやアルゴリズムの変更を提案・実装する前に、以下の3シーンへの影響を確認する：

| シーン | 確認ポイント |
|--------|-------------|
| **直線** | 蛇行が増えないか？ |
| **緩カーブ** | スムーズに曲がれるか？ |
| **急カーブ（S字）** | アンダーステアが出ないか？ |

**促し方の例**:
- 「この変更は直線走行にも影響しますが、蛇行が増える可能性はありませんか？」
- 「S字コーナーでの挙動も確認しておきましょうか？」

### 2. 却下理由の記録促進

試行したパラメータや施策が却下された場合、その理由をConfig.hにコメントとして残すことを促す：

```cpp
// 却下履歴:
// LD_OFFSET = 1200: 却下（直線蛇行増加、2025-01-25）
// LD_OFFSET = 1050: 採用（3周18.53秒、S字改善）
```

**促し方の例**:
- 「この設定値を試した結果と理由をConfig.hにコメントで残しておきますか？」
- 「将来の参考のため、却下理由を記録しておきましょう」

### 3. 評価軸の明示化

複数の施策を比較検討する際は、評価軸を明確にするよう促す：

| 評価軸 | 説明 |
|--------|------|
| **タイム** | ラップタイムへの影響（秒） |
| **安定性** | 蛇行・壁衝突のリスク |
| **実装コスト** | 変更の複雑さ・リスク |

**促し方の例**:
- 「タイム改善と安定性のどちらを優先しますか？」
- 「この施策の評価軸を整理しましょう：タイム/安定性/コストの観点では...」

### 4. 変更レベルの分類

提案する変更のインパクトレベルを意識する：

| レベル | 内容 | 対応 |
|--------|------|------|
| **L1** | 単一パラメータ調整 | 即テスト可 |
| **L2** | アルゴリズム修正 | 影響範囲確認後テスト |
| **L3** | アーキテクチャ変更 | 費用対効果分析先行 |

**促し方の例**:
- 「これはL2（アルゴリズム修正）なので、GapFinderとSteeringControllerの両方への影響を確認しましょう」
- 「L3レベルの変更なので、まず費用対効果を分析しますか？」

---

## Branch Strategy

- `main` - メインブランチ（プロダクション）
- `feat/*` - 新機能開発用ブランチ

---

## Language

コードベース、コメント、ドキュメントは日本語で記述。新しいコードやコメントも日本語を使用すること。
