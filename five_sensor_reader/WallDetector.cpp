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
  float* intersection,
  float* wall_angle,
  float* wall_distance
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

  // 壁の角度を計算（幾何学的に正しい方法）
  // 直線 ax + by + c = 0 の傾き m = -a/b
  // 壁の角度（ラジアン）= atan2(a, -b)
  // 度数法に変換: degrees = radians * 180 / PI
  float angle_rad = atan2(a, -b);
  *wall_angle = angle_rad * 180.0 / PI;

  // 車体中心（原点）から壁までの最短距離を計算
  // 点 (x0, y0) と直線 ax + by + c = 0 の距離: |ax0 + by0 + c| / sqrt(a² + b²)
  // 車体中心が原点 (0, 0) なので: |c| / sqrt(a² + b²)
  float denominator = sqrt(a * a + b * b);
  if (denominator > 0.001) {  // ゼロ除算防止
    *wall_distance = abs(c) / denominator;
  } else {
    *wall_distance = 9999.0;  // 無効な値
  }

  return true;
}

WallDetection WallDetector::detect(const SensorData* sensorData) {
  WallDetection result;

  // 左壁検出（センサー0: -70°、センサー1: -20°）
  result.left_valid = calculateIntersection(
    sensorData[0].distance, 0,
    sensorData[1].distance, 1,
    &result.left_intersection,
    &result.left_angle,
    &result.left_distance
  );

  // 右壁検出（センサー3: +20°、センサー4: +70°）
  result.right_valid = calculateIntersection(
    sensorData[3].distance, 3,
    sensorData[4].distance, 4,
    &result.right_intersection,
    &result.right_angle,
    &result.right_distance
  );

  return result;
}
