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
   public:
    AcceleratorController();

    // 初期化
    void begin();

    // 速度を計算（ステアリング角度に応じた線形補間）
    // steering_angle: ステアリング角度（度）
    // sensorData: センサーデータ（将来の拡張用、現在は未使用）
    // 戻り値: ESCパルス幅（μs）
    uint16_t calculate(float steering_angle, const SensorData* sensorData = nullptr);

    // リセット
    void reset();
};

#endif  // ACCELERATOR_CONTROLLER_H
