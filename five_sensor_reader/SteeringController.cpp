/*
 * SteeringController.cpp
 *
 * ステアリング制御クラス（実装）
 */

#include "SteeringController.h"

SteeringController::SteeringController() {
  // 何もしない
}

float SteeringController::calculate(const WallDetection& walls) {
  float steering_angle = 0.0;

  if (walls.left_valid && walls.right_valid) {
    // 状態1: 両壁検出 → 交点差に比例したステアリング
    float intersection_diff = walls.left_intersection - walls.right_intersection;
    steering_angle = intersection_diff * GAIN_FACTOR;
  }
  else if (walls.left_valid && !walls.right_valid) {
    // 状態2: 左壁のみ → 左へステアリング（開けた方向へ）
    steering_angle = -MAX_STEERING_ANGLE * OPEN_SIDE_RATIO;
  }
  else if (!walls.left_valid && walls.right_valid) {
    // 状態3: 右壁のみ → 右へステアリング（開けた方向へ）
    steering_angle = MAX_STEERING_ANGLE * OPEN_SIDE_RATIO;
  }
  else {
    // 状態4: 壁なし → 直進
    steering_angle = 0.0;
  }

  // 最大操舵角でクランプ
  if (steering_angle > MAX_STEERING_ANGLE) {
    steering_angle = MAX_STEERING_ANGLE;
  } else if (steering_angle < -MAX_STEERING_ANGLE) {
    steering_angle = -MAX_STEERING_ANGLE;
  }

  return steering_angle;
}
