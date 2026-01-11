/*
 * SteeringController.cpp
 *
 * ステアリング制御クラス（実装）
 * Follow the Gap + PD制御 + 壁回避補正
 *
 * 設計思想:
 * - GapFinderが検出したギャップ中心方向へステアリング（攻め）
 * - WallAvoiderが壁に近すぎる時に逃げる補正を追加（守り）
 * - P項: 目標角度に比例したステアリング
 * - D項: 角度変化率に比例した予測制御（高速時のオーバーシュート抑制）
 * - 調整パラメータは STEERING_KP, STEERING_KD, WALL_AVOIDANCE_GAIN
 */

#include "SteeringController.h"

#include "SensorReader.h"

SteeringController::SteeringController() : _lastTargetAngle(0.0), _wallAvoider() {}

void SteeringController::begin() {
    _lastTargetAngle = 0.0;
}

float SteeringController::calculate(const GapResult& gap, const SensorData* sensorData) {
    // 直進モード: 正面センサー（インデックス2、0度）が閾値以上空いていれば直進
    // ただし壁回避補正は適用する
    if (sensorData[2].valid &&
        sensorData[2].distance >= STRAIGHT_MODE_THRESHOLD) {
        float wall_correction = _wallAvoider.calculate(sensorData);
        _lastTargetAngle = 0.0;
        return constrain(wall_correction, -MAX_STEERING_ANGLE, MAX_STEERING_ANGLE);
    }

    // P項: 目標角度に比例
    float p_term = STEERING_KP * gap.target_angle;

    // D項: 角度変化率に比例（急変動を抑制）
    float angle_change = gap.target_angle - _lastTargetAngle;
    float d_term = -STEERING_KD * angle_change;  // 負のフィードバックで急変動を抑制

    // 壁回避補正: 壁が近すぎる時に逃げる
    float wall_correction = _wallAvoider.calculate(sensorData);

    // 目標角度を保存（次回のD項計算用）
    _lastTargetAngle = gap.target_angle;

    // PD制御 + 壁回避補正: ステアリング角 = P項 + D項 + 壁回避
    float steering = p_term + d_term + wall_correction;

    // 最大操舵角でクランプ
    steering = constrain(steering, -MAX_STEERING_ANGLE, MAX_STEERING_ANGLE);

    return steering;
}

void SteeringController::reset() { _lastTargetAngle = 0.0; }
