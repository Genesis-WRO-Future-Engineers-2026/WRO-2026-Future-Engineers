/*
 * five_sensor_reader.ino
 *
 * 5つのVL53L0Xセンサーから距離データを読み取り、
 * 壁追従アルゴリズムでステアリングサーボとモーターを制御
 *
 * 接続:
 * - TCA9548A I2Cマルチプレクサ (アドレス: 0x70)
 * - VL53L0Xセンサー → マルチプレクサのチャンネル0, 1, 2, 3, 4に接続
 * - サーボモーター → Pin 9
 * - ESC → Pin 10
 *
 * 使用方法:
 * 1. Arduino IDEでこのファイルを開く
 * 2. 必要なライブラリをインストール:
 *    - Adafruit_VL53L0X
 *    - Servo (Arduino標準ライブラリ)
 * 3. Arduino Nano R4に書き込み
 * 4. シリアルモニタ（9600bps）で確認
 */

#include <Wire.h>
#include <Servo.h>
#include "Adafruit_VL53L0X.h"

// ============================================================================
// デバッグモード設定
// ============================================================================
// true: PWM出力なし（デバッグ用）、false: PWM出力あり（実機制御）
#define DEBUG_MODE false

// デバッグモードに応じてシリアルプリントを制御するマクロ
#if DEBUG_MODE
  #define DEBUG_PRINT(x) Serial.print(x)
  #define DEBUG_PRINTLN(x) Serial.println(x)
#else
  #define DEBUG_PRINT(x)
  #define DEBUG_PRINTLN(x)
#endif

// ============================================================================
// TCA9548Aマルチプレクサ設定
// ============================================================================
#define TCA9548A_ADDR 0x70

// ============================================================================
// センサー設定
// ============================================================================
#define NUM_SENSORS 5

// 各センサーが接続されているチャンネル
const uint8_t sensorChannels[NUM_SENSORS] = {0, 1, 2, 3, 4};

// VL53L0Xセンサーオブジェクトの配列
Adafruit_VL53L0X sensors[NUM_SENSORS];

// 測定データの配列
VL53L0X_RangingMeasurementData_t measurements[NUM_SENSORS];

// サーボオブジェクト
Servo steeringServo;  // ステアリング用サーボ
Servo escController;  // ESC用

// ============================================================================
// 測定間隔設定
// ============================================================================
const unsigned long MEASUREMENT_INTERVAL = 100;  // 100ms = 10Hz

// ============================================================================
// センサー配置（角度）
// ============================================================================
const float SENSOR_ANGLES[NUM_SENSORS] = {-70.0, -20.0, 0.0, 20.0, 70.0};  // 度数法
// DEG_TO_RADはArduino標準ライブラリで定義済み

// ============================================================================
// ステアリング制御パラメータ
// ============================================================================
const float GAIN_FACTOR = 0.1;              // ステアリング応答ゲイン
const float MAX_STEERING_ANGLE = 30.0;      // 最大操舵角（度）
const float OPEN_SIDE_RATIO = 0.5;          // 片側開放時の操舵比率

// ============================================================================
// センサー信頼性パラメータ
// ============================================================================
const int RELIABLE_RANGE = 700;             // 信頼できる測定範囲（mm）
const int MAX_SENSOR_DIFF = 200;            // センサーペア間の最大許容差（mm）

// ============================================================================
// PWM出力設定
// ============================================================================
const int SERVO_PIN = 9;                    // サーボモーター（ステアリング）
const int ESC_PIN = 10;                     // ESC（モーター制御）

// サーボ: 500-2400μs範囲で±90°ステアリング
const int SERVO_CENTER = 1500;              // 中央位置（μs）
const int SERVO_MIN = 500;                  // 最小パルス幅（μs）
const int SERVO_MAX = 2400;                 // 最大パルス幅（μs）

// ESC: 1000-2000μs範囲（実際の最大前進は1400μs）
const float BASE_SPEED_PULSE = 1.5;        // 基本速度（ms）
const float MAX_SPEED_PULSE = 1.4;          // 最大速度（ms）
const float STOP_SPEED_PULSE = 1.5;         // 停止（ms）

// ============================================================================
// 壁検出結果を格納する構造体
// ============================================================================
struct WallDetection {
  bool left_valid;
  bool right_valid;
  float left_intersection;
  float right_intersection;
};

// ============================================================================
// ヘルパー関数
// ============================================================================

/**
 * TCA9548Aマルチプレクサのチャンネルを選択
 */
void tcaSelect(uint8_t channel) {
  if (channel > 7) return;

  Wire.beginTransmission(TCA9548A_ADDR);
  Wire.write(1 << channel);
  Wire.endTransmission();
}

/**
 * センサー測定値が有効かチェック
 */
bool isSensorValid(uint16_t distance) {
  return (distance > 50 && distance < RELIABLE_RANGE && distance != 65535);
}

/**
 * 2つのセンサーから壁の直線を検出し、y軸との交点を計算
 *
 * @param d1 センサー1の距離（mm）
 * @param angle1 センサー1の角度（度）
 * @param d2 センサー2の距離（mm）
 * @param angle2 センサー2の角度（度）
 * @param intersection y軸交点の結果を格納するポインタ
 * @return 壁検出が有効かどうか
 */
bool calculateWallIntersection(uint16_t d1, float angle1, uint16_t d2, float angle2, float* intersection) {
  // センサー値の有効性チェック
  if (!isSensorValid(d1) || !isSensorValid(d2)) {
    return false;
  }

  // センサーペア間の差が大きすぎる場合は無効
  if (abs((int)d1 - (int)d2) > MAX_SENSOR_DIFF) {
    return false;
  }

  // 極座標→直交座標変換
  float theta1 = angle1 * DEG_TO_RAD;
  float theta2 = angle2 * DEG_TO_RAD;

  float x1 = d1 * cos(theta1);
  float y1 = d1 * sin(theta1);
  float x2 = d2 * cos(theta2);
  float y2 = d2 * sin(theta2);

  // 2点から直線方程式の係数を計算: ax + by + c = 0
  float a = y2 - y1;
  float b = x1 - x2;
  float c = x2 * y1 - x1 * y2;

  // bが0に近い場合（垂直な壁）は無効
  if (abs(b) < 0.001) {
    return false;
  }

  // y軸（x=0）との交点を計算: y = -c / b
  *intersection = -c / b;

  return true;
}

/**
 * 全センサーから壁を検出
 */
WallDetection detectWalls() {
  WallDetection result;

  // 左壁検出（センサー0: -70°、センサー1: -20°）
  result.left_valid = calculateWallIntersection(
    measurements[0].RangeMilliMeter, SENSOR_ANGLES[0],
    measurements[1].RangeMilliMeter, SENSOR_ANGLES[1],
    &result.left_intersection
  );

  // 右壁検出（センサー3: +20°、センサー4: +70°）
  result.right_valid = calculateWallIntersection(
    measurements[3].RangeMilliMeter, SENSOR_ANGLES[3],
    measurements[4].RangeMilliMeter, SENSOR_ANGLES[4],
    &result.right_intersection
  );

  return result;
}

/**
 * 壁検出結果からステアリング角度を計算
 */
float calculateSteeringAngle(WallDetection walls) {
  float steering_angle = 0.0;

  if (walls.left_valid && walls.right_valid) {
    // 状態1: 両壁検出 → 交点差に比例したステアリング
    float intersection_diff = walls.left_intersection - walls.right_intersection;
    steering_angle = intersection_diff * GAIN_FACTOR;
  }
  else if (walls.left_valid && !walls.right_valid) {
    // 状態2: 左壁のみ → 左へステアリング（開けた方向へ）
    steering_angle = -MAX_STEERING_ANGLE * OPEN_SIDE_RATIO;
  }
  else if (!walls.left_valid && walls.right_valid) {
    // 状態3: 右壁のみ → 右へステアリング（開けた方向へ）
    steering_angle = MAX_STEERING_ANGLE * OPEN_SIDE_RATIO;
  }
  else {
    // 状態4: 壁なし → 直進
    steering_angle = 0.0;
  }

  // 最大操舵角でクランプ
  if (steering_angle > MAX_STEERING_ANGLE) {
    steering_angle = MAX_STEERING_ANGLE;
  } else if (steering_angle < -MAX_STEERING_ANGLE) {
    steering_angle = -MAX_STEERING_ANGLE;
  }

  return steering_angle;
}

/**
 * ステアリング角度をサーボパルス幅に変換して出力
 *
 * @param angle_degrees ステアリング角度（-90 ～ +90度）
 */
// TODO: パルスとアングル修正
void setSteeringAngle(float angle_degrees) {
  // 角度をパルス幅に変換（-90° → 500μs、0° → 1500μs、+90° → 2400μs）
  int pulse_us = map((int)(angle_degrees * 10), -900, 900, SERVO_MIN, SERVO_MAX);

  // 範囲チェック
  if (pulse_us < SERVO_MIN) pulse_us = SERVO_MIN;
  if (pulse_us > SERVO_MAX) pulse_us = SERVO_MAX;

  // PWM出力
  if (!DEBUG_MODE) {
    steeringServo.writeMicroseconds(pulse_us);
  }

  // デバッグ出力
  DEBUG_PRINT("  [Servo: ");
  DEBUG_PRINT(pulse_us);
  DEBUG_PRINT("us");
  if (DEBUG_MODE) DEBUG_PRINT(" (sim)");
  DEBUG_PRINT("]");
}

/**
 * ESC速度を設定
 *
 * @param speed_pulse 速度パルス幅（ms）
 */
void setSpeed(float speed_pulse) {
  // msをμsに変換
  int pulse_us = (int)(speed_pulse * 1000);

  // 範囲チェック（1000-2000μs）
  if (pulse_us < 1000) pulse_us = 1000;
  if (pulse_us > 2000) pulse_us = 2000;

  // PWM出力
  if (!DEBUG_MODE) {
    escController.writeMicroseconds(pulse_us);
  }

  // デバッグ出力
  DEBUG_PRINT("  [ESC: ");
  DEBUG_PRINT(speed_pulse);
  DEBUG_PRINT("ms");
  if (DEBUG_MODE) DEBUG_PRINT(" (sim)");
  DEBUG_PRINT("]");
}

// ============================================================================
// Setup関数
// ============================================================================
void setup() {
  // シリアル通信開始
  Serial.begin(9600);
  Wire.begin();

  DEBUG_PRINTLN("==========================================");
  DEBUG_PRINTLN("  5-Sensor Wall Following System");
  DEBUG_PRINTLN("==========================================");
  DEBUG_PRINT("Debug Mode: ");
  DEBUG_PRINTLN(DEBUG_MODE ? "ON (No PWM)" : "OFF (PWM Active)");
  DEBUG_PRINTLN();

  // PWM出力ピンを初期化
  if (!DEBUG_MODE) {
    steeringServo.attach(SERVO_PIN);
    escController.attach(ESC_PIN);

    // 初期位置に設定（中央ステアリング、停止状態）
    steeringServo.writeMicroseconds(SERVO_CENTER);
    escController.writeMicroseconds((int)(STOP_SPEED_PULSE * 1000));

    DEBUG_PRINTLN("PWM outputs initialized:");
    DEBUG_PRINT("  Servo: Pin ");
    DEBUG_PRINTLN(SERVO_PIN);
    DEBUG_PRINT("  ESC: Pin ");
    DEBUG_PRINTLN(ESC_PIN);
    DEBUG_PRINTLN();
  }

  // 全センサーを初期化
  DEBUG_PRINTLN("Initializing sensors...");
  for (int i = 0; i < NUM_SENSORS; ++i) {
    tcaSelect(sensorChannels[i]);
    delay(1000);

    DEBUG_PRINT("  Sensor ");
    DEBUG_PRINT(i);
    DEBUG_PRINT(" (Ch");
    DEBUG_PRINT(sensorChannels[i]);
    DEBUG_PRINT(", ");
    DEBUG_PRINT(SENSOR_ANGLES[i]);
    DEBUG_PRINT("deg)...");

    if (!sensors[i].begin()) {
      DEBUG_PRINTLN("FAILED!");
      DEBUG_PRINT("Check sensor ");
      DEBUG_PRINT(i);
      DEBUG_PRINTLN(" connections!");
      while (1);
    }

    DEBUG_PRINTLN("OK!");
  }

  DEBUG_PRINTLN();
  DEBUG_PRINTLN("Initialization complete!");
  DEBUG_PRINTLN("Starting wall-following control...\n");
}

// ============================================================================
// Loop関数
// ============================================================================
void loop() {
  static unsigned long lastMeasurement = 0;
  unsigned long currentTime = millis();

  // 指定した間隔で測定
  if (currentTime - lastMeasurement >= MEASUREMENT_INTERVAL) {
    lastMeasurement = currentTime;

    // フェーズ1: センサーデータ取得
    for (int i = 0; i < NUM_SENSORS; ++i) {
      tcaSelect(sensorChannels[i]);
      sensors[i].rangingTest(&measurements[i], false);
    }

    // センサーデータ表示
    for (int i = 0; i < NUM_SENSORS; ++i) {
      DEBUG_PRINT("Ch");
      DEBUG_PRINT(sensorChannels[i]);
      DEBUG_PRINT(": ");

      if (measurements[i].RangeStatus != 4) {
        DEBUG_PRINT(measurements[i].RangeMilliMeter);
        DEBUG_PRINT(" mm");
      } else {
        DEBUG_PRINT("Out of range");
      }

      if (i < NUM_SENSORS - 1) {
        DEBUG_PRINT("  |  ");
      }
    }

    // フェーズ2: 壁検出
    WallDetection walls = detectWalls();

    // フェーズ3: ステアリング角度計算
    float steering_angle = calculateSteeringAngle(walls);

    // デバッグ情報表示
    DEBUG_PRINT("  | L:");
    DEBUG_PRINT(walls.left_valid ? "OK" : "NG");
    DEBUG_PRINT(" R:");
    DEBUG_PRINT(walls.right_valid ? "OK" : "NG");
    DEBUG_PRINT(" | Steer:");
    DEBUG_PRINT(steering_angle);
    DEBUG_PRINT("deg");

    // フェーズ4: アクチュエーター制御
    setSteeringAngle(steering_angle);
    setSpeed(BASE_SPEED_PULSE);

    DEBUG_PRINTLN();
  }
}
