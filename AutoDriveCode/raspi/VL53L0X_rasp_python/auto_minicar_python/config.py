"""
設定ファイル - GPIO ピン番号と制御パラメータ
"""

# GPIO ピン番号設定
# センサー用シャットダウンピン
SENSOR1_SHUTDOWN = 20  # センサー1 (20度)
SENSOR2_SHUTDOWN = 21  # センサー2 (70度)

# サーボとESCのGPIOピン
SERVO_PIN = 12  # サーボ用GPIO 12
ESC_PIN = 13    # ESC用GPIO 13

# センサーI2Cアドレス
SENSOR1_ADDRESS = 0x2B  # センサー1のI2Cアドレス
SENSOR2_ADDRESS = 0x2D  # センサー2のI2Cアドレス

# センサー角度設定
SENSOR1_ANGLE = 20  # センサー1の取り付け角度（度）
SENSOR2_ANGLE = 70  # センサー2の取り付け角度（度）

# 壁追従制御パラメータ
PARALLEL_ANGLE = 110.0      # 壁と平行時の基準角度（度）
ANGLE_TOLERANCE = 2.0       # 角度の許容誤差（度）
TARGET_DISTANCE = 200.0     # 壁までの目標距離（mm）
DISTANCE_TOLERANCE = 20.0   # 距離の許容誤差（mm）

# ステアリング制御パラメータ
COUNTER_STEER_ANGLE = 30  # カウンターステア角度（度）
NEUTRAL_ANGLE = 0         # ニュートラル角度（直進）

# モーター速度パラメータ
SPEED_PULSE = 1.52   # 前進速度（パルス幅 ms）
STOP_PULSE = 1.5     # 停止（パルス幅 ms）

# PWM周波数
PWM_FREQUENCY = 50   # PWM周波数（Hz）

# サーボパルス幅範囲
SERVO_MIN_PULSE_WIDTH_MS = 0.5   # 最小パルス幅（ms）
SERVO_MAX_PULSE_WIDTH_MS = 2.4   # 最大パルス幅（ms）

# 測定パラメータ
DEFAULT_ITERATIONS = 100  # デフォルトの測定回数
MIN_TIMING = 20000        # 最小タイミング（マイクロ秒）

# 動的ステアリング制御パラメータ
# ====================================

# 比例ゲイン（誤差に対する操舵角の応答性）
DISTANCE_GAIN = 0.15        # deg/mm - 距離誤差への応答
ANGLE_GAIN = 1.5            # deg/deg - 角度誤差への応答

# 制御の重み付け（距離優先）
DISTANCE_WEIGHT = 2.0       # 距離制御の重み
ANGLE_WEIGHT = 1.0          # 角度制御の重み

# ステアリング制限
MAX_STEER_ANGLE = 30        # 最大操舵角（度）
MIN_STEER_ANGLE = 2         # 最小操舵角閾値（度）※小さすぎる角度は無視

# デッドゾーン（誤差がこの範囲内なら補正しない）
DISTANCE_DEADZONE = 5.0     # mm
ANGLE_DEADZONE = 1.0        # 度
