/*
 * SteeringController.h
 *
 * ステアリング制御クラス（宣言）
 * Follow the Gap + Pure Pursuit制御によるステアリング
 */

#ifndef STEERING_CONTROLLER_H
#define STEERING_CONTROLLER_H

#include <Arduino.h>

#include "Config.h"
#include "GapFinder.h"

class SteeringController {
   public:
    SteeringController();

    // 初期化
    void begin();

    // ステアリング角度を計算（Pure Pursuit）
    float calculate(const GapResult& gap, const SensorData* sensorData);
};

#endif  // STEERING_CONTROLLER_H
