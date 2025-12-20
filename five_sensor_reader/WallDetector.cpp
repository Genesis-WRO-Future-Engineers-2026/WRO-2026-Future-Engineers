/*
 * WallDetector.cpp
 *
 * 壁検出クラス（実装）
 */

#include "WallDetector.h"

WallDetector::WallDetector() {
  // 何もしない
}

bool WallDetector::isSensorValid(uint16_t distance) const {
  return (distance > MIN_VALID_DISTANCE &&
          distance < RELIABLE_RANGE &&
          distance != SENSOR_ERROR_VALUE);
}

bool WallDetector::calculateIntersection(
  uint16_t d1, uint8_t sensor_idx1,
  uint16_t d2, uint8_t sensor_idx2,
  float* intersection
) {
  // センサー値の有効性チェック
  if (!isSensorValid(d1) || !isSensorValid(d2)) {
    return false;
  }

  // センサーペア間の差が大きすぎる場合は無効
  if (abs((int)d1 - (int)d2) > MAX_SENSOR_DIFF) {
    return false;
  }

  // LUTから三角関数値を取得（高速化）
  float x1 = d1 * COS_ANGLES[sensor_idx1];
  float y1 = d1 * SIN_ANGLES[sensor_idx1];
  float x2 = d2 * COS_ANGLES[sensor_idx2];
  float y2 = d2 * SIN_ANGLES[sensor_idx2];

  // 2点から直線方程式の係数を計算: ax + by + c = 0
  float a = y2 - y1;
  float b = x1 - x2;
  float c = x2 * y1 - x1 * y2;

  // bが0に近い場合（垂直な壁）は無効
  if (abs(b) < EPSILON_VERTICAL) {
    return false;
  }

  // y軸（x=0）との交点を計算: y = -c / b
  *intersection = -c / b;

  return true;
}

WallDetection WallDetector::detect(const SensorData* sensorData) {
  WallDetection result;

  // 左壁検出（センサー0: -70°、センサー1: -20°）
  result.left_valid = calculateIntersection(
    sensorData[0].distance, 0,
    sensorData[1].distance, 1,
    &result.left_intersection
  );

  // 右壁検出（センサー3: +20°、センサー4: +70°）
  result.right_valid = calculateIntersection(
    sensorData[3].distance, 3,
    sensorData[4].distance, 4,
    &result.right_intersection
  );

  return result;
}
