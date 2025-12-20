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
public:
  // コンストラクタ
  SteeringController();

  // ステアリング角度を計算
  float calculate(const WallDetection& walls);
};

#endif // STEERING_CONTROLLER_H
