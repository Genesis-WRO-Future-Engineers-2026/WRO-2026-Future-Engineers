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
  float left_intersection;    // y軸との交点（mm）
  float right_intersection;   // y軸との交点（mm）
  float left_angle;           // 壁の角度（度）
  float right_angle;          // 壁の角度（度）
  float left_distance;        // 車体中心から左壁までの最短距離（mm）
  float right_distance;       // 車体中心から右壁までの最短距離（mm）
};

class WallDetector {
private:
  // センサー値の有効性チェック
  bool isSensorValid(uint16_t distance) const;

  // 2つのセンサーから壁の直線を検出し、y軸との交点、角度、距離を計算
  bool calculateIntersection(
    uint16_t d1, uint8_t sensor_idx1,
    uint16_t d2, uint8_t sensor_idx2,
    float* intersection,
    float* wall_angle,
    float* wall_distance
  );

public:
  // コンストラクタ
  WallDetector();

  // 壁検出を実行
  WallDetection detect(const SensorData* sensorData);
};

#endif // WALL_DETECTOR_H
