/*
 * SteeringController.cpp
 *
 * ステアリング制御クラス（実装）
 * Follow the Gap + PD制御 + 直進モード判定
 *
 * 設計思想:
 * - 直進モード: 2条件のいずれかを満たせばステアリング0度
 *   - 条件1: 前方センサーが十分開けている（≥ STRAIGHT_THRESHOLD_FRONT）
 *   - 条件2: 全センサー最小距離 ≥ STRAIGHT_THRESHOLD_MIN
 *            AND 前方センサー ≥ STRAIGHT_THRESHOLD_FRONT_MIN
 * - 通常モード: GapFinderが検出したギャップ中心方向へステアリング
 * - P項: 目標角度に比例したステアリング
 * - D項: 角度変化率に比例した予測制御（高速時のオーバーシュート抑制）
 * - 調整パラメータは STEERING_KP, STEERING_KD
 */

#include "SteeringController.h"

#include "SensorReader.h"

SteeringController::SteeringController() : _lastTargetAngle(0.0) {}

void SteeringController::begin() {
    _lastTargetAngle = 0.0;
}

float SteeringController::calculate(const GapResult& gap, const SensorData* sensorData) {
    // 直進モード判定
    bool is_straight = false;

    // 条件1: 前方センサーが十分開けている
    if (sensorData[FRONT_SENSOR_INDEX].valid &&
        sensorData[FRONT_SENSOR_INDEX].distance >= STRAIGHT_THRESHOLD_FRONT) {
        is_straight = true;
    }

    // 条件2: 全センサーが壁から離れている AND 前方もある程度開けている
    if (!is_straight) {
        uint16_t min_dist = UINT16_MAX;
        for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
            if (sensorData[i].valid && sensorData[i].distance < min_dist) {
                min_dist = sensorData[i].distance;
            }
        }
        uint16_t front_dist = sensorData[FRONT_SENSOR_INDEX].valid
            ? sensorData[FRONT_SENSOR_INDEX].distance : 0;
        if (min_dist >= STRAIGHT_THRESHOLD_MIN &&
            front_dist >= STRAIGHT_THRESHOLD_FRONT_MIN) {
            is_straight = true;
        }
    }

    // 直進モード: ステアリング0度
    if (is_straight) {
        _lastTargetAngle = 0.0;
        return 0.0;
    }

    // P項: 目標角度に比例
    float p_term = STEERING_KP * gap.target_angle;

    // D項: 角度変化率に比例（急変動を抑制）
    float angle_change = gap.target_angle - _lastTargetAngle;
    float d_term = -STEERING_KD * angle_change;  // 負のフィードバックで急変動を抑制

    // 目標角度を保存（次回のD項計算用）
    _lastTargetAngle = gap.target_angle;

    // PD制御: ステアリング角 = P項 + D項
    float steering = p_term + d_term;

    // 最大操舵角でクランプ
    steering = constrain(steering, -MAX_STEERING_ANGLE, MAX_STEERING_ANGLE);

    return steering;
}

void SteeringController::reset() { _lastTargetAngle = 0.0; }
