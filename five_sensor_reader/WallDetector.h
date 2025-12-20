/*
 * WallDetector.h
 *
 * 壁検出クラス（宣言）
 * センサーデータから壁の位置を計算
 */

#ifndef WALL_DETECTOR_H
#define WALL_DETECTOR_H

#include <Arduino.h>
#include "Config.h"
#include "SensorReader.h"

// 壁検出結果
struct WallDetection {
  bool left_valid;
  bool right_valid;
  float left_intersection;
  float right_intersection;
};

class WallDetector {
private:
  // センサー値の有効性チェック
  bool isSensorValid(uint16_t distance) const;

  // 2つのセンサーから壁の直線を検出し、y軸との交点を計算
  bool calculateIntersection(
    uint16_t d1, uint8_t sensor_idx1,
    uint16_t d2, uint8_t sensor_idx2,
    float* intersection
  );

public:
  // コンストラクタ
  WallDetector();

  // 壁検出を実行
  WallDetection detect(const SensorData* sensorData);
};

#endif // WALL_DETECTOR_H
