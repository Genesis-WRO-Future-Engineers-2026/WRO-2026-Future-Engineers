/*
 * AcceleratorController.cpp
 *
 * アクセル制御クラス（実装）
 * 前方距離に応じた速度制御
 *
 * 設計思想:
 * - 前方距離が近いほど減速（線形補間）
 */

#include "AcceleratorController.h"

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

    return _calculateFromDistance(sensorData);
}

uint16_t AcceleratorController::_calculateFromDistance(const SensorData* sensorData) {
    // sensorDataがnullの場合は停止
    if (sensorData == nullptr) {
        return ESC_STOP_US;
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
