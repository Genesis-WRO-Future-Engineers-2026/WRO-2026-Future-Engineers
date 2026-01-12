/*
 * AcceleratorController.cpp
 *
 * アクセル制御クラス（実装）
 * ステアリング角度に応じた連続的な速度制御
 *
 * 設計思想:
 * - ステアリング角度が大きいほど減速
 * - STEERING_DEADZONE以内は最高速度を維持
 * - DEADZONE〜MAX_STEERING_ANGLEは線形補間で減速
 */

#include "AcceleratorController.h"

#include <math.h>

AcceleratorController::AcceleratorController() {}

void AcceleratorController::begin() {
    // 将来の拡張用
}

uint16_t AcceleratorController::calculate(float steering_angle, const SensorData* sensorData) {
    // ステアリング連動が無効の場合は固定速度
    if (!SPEED_STEERING_LINK_ENABLED) {
        return TOP_SPEED_US;
    }

    float abs_angle = fabs(steering_angle);

    // DEADZONE以内は最高速度
    if (abs_angle <= STEERING_DEADZONE) {
        return TOP_SPEED_US;
    }

    // DEADZONE〜MAX_STEERING_ANGLEで線形補間
    // abs_angle = STEERING_DEADZONE → TOP_SPEED_US
    // abs_angle = MAX_STEERING_ANGLE → CORNER_SPEED_US
    float effective_angle = abs_angle - STEERING_DEADZONE;
    float effective_range = MAX_STEERING_ANGLE - STEERING_DEADZONE;

    // 比率を計算（0.0 〜 1.0）
    float ratio = effective_angle / effective_range;
    if (ratio > 1.0) ratio = 1.0;

    // 線形補間: TOP_SPEED_US から CORNER_SPEED_US へ
    // CORNER_SPEED_US < TOP_SPEED_US なので、減速方向
    uint16_t speed = TOP_SPEED_US + (int16_t)((CORNER_SPEED_US - TOP_SPEED_US) * ratio);

    return speed;
}

void AcceleratorController::reset() {
    // 将来の拡張用
}
