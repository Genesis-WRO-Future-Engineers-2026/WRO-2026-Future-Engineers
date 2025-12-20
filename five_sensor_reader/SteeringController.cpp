/*
 * SteeringController.cpp
 *
 * ステアリング制御クラス（実装）
 * 幾何学ベース：壁の角度から直接ステアリング角度を決定
 * + 左側センサーの最小距離制約（35cm以上）
 */

#include "SteeringController.h"
#include "SensorReader.h"

SteeringController::SteeringController() {
  lastSensorData = nullptr;
}

float SteeringController::calculate(const WallDetection& walls, const SensorData* sensorData) {
  float steering_angle = 0.0;

  // =========================================================================
  // 基本ステアリング角度の計算（壁検出ベース）
  // =========================================================================
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

  // =========================================================================
  // 制約: 左側センサー（センサー0, 1）が35cm以上になるように補正
  // =========================================================================
  if (sensorData != nullptr) {
    // センサー0（-70°）とセンサー1（-20°）の距離を取得
    uint16_t sensor0_dist = sensorData[0].valid ? sensorData[0].distance : 9999;
    uint16_t sensor1_dist = sensorData[1].valid ? sensorData[1].distance : 9999;

    // 左側センサーのうち、近い方の距離
    uint16_t min_left_dist = min(sensor0_dist, sensor1_dist);

    // 左側が近すぎる場合、右に曲がる補正を追加
    if (min_left_dist < MIN_LEFT_DISTANCE) {
      // 距離が近いほど強く補正
      // 例: 300mm → 50mm不足 → +2.5度の補正
      // 例: 200mm → 150mm不足 → +7.5度の補正
      float shortage = MIN_LEFT_DISTANCE - min_left_dist;
      float correction = shortage * LEFT_AVOID_GAIN;

      // 右方向に補正（正の角度）
      steering_angle += correction;
    }
  }

  // =========================================================================
  // 最大操舵角でクランプ
  // =========================================================================
  if (steering_angle > MAX_STEERING_ANGLE) {
    steering_angle = MAX_STEERING_ANGLE;
  } else if (steering_angle < -MAX_STEERING_ANGLE) {
    steering_angle = -MAX_STEERING_ANGLE;
  }

  return steering_angle;
}
