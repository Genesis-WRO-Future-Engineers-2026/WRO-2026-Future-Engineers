/*
 * SensorConfig.h
 *
 * センサー構成定数の定義
 * - センサー数
 * - I2Cアドレス
 * - シャットダウンピン
 * - センサー角度
 */

#ifndef SENSOR_CONFIG_H
#define SENSOR_CONFIG_H

#include <Arduino.h>

// ============================================================================
// センサー構成定数
// ============================================================================

// センサー数
constexpr int NUM_SENSORS = 5;

// I2Cアドレス（初期化後に設定するアドレス）
// デフォルトアドレス0x29から変更される
inline const uint8_t* getSensorAddresses() {
  static const uint8_t addresses[NUM_SENSORS] = {
    0x30,  // Sensor 1 (左後)
    0x2B,  // Sensor 2 (左前)
    0x2D,  // Sensor 3 (正面)
    0x2E,  // Sensor 4 (右前)
    0x2F   // Sensor 5 (右後)
  };
  return addresses;
}

// シャットダウンピン（XSHUT）
// センサーの電源管理とI2Cアドレス設定に使用
inline const uint8_t* getShutdownPins() {
  static const uint8_t pins[NUM_SENSORS] = {
    2,  // Sensor 1
    3,  // Sensor 2
    4,  // Sensor 3
    5,  // Sensor 4
    6   // Sensor 5
  };
  return pins;
}

// センサー角度（度）
// 車体中心線を0°として、左を負、右を正とする
inline const float* getSensorAngles() {
  static const float angles[NUM_SENSORS] = {
    -70.0,  // Sensor 1 (左後)
    -20.0,  // Sensor 2 (左前)
      0.0,  // Sensor 3 (正面)
    +20.0,  // Sensor 4 (右前)
    +70.0   // Sensor 5 (右後)
  };
  return angles;
}

// センサー名（デバッグ用）
inline const char* const* getSensorNames() {
  static const char* names[NUM_SENSORS] = {
    "Left-Rear",   // Sensor 1
    "Left-Front",  // Sensor 2
    "Front",       // Sensor 3
    "Right-Front", // Sensor 4
    "Right-Rear"   // Sensor 5
  };
  return names;
}

// 便利なアクセサマクロ（後方互換性のため）
#define SENSOR_ADDRESSES (getSensorAddresses())
#define SHUTDOWN_PINS (getShutdownPins())
#define SENSOR_ANGLES (getSensorAngles())
#define SENSOR_NAMES (getSensorNames())

#endif // SENSOR_CONFIG_H
