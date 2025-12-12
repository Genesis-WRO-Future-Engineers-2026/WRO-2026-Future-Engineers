# 実機デプロイスクリプト

本番競技会での実機制御用スクリプト。

## スクリプト一覧

### 1. `run_real_robot.py` - 実機ロボット制御（本番用）

**用途**: 本番競技会での実機制御

**特徴**:
- コース定義ファイルは不要（LiDARセンサーのみで走行）
- 実機のセンサー（LiDAR、IMU、エンコーダー）から直接データ取得
- 実機のモーター（サーボ、ESC）に直接コマンド送信
- 6分間連続走行

**使い方**:

```bash
# 基本的な使い方（実機モード）
python scripts/deploy/run_real_robot.py --model models/checkpoints/final_model.pth

# テストモード（モックセンサー/モーター）
python scripts/deploy/run_real_robot.py --model models/checkpoints/final_model.pth --mock

# カスタム走行時間（例: 1分間テスト）
python scripts/deploy/run_real_robot.py --model models/checkpoints/final_model.pth --duration 60 --mock

# GPIOピン番号のカスタマイズ
python scripts/deploy/run_real_robot.py \
  --model models/checkpoints/final_model.pth \
  --steering-pin 17 \
  --throttle-pin 18 \
  --lidar-port /dev/ttyUSB0
```

**オプション**:
- `--model`: 学習済みモデルのパス（必須）
- `--duration`: 走行時間（秒、デフォルト: 360）
- `--mock`: モックモードを使用（実機がない環境でのテスト用）
- `--device`: PyTorchデバイス（cpu/cuda/mps、デフォルト: cpu）
- `--lidar-port`: LiDARデバイスのポート（デフォルト: /dev/ttyUSB0）
- `--steering-pin`: ステアリングサーボのGPIOピン番号（デフォルト: 17）
- `--throttle-pin`: スロットルESCのGPIOピン番号（デフォルト: 18）

---

### 2. `run_6min_race.py` - シミュレーター検証（開発用）

**用途**: シミュレーター環境での最終検証

**特徴**:
- Box2D物理シミュレーション環境を使用
- コース定義ファイルが必要
- GUI表示でデバッグ可能
- ラップタイム記録

**使い方**:

```bash
# シミュレーターで6分間走行テスト
python scripts/deploy/run_6min_race.py \
  --model models/checkpoints/final_model.pth \
  --course courses/competition/real_course.json \
  --gui
```

---

## アーキテクチャ

### 観測空間（10次元）

実機・シミュレーター共通の観測空間:

```
[lidar_0, lidar_1, lidar_2, lidar_3, lidar_4,  # 5次元: 前方120度（-60° ~ +60°）
 vx, vy,                                        # 2次元: 速度
 angular_velocity,                              # 1次元: 角速度
 prev_steering, prev_throttle]                  # 2次元: 前回の行動
```

**重要**: チェックポイント情報は観測空間に含まれていません。エージェントはLiDARと速度情報のみで走行します。

### 行動空間（2次元）

```
[steering, throttle]  # 各次元 [-1.0, 1.0]
```

---

## 実機環境のセットアップ

### 1. ハードウェア要件

- **Raspberry Pi 4** (推奨: 4GB以上)
- **LiDAR**: RPLiDAR A1/A2 (USB経由)
- **IMU**: MPU6050/9250 (I2C経由)
- **モーター**: ステアリングサーボ + ESC
- **エンコーダー**: モーターエンコーダー（速度計測用）

### 2. 依存ライブラリのインストール

```bash
# Raspberry Pi上で実行
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install numpy

# LiDARドライバー（RPLiDAR用）
pip install rplidar-roboticia

# IMUドライバー（MPU6050用）
pip install smbus2

# GPIO制御
# （Raspberry Pi OSにデフォルトでインストール済み）
```

### 3. センサー・モーターの実装

現在、`src/deploy/sensor_interface.py`と`src/deploy/motor_interface.py`は抽象化層のみ実装されています。

実機のハードウェアに応じて、以下の部分を実装してください:

#### `RaspberryPiSensorInterface` (src/deploy/sensor_interface.py)

```python
# TODO部分を実装:
# - LiDARドライバーの初期化
# - IMU/エンコーダーの初期化
# - get_lidar_scan()の実装
# - get_velocity()の実装
# - get_angular_velocity()の実装
```

#### `RaspberryPiMotorInterface` (src/deploy/motor_interface.py)

```python
# TODO部分を実装:
# - GPIO PWMの初期化
# - set_control()の実装
# - PWMパルス幅の調整
```

---

## テスト方法

### 1. モックモードでのテスト

実機がない環境でも動作確認できます:

```bash
python scripts/deploy/run_real_robot.py \
  --model models/checkpoints/final_model.pth \
  --mock \
  --duration 10
```

### 2. センサーのみテスト

センサーインターフェースだけをテスト:

```python
from src.deploy.sensor_interface import RaspberryPiSensorInterface

sensor = RaspberryPiSensorInterface()
lidar_scan = sensor.get_lidar_scan()
vx, vy = sensor.get_velocity()
print(f"LiDAR: {lidar_scan[:5]}")
print(f"Velocity: ({vx}, {vy})")
```

### 3. モーターのみテスト

モーター制御だけをテスト:

```python
from src.deploy.motor_interface import RaspberryPiMotorInterface
import time

motor = RaspberryPiMotorInterface()

# 前進
motor.set_control(steering=0.0, throttle=0.5)
time.sleep(2)

# 停止
motor.stop()
motor.close()
```

---

## トラブルシューティング

### LiDARが接続できない

```bash
# デバイスを確認
ls -l /dev/ttyUSB*

# 権限を付与
sudo chmod 666 /dev/ttyUSB0

# または、ユーザーをdialoutグループに追加
sudo usermod -a -G dialout $USER
```

### I2C (IMU)が認識されない

```bash
# I2Cを有効化
sudo raspi-config
# Interface Options → I2C → Enable

# I2Cデバイスを確認
i2cdetect -y 1
```

### モデル推論が遅い

Raspberry Piでは推論速度が遅い場合があります:

```bash
# CPUのみで推論（--device cpu）
python scripts/deploy/run_real_robot.py --model ... --device cpu

# 推論の最適化:
# - ONNXに変換して軽量化
# - モデルを量子化（INT8）
```

---

## 次のステップ

1. **センサー・モーターの実装**: `src/deploy/sensor_interface.py`と`src/deploy/motor_interface.py`のTODO部分を実装
2. **実機テスト**: モックモードで動作確認後、実機で動作確認
3. **チューニング**: PWMパルス幅やセンサーノイズフィルタを調整
4. **最適化**: ONNX変換や量子化で推論速度を改善

---

## 参考

- プロジェクトルートの`CLAUDE.md`: プロジェクト全体の概要
- `src/env/minicar_env.py`: シミュレーター環境の実装
- `src/rl/ppo.py`: PPOアルゴリズムの実装
