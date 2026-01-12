/*
 * AcceleratorController.cpp
 *
 * アクセル制御クラス（実装）
 * ステアリング角度と前方距離に応じた速度制御
 *
 * 設計思想:
 * - ステアリング角度が大きいほど減速（線形補間）
 * - 前方距離が近いほど減速（線形補間）
 * - 両者のmin（より遅い方）を採用
 */

#include "AcceleratorController.h"

#include <math.h>

#include "SensorReader.h"

AcceleratorController::AcceleratorController() {}

void AcceleratorController::begin() {
    // 将来の拡張用
}

uint16_t AcceleratorController::calculate(float steering_angle, const SensorData* sensorData) {
    // ステアリング連動が無効の場合は固定速度
    if (!SPEED_STEERING_LINK_ENABLED) {
        return TOP_SPEED_US;
    }

    // === 1. ステアリング角度による速度 ===
    uint16_t steering_speed = _calculateFromSteering(steering_angle);

    // === 2. 前方距離による速度 ===
    uint16_t distance_speed = _calculateFromDistance(sensorData);

    // === 3. より遅い方を採用 ===
    return min(steering_speed, distance_speed);
}

uint16_t AcceleratorController::_calculateFromSteering(float steering_angle) {
    float abs_angle = fabs(steering_angle);

    // DEADZONE以内は最高速度
    if (abs_angle <= STEERING_DEADZONE) {
        return TOP_SPEED_US;
    }

    // 比率を計算（0.0 〜 1.0）
    float ratio = abs_angle / MAX_STEERING_ANGLE;
    if (ratio > 1.0) ratio = 1.0;

    // 線形補間: TOP_SPEED_US から CORNER_SPEED_US へ
    return TOP_SPEED_US + (int16_t)((CORNER_SPEED_US - TOP_SPEED_US) * ratio);
}

uint16_t AcceleratorController::_calculateFromDistance(const SensorData* sensorData) {
    // sensorDataがnullの場合は最高速度
    if (sensorData == nullptr) {
        return 1500; // stop
    }

    // 正面センサー（インデックス2）の距離を取得
    uint16_t front_distance = sensorData[2].valid ? sensorData[2].distance : RELIABLE_RANGE;

    // STRAIGHT_MODE_THRESHOLD以上なら最高速度
    if (front_distance >= STRAIGHT_MODE_THRESHOLD) {
        return TOP_SPEED_US;
    }

    // EMERGENCY_FRONT_THRESHOLD以下なら最低速度
    if (front_distance <= EMERGENCY_FRONT_THRESHOLD) {
        return CORNER_SPEED_US;
    }

    // 線形補間: 距離が近いほど減速
    // front_distance = STRAIGHT_MODE_THRESHOLD → ratio = 0 → TOP_SPEED
    // front_distance = EMERGENCY_FRONT_THRESHOLD → ratio = 1 → CORNER_SPEED
    float ratio = (float)(STRAIGHT_MODE_THRESHOLD - front_distance) /
                  (float)(STRAIGHT_MODE_THRESHOLD - EMERGENCY_FRONT_THRESHOLD);

    return TOP_SPEED_US + (int16_t)((CORNER_SPEED_US - TOP_SPEED_US) * ratio);
}

void AcceleratorController::reset() {
    // 将来の拡張用
}
