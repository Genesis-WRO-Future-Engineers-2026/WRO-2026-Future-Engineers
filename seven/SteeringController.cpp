/*
 * SteeringController.cpp
 *
 * ステアリング制御クラス（実装）
 * Follow the Gap + Pure Pursuit制御
 *
 * 設計思想:
 * - GapFinderが検出した目標方向と距離をPure Pursuit公式に適用
 * - 公式: steering = atan2(2 × L × sin(α), Ld)
 *   L: ホイールベース（mm）
 *   α: 目標点への角度（ラジアン）
 *   Ld: ルックアヘッド距離（mm）- 目標方向への推定距離
 */

#include "SteeringController.h"

#include <math.h>

#include "SensorReader.h"

// 度からラジアンへの変換定数
#ifndef DEG_TO_RAD
#define DEG_TO_RAD 0.017453292519943295f  // PI / 180.0
#endif

#ifndef RAD_TO_DEG
#define RAD_TO_DEG 57.29577951308232f  // 180.0 / PI
#endif

SteeringController::SteeringController() {}

void SteeringController::begin() {
    // Pure Pursuitはステートレスなので初期化処理なし
}

float SteeringController::calculate(const GapResult& gap, const SensorData* sensorData) {
    // GapFinderの出力を目標点の極座標として解釈
    // α (alpha): 目標点への角度
    // Ld: ルックアヘッド距離（目標点までの距離）

    float alpha_deg = gap.target_angle;

    // 壁の手前を目標点とする（壁からオフセット分手前）
    float Ld_mm = gap.target_distance - LOOKAHEAD_OFFSET_MM;

    // 安定性のためルックアヘッド距離をクランプ
    Ld_mm = constrain(Ld_mm, MIN_LOOKAHEAD_MM, MAX_LOOKAHEAD_MM);

    // 角度をラジアンに変換
    float alpha_rad = alpha_deg * DEG_TO_RAD;

    // Pure Pursuit公式: δ = atan2(2 × L × sin(α), Ld)
    float steering_rad = atan2(2.0f * WHEELBASE_MM * sin(alpha_rad), Ld_mm);

    // 度に変換
    float steering_deg = steering_rad * RAD_TO_DEG;

    // 最大操舵角でクランプ
    steering_deg = constrain(steering_deg, -MAX_STEERING_ANGLE, MAX_STEERING_ANGLE);

    return steering_deg;
}

void SteeringController::reset() {
    // Pure Pursuitはステートレスなのでリセット処理なし
}
