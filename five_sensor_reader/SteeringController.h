/*
 * SteeringController.h
 *
 * ステアリング制御クラス（宣言）
 * 壁検出結果からステアリング角度を計算
 */

#ifndef STEERING_CONTROLLER_H
#define STEERING_CONTROLLER_H

#include <Arduino.h>
#include "Config.h"
#include "WallDetector.h"

class SteeringController {
private:
  // センサーデータへの参照（制約チェック用）
  const SensorData* lastSensorData;

public:
  // コンストラクタ
  SteeringController();

  // ステアリング角度を計算
  float calculate(const WallDetection& walls, const SensorData* sensorData);
};

#endif // STEERING_CONTROLLER_H
