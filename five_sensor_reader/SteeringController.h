/*
 * SteeringController.h
 *
 * ステアリング制御クラス（宣言）
 * Follow the Gap + P制御によるステアリング
 */

#ifndef STEERING_CONTROLLER_H
#define STEERING_CONTROLLER_H

#include <Arduino.h>

#include "Config.h"
#include "GapFinder.h"

class SteeringController {
   private:
    float _lastTargetAngle;  // 最後の目標角度（デバッグ用）

   public:
    SteeringController();

    // 初期化
    void begin();

    // ステアリング角度を計算（P制御）
    float calculate(const GapResult& gap);

    // 最後の目標角度を取得（デバッグ用）
    float getLastTargetAngle() const { return _lastTargetAngle; }

    // リセット
    void reset();
};

#endif  // STEERING_CONTROLLER_H
