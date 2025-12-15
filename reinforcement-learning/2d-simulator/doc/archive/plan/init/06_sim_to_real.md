# Sim-to-Real転移戦略

## 1. 概要

シミュレーターで学習したポリシーを実機に転移する際の課題と対策をまとめる。

### 1.1 主要な課題

1. **物理パラメータの違い**
   - 摩擦係数、質量、慣性の不一致
   - モーター応答の遅延
   - タイヤのスリップ

2. **センサーノイズ**
   - LiDARの測定誤差
   - IMUのドリフト
   - レイテンシ（遅延）

3. **環境の違い**
   - 床面の状態（摩擦の変動）
   - 照明（LiDARには影響少）
   - 温度（モーター性能への影響）

4. **制御の違い**
   - 離散時間制御（サンプリング周波数）
   - アクチュエータの限界
   - 通信遅延

---

## 2. Domain Randomization戦略

### 2.1 物理パラメータのランダム化

学習時に以下のパラメータをエピソードごとにランダム化：

#### 摩擦係数
```python
friction_coefficient = np.random.uniform(0.5, 1.5)
# 理由: 床面の状態は変動する（ホコリ、湿度等）
```

#### 質量・慣性
```python
mass = base_mass * np.random.uniform(0.8, 1.2)
# 理由: バッテリー残量、パーツの取り付け誤差
```

#### モーター応答遅延
```python
motor_delay = np.random.uniform(0.0, 0.05)  # 0-50ms
# 理由: PWM制御、モーターの立ち上がり時間
```

#### モータートルクの変動
```python
motor_force = nominal_force * np.random.uniform(0.9, 1.1)
# 理由: 個体差、バッテリー電圧の変動
```

### 2.2 センサーノイズのランダム化

#### LiDARノイズ
```python
def add_lidar_noise(distances, noise_config):
    # ガウシアンノイズ
    noise_level = np.random.uniform(
        noise_config['min_noise'],
        noise_config['max_noise']
    )
    noise = np.random.normal(0, noise_level * max_range, distances.shape)
    noisy_distances = distances + noise

    # ドロップアウト（一部のレイが無効）
    dropout_prob = noise_config['dropout_prob']
    mask = np.random.random(distances.shape) > dropout_prob
    noisy_distances = np.where(mask, noisy_distances, max_range)

    # スパイクノイズ（外れ値）
    spike_prob = noise_config['spike_prob']
    spike_mask = np.random.random(distances.shape) < spike_prob
    noisy_distances = np.where(spike_mask, np.random.uniform(0, max_range), noisy_distances)

    return np.clip(noisy_distances, 0, max_range)
```

**推奨設定:**
```yaml
lidar_noise:
  min_noise: 0.005  # 距離の0.5%
  max_noise: 0.02   # 距離の2%
  dropout_prob: 0.05  # 5%のレイが無効
  spike_prob: 0.01    # 1%のレイが外れ値
```

#### IMUノイズ
```python
# 角速度ノイズ
angular_velocity_noisy = angular_velocity + np.random.normal(0, 0.01)

# ドリフト（長期的なバイアス）
imu_bias += np.random.normal(0, 0.0001)
angular_velocity_noisy += imu_bias
```

### 2.3 遅延のシミュレーション

#### センサー遅延
```python
class DelayedSensor:
    def __init__(self, delay_steps: int):
        self.delay_steps = delay_steps
        self.history = deque(maxlen=delay_steps + 1)

    def get_observation(self, current_obs):
        self.history.append(current_obs)
        if len(self.history) <= self.delay_steps:
            return current_obs  # 初期は遅延なし
        return self.history[0]  # 古い観測を返す
```

#### 制御遅延
```python
class DelayedActuator:
    def __init__(self, delay_steps: int):
        self.delay_steps = delay_steps
        self.action_queue = deque(maxlen=delay_steps + 1)

    def apply_action(self, action):
        self.action_queue.append(action)
        if len(self.action_queue) <= self.delay_steps:
            return np.zeros_like(action)  # 初期は動かない
        return self.action_queue[0]  # 古い行動を適用
```

**推奨設定:**
```yaml
delays:
  sensor_delay_steps: 1-2   # 10-20Hz → 50-100ms
  actuator_delay_steps: 1-2
```

---

## 3. 実機セットアップ

### 3.1 ハードウェア構成

#### Raspberry Pi 4のセットアップ
```bash
# OS: Raspberry Pi OS (64-bit)
# Python 3.9以上

# 必要なライブラリ
sudo apt-get update
sudo apt-get install -y python3-pip python3-opencv
pip3 install numpy onnxruntime
```

#### LiDAR接続
```python
# LD06 LiDARのセットアップ
import serial

class LD06LiDAR:
    def __init__(self, port='/dev/ttyUSB0', baudrate=230400):
        self.serial = serial.Serial(port, baudrate)

    def read_scan(self) -> np.ndarray:
        """1回転分のスキャンを読み取り"""
        # LD06のプロトコルに従ってパース
        ...
        return distances  # (360,) または (72,) にリサンプル
```

#### モーター制御
```python
import RPi.GPIO as GPIO
import pigpio

class MotorController:
    def __init__(self, pwm_pin_throttle, pwm_pin_steering):
        self.pi = pigpio.pi()
        self.throttle_pin = pwm_pin_throttle
        self.steering_pin = pwm_pin_steering

    def set_throttle(self, value: float):
        """スロットル設定 (0~1)"""
        pwm = int(1000 + value * 1000)  # 1000-2000us
        self.pi.set_servo_pulsewidth(self.throttle_pin, pwm)

    def set_steering(self, value: float):
        """ステアリング設定 (-1~1)"""
        pwm = int(1500 + value * 500)  # 1000-2000us
        self.pi.set_servo_pulsewidth(self.steering_pin, pwm)
```

### 3.2 モデルのデプロイ

#### PyTorch → ONNX変換
```python
# src/deploy/model_converter.py

def convert_to_onnx(policy_path: str, output_path: str):
    # モデルをロード
    policy = GaussianPolicy(obs_dim=77, action_dim=2)
    policy.load_state_dict(torch.load(policy_path))
    policy.eval()

    # ダミー入力
    dummy_input = torch.randn(1, 77)

    # ONNX変換
    torch.onnx.export(
        policy,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=11,
        input_names=['observation'],
        output_names=['action_mean', 'action_log_std'],
        dynamic_axes={
            'observation': {0: 'batch_size'},
            'action_mean': {0: 'batch_size'},
            'action_log_std': {0: 'batch_size'},
        }
    )
    print(f"Model exported to {output_path}")
```

#### ONNX Runtime推論
```python
# src/deploy/rpi_inference.py

import onnxruntime as ort

class ONNXPolicy:
    def __init__(self, model_path: str):
        self.session = ort.InferenceSession(model_path)
        self.input_name = self.session.get_inputs()[0].name

    def predict(self, observation: np.ndarray) -> np.ndarray:
        """
        Args:
            observation: (77,)
        Returns:
            action: (2,) [steering, throttle]
        """
        obs = observation.reshape(1, -1).astype(np.float32)
        outputs = self.session.run(None, {self.input_name: obs})

        action_mean = outputs[0][0]  # (2,)
        # 実機では平均値を使用（探索なし）
        return action_mean
```

### 3.3 実機制御ループ
```python
# scripts/run_real_robot.py

def main():
    # ハードウェア初期化
    lidar = LD06LiDAR()
    motor = MotorController(pwm_pin_throttle=18, pwm_pin_steering=19)

    # ポリシーロード
    policy = ONNXPolicy("models/best/policy.onnx")

    # 状態保持
    last_action = np.zeros(2)
    velocity = np.zeros(2)

    # 制御ループ (20Hz)
    rate = 20  # Hz
    dt = 1.0 / rate

    while True:
        start_time = time.time()

        # センサー読み取り
        lidar_scan = lidar.read_scan()  # (72,)

        # 速度推定（簡易的）
        velocity = estimate_velocity()  # IMUまたはオドメトリから

        # 観測作成
        observation = np.concatenate([
            lidar_scan,
            velocity,
            [0.0],  # 角速度（IMUから取得）
            last_action,
        ])

        # 推論
        action = policy.predict(observation)

        # 制御適用
        motor.set_steering(action[0])
        motor.set_throttle(action[1])

        last_action = action

        # 周期維持
        elapsed = time.time() - start_time
        time.sleep(max(0, dt - elapsed))
```

---

## 4. 実機キャリブレーション

### 4.1 センサーキャリブレーション

#### LiDARキャリブレーション
```python
def calibrate_lidar():
    """LiDARのオフセットとスケールを調整"""
    # 既知の距離に壁を設置
    true_distances = [1.0, 2.0, 3.0, 5.0]  # m

    measured_distances = []
    for true_dist in true_distances:
        input(f"壁を{true_dist}mに設置してEnter")
        scan = lidar.read_scan()
        measured_distances.append(np.median(scan))

    # 線形回帰でスケールとオフセットを求める
    from scipy.stats import linregress
    slope, intercept, _, _, _ = linregress(measured_distances, true_distances)

    print(f"Scale: {slope}, Offset: {intercept}")
    return slope, intercept

# 使用時
lidar_scan_calibrated = lidar_scan * scale + offset
```

#### IMUキャリブレーション
```python
def calibrate_imu(num_samples=1000):
    """静止状態でIMUのバイアスを測定"""
    gyro_readings = []

    print("車両を静止させてください...")
    time.sleep(2)

    for _ in range(num_samples):
        gyro = imu.read_gyro()
        gyro_readings.append(gyro)
        time.sleep(0.01)

    bias = np.mean(gyro_readings, axis=0)
    print(f"Gyro bias: {bias}")
    return bias
```

### 4.2 モーターキャリブレーション

#### スロットル応答の測定
```python
def calibrate_throttle():
    """スロットル入力と実際の速度の関係を測定"""
    throttle_inputs = np.linspace(0, 1, 10)
    measured_speeds = []

    for throttle in throttle_inputs:
        motor.set_throttle(throttle)
        time.sleep(2)  # 安定するまで待機

        # 速度測定（オドメトリまたは外部計測）
        speed = measure_speed()
        measured_speeds.append(speed)

        motor.set_throttle(0)
        time.sleep(1)

    # プロット
    plt.plot(throttle_inputs, measured_speeds)
    plt.xlabel('Throttle Input')
    plt.ylabel('Speed (m/s)')
    plt.savefig('throttle_calibration.png')
```

#### ステアリング応答の測定
```python
def calibrate_steering():
    """ステアリング入力と旋回半径の関係を測定"""
    steering_inputs = np.linspace(-1, 1, 10)
    turn_radii = []

    for steering in steering_inputs:
        motor.set_steering(steering)
        motor.set_throttle(0.5)

        # 円を描いて旋回半径を測定
        radius = measure_turn_radius()
        turn_radii.append(radius)

        motor.set_throttle(0)
        time.sleep(1)

    plt.plot(steering_inputs, turn_radii)
    plt.xlabel('Steering Input')
    plt.ylabel('Turn Radius (m)')
    plt.savefig('steering_calibration.png')
```

---

## 5. 段階的な転移プロセス

### Phase 1: シミュレーターの調整
1. 実機でセンサーデータを収集
2. シミュレーターのパラメータを実機に近づける
3. Domain Randomizationの範囲を調整

### Phase 2: 安全な環境でテスト
1. 広いスペースでゆっくり走行
2. 衝突しても安全な環境
3. ポリシーの動作を観察

### Phase 3: Fine-tuning（オプション）
1. 実機で追加学習（少量のエピソード）
2. シミュレーター + 実機のハイブリッド学習
3. ポリシーの微調整

### Phase 4: 本番環境でのテスト
1. 実際のコースで評価
2. 複数回のトライアル
3. 安定性の確認

---

## 6. トラブルシューティング

### 6.1 実機での一般的な問題

#### 問題1: 実機で動きが不安定
**原因:**
- センサーノイズが想定より大きい
- 制御周波数が不足
- モーター応答が遅い

**対策:**
```python
# センサーデータの移動平均
lidar_scan = moving_average(lidar_scan, window=3)

# 制御周波数を上げる
rate = 30  # 20Hz → 30Hz

# モーターの最大トルクを制限
max_throttle = 0.7  # 1.0 → 0.7
```

#### 問題2: 壁に衝突する
**原因:**
- LiDARの精度不足
- 安全マージンが小さい
- 遅延の影響

**対策:**
```python
# 安全マージンを増やす
def add_safety_margin(action, min_distance):
    if min_distance < 0.5:  # 50cm以内
        # スロットルを減らす
        action[1] *= 0.5
    return action
```

#### 問題3: 推論速度が遅い
**原因:**
- モデルサイズが大きい
- ONNX Runtimeの最適化不足

**対策:**
```python
# ONNX Runtimeの最適化
session_options = ort.SessionOptions()
session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
session = ort.InferenceSession(model_path, session_options)

# モデルの軽量化
# - ネットワークサイズを削減（256→128）
# - 量子化（FP32 → FP16 or INT8）
```

### 6.2 安全対策

#### 緊急停止機能
```python
class EmergencyStop:
    def __init__(self, min_safe_distance=0.2):
        self.min_safe_distance = min_safe_distance

    def should_stop(self, lidar_scan) -> bool:
        """緊急停止が必要か判定"""
        min_distance = np.min(lidar_scan)
        return min_distance < self.min_safe_distance

# 使用
emergency_stop = EmergencyStop()
if emergency_stop.should_stop(lidar_scan):
    motor.set_throttle(0)
    motor.set_steering(0)
    print("Emergency stop!")
```

#### リモート停止
```python
# キーボードからの停止
import threading

stop_flag = False

def listen_keyboard():
    global stop_flag
    input("Press Enter to stop...")
    stop_flag = True

threading.Thread(target=listen_keyboard, daemon=True).start()

# メインループ内
if stop_flag:
    motor.set_throttle(0)
    break
```

---

## 7. 評価指標

### 7.1 シミュレーター vs 実機

| 指標 | シミュレーター目標 | 実機目標 |
|------|-------------------|----------|
| 完走率 | 90%以上 | 70%以上 |
| 平均ラップタイム | - | ±20%以内 |
| 壁との最小距離 | >10cm | >20cm |
| 安定性（標準偏差） | 低い | 中程度 |

### 7.2 ログとモニタリング

```python
class PerformanceLogger:
    def __init__(self):
        self.episodes = []

    def log_episode(self, success, time, min_distance):
        self.episodes.append({
            'success': success,
            'time': time,
            'min_distance': min_distance,
        })

    def get_statistics(self):
        success_rate = np.mean([e['success'] for e in self.episodes])
        avg_time = np.mean([e['time'] for e in self.episodes if e['success']])
        avg_min_distance = np.mean([e['min_distance'] for e in self.episodes])

        return {
            'success_rate': success_rate,
            'avg_time': avg_time,
            'avg_min_distance': avg_min_distance,
        }
```

---

## まとめ

Sim-to-Real転移は段階的に進めることが重要です。Domain Randomizationを適切に実装し、実機でのキャリブレーションを丁寧に行うことで、シミュレーターで学習したポリシーを実機に効果的に転移できます。
