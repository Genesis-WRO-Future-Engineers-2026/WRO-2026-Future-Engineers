/*
 * SteeringController.cpp
 *
 * ステアリング制御クラス（実装）
 * 幾何学ベース：壁の角度から直接ステアリング角度を決定
 */

#include "SteeringController.h"

SteeringController::SteeringController() {
  // 何もしない
}

float SteeringController::calculate(const WallDetection& walls) {
  float steering_angle = 0.0;

  if (walls.left_valid && walls.right_valid) {
    // 状態1: 両壁検出 → 近い方の壁に平行になるようにステアリング

    // どちらの壁が近いか判定（y軸交点が小さい方が近い）
    // 絶対値で比較（マイナスの交点は車体より後方なので遠い）
    float left_distance = abs(walls.left_intersection);
    float right_distance = abs(walls.right_intersection);

    if (left_distance < right_distance) {
      // 左壁が近い → 左壁に平行になる角度でステアリング
      steering_angle = walls.left_angle;
    } else {
      // 右壁が近い → 右壁に平行になる角度でステアリング
      // 注: 右壁は符号を反転（右壁の角度は車体から見て逆向き）
      steering_angle = -walls.right_angle;
    }
  }
  else if (walls.left_valid && !walls.right_valid) {
    // 状態2: 左壁のみ → 左壁に平行になるようにステアリング
    steering_angle = walls.left_angle;
  }
  else if (!walls.left_valid && walls.right_valid) {
    // 状態3: 右壁のみ → 右壁に平行になるようにステアリング
    // 注: 右壁は符号を反転（右壁の角度は車体から見て逆向き）
    steering_angle = -walls.right_angle;
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
