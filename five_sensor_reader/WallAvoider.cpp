/*
 * WallAvoider.cpp
 *
 * 壁回避補正クラス（実装）
 *
 * 設計思想:
 * - GapFinderが「どこに向かうか」を決定（攻め）
 * - WallAvoiderが「壁から離れる補正」を計算（守り）
 * - 壁が近いセンサーがあれば、その逆方向への補正を返す
 */

#include "WallAvoider.h"

#include "SensorReader.h"

WallAvoider::WallAvoider() {
    // 何もしない
}

float WallAvoider::calculate(const SensorData* sensorData) {
    float correction = 0.0;

    for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
        if (!sensorData[i].valid) {
            continue;
        }

        // 閾値より近いセンサーを検出
        if (sensorData[i].distance < WALL_PROXIMITY_THRESHOLD) {
            // 近さの度合い（0〜1、近いほど大きい）
            float proximity = (float)(WALL_PROXIMITY_THRESHOLD - sensorData[i].distance) /
                              (float)WALL_PROXIMITY_THRESHOLD;

            // センサー角度の逆方向に補正
            // 左側センサー（負の角度）が近い → 正の補正（右へ逃げる）
            // 右側センサー（正の角度）が近い → 負の補正（左へ逃げる）
            correction -= SENSOR_ANGLES[i] * proximity * WALL_AVOIDANCE_GAIN;
        }
    }

    return correction;
}
