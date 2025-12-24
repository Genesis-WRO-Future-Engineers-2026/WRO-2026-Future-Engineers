/*
 * SteeringController.cpp
 *
 * ステアリング制御クラス（実装）
 * Follow the Gap + P制御
 *
 * 設計思想:
 * - GapFinderが検出したギャップ中心方向へステアリング
 * - シンプルなP制御（比例制御のみ）
 * - 調整パラメータは STEERING_KP の1つだけ
 */

#include "SteeringController.h"

#include "Logger.h"

SteeringController::SteeringController() { _lastTargetAngle = 0.0; }

void SteeringController::begin() {
    // P制御なので特別な初期化は不要
    _lastTargetAngle = 0.0;
}

float SteeringController::calculate(const GapResult& gap) {
    // 目標角度を保存（デバッグ用）
    _lastTargetAngle = gap.target_angle;

    // P制御: ステアリング角 = Kp × ギャップ中心角度
    float steering = STEERING_KP * gap.target_angle;

    // 最大操舵角でクランプ
    steering = constrain(steering, -MAX_STEERING_ANGLE, MAX_STEERING_ANGLE);

    return steering;
}

void SteeringController::reset() { _lastTargetAngle = 0.0; }
