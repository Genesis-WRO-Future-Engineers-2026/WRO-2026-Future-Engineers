/*
 * SteeringController.h
 *
 * ステアリング制御クラス（宣言）
 * Follow the Gap + PD制御によるステアリング
 */

#ifndef STEERING_CONTROLLER_H
#define STEERING_CONTROLLER_H

#include <Arduino.h>

#include "Config.h"
#include "GapFinder.h"

// 前方宣言（ポインタ型のみ使用のためフルインクルード不要）
struct SensorData;

class SteeringController {
   private:
    float _lastTargetAngle;  // 最後の目標角度（D項計算用）

   public:
    SteeringController();

    // 初期化
    void begin();

    // ステアリング角度を計算（PD制御）
    float calculate(const GapResult& gap, const SensorData* sensorData);

    // 最後の目標角度を取得（デバッグ用）
    float getLastTargetAngle() const { return _lastTargetAngle; }

    // リセット
    void reset();
};

#endif  // STEERING_CONTROLLER_H
