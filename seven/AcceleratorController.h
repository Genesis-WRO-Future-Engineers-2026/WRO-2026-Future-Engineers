/*
 * AcceleratorController.h
 *
 * アクセル制御クラス（宣言）
 * ステアリング角度に応じた速度制御
 */

#ifndef ACCELERATOR_CONTROLLER_H
#define ACCELERATOR_CONTROLLER_H

#include <Arduino.h>

#include "Config.h"

// 前方宣言（将来の拡張用）
struct SensorData;

class AcceleratorController {
   private:
    // 前方距離から速度を計算
    uint16_t _calculateFromDistance(const SensorData* sensorData);

   public:
    AcceleratorController();

    // 初期化
    void begin();

    // 速度を計算（ステアリング角度と前方距離から）
    // steering_angle: ステアリング角度（度）
    // sensorData: センサーデータ（前方距離による減速に使用）
    // 戻り値: ESCパルス幅（μs）
    uint16_t calculate(float steering_angle, const SensorData* sensorData = nullptr);
};

#endif  // ACCELERATOR_CONTROLLER_H
