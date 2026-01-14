/*
 * AcceleratorController.cpp
 *
 * アクセル制御クラス（実装）
 * 前方距離に応じた速度制御
 *
 * 設計思想:
 * - 前方距離が近いほど減速（非線形カーブ）
 * - DECEL_CURVE_EXPONENT で減速の急さを調整
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
    if (!SPEED_DISTANCE_LINK_ENABLED) {
        return MAX_SPEED_US;
    }

    return _calculateFromDistance(sensorData);
}

uint16_t AcceleratorController::_calculateFromDistance(const SensorData* sensorData) {
    // sensorDataがnullの場合は停止
    if (sensorData == nullptr) {
        return ESC_STOP_US;
    }

    // 正面センサーの距離を取得
    uint16_t front_distance = sensorData[FRONT_SENSOR_INDEX].valid ? sensorData[FRONT_SENSOR_INDEX].distance : RELIABLE_RANGE;

    // DECEL_START_DISTANCE以上なら最高速度
    if (front_distance >= DECEL_START_DISTANCE) {
        return MAX_SPEED_US;
    }

    // EMERGENCY_FRONT_THRESHOLD以下なら最低速度
    if (front_distance <= EMERGENCY_FRONT_THRESHOLD) {
        return MIN_SPEED_US;
    }

    // 非線形カーブ: 距離が近いほど減速
    // front_distance = DECEL_START_DISTANCE → ratio = 0 → MAX_SPEED_US
    // front_distance = EMERGENCY_FRONT_THRESHOLD → ratio = 1 → MIN_SPEED_US
    // DECEL_CURVE_EXPONENT < 1.0 で最初に急激に減速
    float ratio_linear = (float)(DECEL_START_DISTANCE - front_distance) /
                         (float)(DECEL_START_DISTANCE - EMERGENCY_FRONT_THRESHOLD);
    float ratio = pow(ratio_linear, DECEL_CURVE_EXPONENT);

    return MAX_SPEED_US + (int16_t)((MIN_SPEED_US - MAX_SPEED_US) * ratio);
}

void AcceleratorController::reset() {
    // 将来の拡張用
}
