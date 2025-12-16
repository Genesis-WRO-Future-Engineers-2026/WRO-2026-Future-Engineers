/*
 * SensorData.h
 *
 * センサーデータ構造体の定義
 * 1つのセンサーの測定結果を保持
 */

#ifndef SENSOR_DATA_H
#define SENSOR_DATA_H

#include <Arduino.h>

// ============================================================================
// SensorData構造体 - 1つのセンサーの測定データ
// ============================================================================
struct SensorData {
  uint8_t id;              // センサーID (0-4)
  float angle;             // センサー角度（度）
  uint16_t distance;       // 測定距離（mm）
  bool isValid;            // 測定値の有効性
  uint8_t rangeStatus;     // VL53L0Xのステータスコード
                           // 0: 正常測定
                           // 1: Sigma fail (測定精度が低い)
                           // 2: Signal fail (信号が弱い)
                           // 4: Out of range (測定範囲外)
                           // 5: Hardware fail (ハードウェア異常)

  // デフォルトコンストラクタ
  SensorData()
    : id(0),
      angle(0.0),
      distance(0),
      isValid(false),
      rangeStatus(255) {
  }

  // パラメータ付きコンストラクタ
  SensorData(uint8_t _id, float _angle)
    : id(_id),
      angle(_angle),
      distance(0),
      isValid(false),
      rangeStatus(255) {
  }

  // 測定値が信頼できるかチェック
  bool isReliable() const {
    return isValid && (rangeStatus == 0);
  }

  // 測定範囲外かチェック
  bool isOutOfRange() const {
    return rangeStatus == 4;
  }

  // ハードウェア異常かチェック
  bool hasHardwareError() const {
    return rangeStatus == 5;
  }
};

#endif // SENSOR_DATA_H
