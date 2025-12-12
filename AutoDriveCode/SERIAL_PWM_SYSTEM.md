# シリアル通信によるPWM制御システム

## 概要

このシステムは、Raspberry PiとArduinoを連携させてPWMパルスを生成します。

### システム構成

```
┌─────────────────────────────────────────────┐
│ Raspberry Pi                                │
│                                             │
│  1. センサーで距離測定                        │
│  2. ステアリング角度・速度を計算              │
│  3. パルス幅(μs)を計算                       │
│  4. シリアル通信でArduinoに送信              │
│                                             │
└────────────┬────────────────────────────────┘
             │ シリアル通信
             │ (GPIO14/15, 115200bps)
             │
┌────────────▼────────────────────────────────┐
│ Arduino Nano                                │
│                                             │
│  1. パルス幅を受信                           │
│  2. 受信した値でPWMパルス生成(50Hz)          │
│  3. 新しい値が来るまで同じパルス出力を継続    │
│  4. 通信タイムアウト時は自動停止              │
│                                             │
└────────────┬────────────────────────────────┘
             │
     ┌───────┴───────┐
     ▼               ▼
  サーボ           ESC
(ステアリング)   (モーター)
```

## なぜこの構成が必要か？

### 以前の構成の問題点
- Raspberry PiのGPIOは**ソフトウェアPWM**のため、パルス精度が低い
- LinuxのOSスケジューリングの影響で、タイミングが不安定
- サーボやESCが誤動作する可能性がある

### 新しい構成の利点
- Arduinoは**ハードウェアPWM**で高精度なパルスを生成可能
- Raspberry Piは計算処理に専念できる
- 処理速度の違いに対応（Raspiが遅くてもArduinoが最後の値を保持）
- 通信途切れ時は安全に停止

---

## ファイル構成

### Raspberry Pi側

#### 1. `serial_comm.py` - シリアル通信モジュール
```python
from serial_comm import ArduinoSerial

arduino = ArduinoSerial(port='/dev/serial0')
arduino.send_servo_pulse(1500)  # サーボに1500μs
arduino.send_esc_pulse(1500)    # ESCに1500μs
```

**主な機能:**
- Arduinoとのシリアル通信を管理
- `send_servo_pulse(pulse_us)` - サーボ用パルス幅送信
- `send_esc_pulse(pulse_us)` - ESC用パルス幅送信

#### 2. `actuators.py` - アクチュエーター制御（修正版）
```python
from actuators import Actuator

actuator = Actuator()
actuator.set_steering_angle(30)    # +30度に旋回
actuator.set_speed(1.6)            # 1.6ms = 前進
```

**変更点:**
- 以前: Raspberry PiのGPIOで直接PWM出力
- 現在: パルス幅を計算してArduinoに送信

**処理の流れ:**
1. 角度やms値を受け取る
2. パルス幅(μs)に変換
3. `serial_comm.py`経由でArduinoに送信

#### 3. `test_serial_actuator.py` - テストプログラム
動作確認用のインタラクティブなテストツール

---

### Arduino側

#### `pulse_generator.ino` - パルス生成プログラム

**主な機能:**
- シリアル通信でパルス幅を受信
- サーボ(pin 9)とESC(pin 10)にPWMパルスを出力
- 通信タイムアウト検知（1秒以上通信がない場合、自動停止）

**通信プロトコル:**
| コマンド | 意味 | 例 |
|---------|------|-----|
| `S1500\n` | サーボに1500μsのパルス幅を設定 | ステアリング中央 |
| `E1600\n` | ESCに1600μsのパルス幅を設定 | 前進 |

**パルス幅の範囲:**
- サーボ: 500～2400μs（-90°～+90°に対応）
- ESC: 1000～2000μs（後退～前進に対応）

---

## セットアップ手順

### 1. ハードウェア接続

#### Raspberry Pi ⇔ Arduino
```
Raspberry Pi (GPIO)     Arduino Nano
─────────────────────   ────────────
GPIO14 (TXD)    ───────> RX
GPIO15 (RXD)    <─────── TX
GND             ───────> GND
```

#### Arduino ⇔ アクチュエーター
```
Arduino          接続先
────────────     ─────────────
Pin 9     ────> サーボ信号線
Pin 10    ────> ESC信号線
5V        ────> サーボ・ESC電源（または別電源）
GND       ────> サーボ・ESC GND
```

### 2. Raspberry Piのシリアル設定

Raspberry PiのGPIOシリアルを有効化:

```bash
# 1. raspi-configを開く
sudo raspi-config

# 2. "Interface Options" → "Serial Port"を選択
# 3. "Would you like a login shell to be accessible over serial?" → No
# 4. "Would you like the serial port hardware to be enabled?" → Yes
# 5. 再起動
sudo reboot
```

### 3. Arduinoプログラムの書き込み

```bash
# Arduino IDEまたはarduino-cliを使用
arduino-cli compile --fqbn arduino:avr:nano AutoDriveCode/arduino/pulse_generator.ino
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:nano AutoDriveCode/arduino/pulse_generator.ino
```

### 4. Pythonライブラリのインストール

```bash
pip3 install pyserial
```

---

## 使い方

### テスト実行

```bash
cd AutoDriveCode/raspi/VL53L0X_rasp_python/auto_minicar_python_3
python3 test_serial_actuator.py
```

テストメニューから各機能を確認できます:
1. サーボテスト（左右に旋回）
2. ESCテスト（前進・後退・停止）
3. 同時制御テスト（旋回しながら前進）

### 既存のプログラムでの使用

`main.py`などの既存プログラムでは、**変更不要**で動作します。
`actuators.py`の内部実装が変わっただけで、インターフェースは同じです。

```python
# main.pyの該当部分（変更不要）
self.actuator = Actuator()
self.actuator.set_steering_angle(decision.angle)  # そのまま使える
```

---

## トラブルシューティング

### Q1. "Failed to open serial port" エラー

**原因:** シリアルポートへのアクセス権限がない

**解決策:**
```bash
# ユーザーをdialoutグループに追加
sudo usermod -a -G dialout $USER

# ログアウト→ログインで反映
# または
sudo reboot
```

### Q2. Arduinoが応答しない

**確認事項:**
1. Arduino Nanoが正しく接続されているか
2. `pulse_generator.ino`が書き込まれているか
3. 配線が正しいか（TX⇔RX、GND⇔GND）
4. ボーレートが一致しているか（115200bps）

**デバッグ方法:**
```bash
# シリアルモニターで確認
screen /dev/serial0 115200

# 手動でコマンド送信
echo "S1500" > /dev/serial0
```

### Q3. サーボやESCが動かない

**確認事項:**
1. サーボ・ESCの電源は供給されているか
2. 信号線がArduinoの正しいピン(9, 10)に接続されているか
3. ESCがキャリブレーション済みか

**ESCキャリブレーション手順:**
```bash
# テストプログラムで以下を実行
python3 test_serial_actuator.py

# ESCテストを選択し、停止→最高速→停止の順に動かす
```

### Q4. "Communication timeout" が頻発する

**原因:** Raspberry Piの処理が1秒以上止まっている

**解決策:**
- Arduino側の`COMM_TIMEOUT_MS`を延長（例: 3000ms）
- Raspberry Pi側の処理を高速化
- センサー読み取り頻度を調整

---

## 通信プロトコル詳細

### コマンド形式

```
<コマンド種別><パルス幅>\n

コマンド種別:
  S または s → サーボ制御
  E または e → ESC制御

パルス幅: マイクロ秒単位の整数値
```

### 例

| 送信コマンド | 意味 |
|------------|------|
| `S500\n` | サーボに500μs（最左 -90°） |
| `S1500\n` | サーボに1500μs（中央 0°） |
| `S2400\n` | サーボに2400μs（最右 +90°） |
| `E1000\n` | ESCに1000μs（最大後退） |
| `E1500\n` | ESCに1500μs（停止） |
| `E2000\n` | ESCに2000μs（最大前進） |

---

## パフォーマンス特性

### タイミング仕様

| 項目 | 値 |
|------|-----|
| PWM周波数 | 50Hz (20ms周期) |
| パルス精度 | ±1μs (Arduinoハードウェアタイマー使用) |
| シリアル通信速度 | 115200bps |
| コマンド送信時間 | 約1ms以下 |
| 通信タイムアウト | 1000ms（変更可能） |

### Raspberry Piの処理フロー

```python
# メインループ内（約20ms周期）
distances = sensor_manager.read_all_distances()     # ~10ms
decision = steering_controller.calculate_steering() # ~1ms
actuator.set_steering_angle(decision.angle)         # ~1ms (シリアル送信)
```

→ Raspberry Piが遅くても、Arduinoは最後のパルス幅を継続出力

---

## 今後の拡張案

### 1. フィードバック機能
Arduinoから現在のパルス幅やステータスを返信

### 2. 複数モーター対応
3モーター、4モーターなどに拡張

### 3. エンコーダー読み取り
Arduinoでエンコーダー値を読み取ってRaspberry Piに送信

---

## 参考情報

### パルス幅と動作の対応

#### サーボ（ステアリング）
```
  500μs ────────── 1500μs ────────── 2400μs
   -90°           0° (中央)           +90°
  (最左)          (直進)            (最右)
```

#### ESC（モーター）
```
 1000μs ────── 1500μs ────── 2000μs
 (最大後退)     (停止)     (最大前進)
```

### 関連ファイル
- `AutoDriveCode/raspi/VL53L0X_rasp_python/auto_minicar_python_3/serial_comm.py`
- `AutoDriveCode/raspi/VL53L0X_rasp_python/auto_minicar_python_3/actuators.py`
- `AutoDriveCode/arduino/pulse_generator.ino`
- `AutoDriveCode/raspi/VL53L0X_rasp_python/auto_minicar_python_3/test_serial_actuator.py`

---

## まとめ

このシステムにより、以下が実現できました:

✅ Raspberry Piは計算処理に専念
✅ Arduinoが高精度なPWMパルスを生成
✅ 処理速度の違いに柔軟に対応
✅ 通信途切れ時の安全停止機能
✅ 既存コードへの影響を最小限に

プロジェクトに入ったばかりの方でも、このドキュメントを読めばシステム全体の仕組みが理解できるようになっています。
