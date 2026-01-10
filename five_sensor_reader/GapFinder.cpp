/*
 * GapFinder.cpp
 *
 * 最遠+隣接センサー方式によるギャップ検出（実装）
 *
 * アルゴリズム概要:
 * 1. 有効な5センサーから距離が最も遠い1つを選択（ヒステリシス付き）
 * 2. その隣接センサー（左右）を取得（端の場合は片側のみ）
 * 3. 最遠センサー+隣接センサーの距離で重み付けした角度をtarget_angleとする
 */

#include "GapFinder.h"

GapFinder::GapFinder() : _lastFarthestIdx(2) {}  // 初期値は正面（センサー2）

GapResult GapFinder::find(const SensorData* data) {
    GapResult result;
    result.target_angle = 0.0;
    result.farthest_distance = 0.0;

    // Step 1: 最も遠いセンサーを見つける
    int farthest_idx = -1;
    float farthest_dist = 0.0;

    for (int i = 0; i < NUM_SENSORS; ++i) {
        if (data[i].valid && data[i].distance > farthest_dist) {
            farthest_dist = data[i].distance;
            farthest_idx = i;
        }
    }

    // 有効なセンサーがない場合は直進
    if (farthest_idx < 0) {
        return result;
    }

    // Step 1.5: ヒステリシス処理（最遠センサーの切り替え抑制）
    // 前回の最遠センサーが有効で、新しい最遠との差がヒステリシス未満なら切り替えない
    if (_lastFarthestIdx >= 0 && _lastFarthestIdx < NUM_SENSORS &&
        data[_lastFarthestIdx].valid && farthest_idx != _lastFarthestIdx) {
        float diff = farthest_dist - data[_lastFarthestIdx].distance;
        if (diff < FARTHEST_HYSTERESIS) {
            // 切り替えない：前回の最遠センサーを維持
            farthest_idx = _lastFarthestIdx;
            farthest_dist = data[farthest_idx].distance;
        }
    }
    _lastFarthestIdx = farthest_idx;

    // Step 2: 隣接センサーのインデックスを決定
    int left_idx = (farthest_idx > 0) ? farthest_idx - 1 : -1;
    int right_idx = (farthest_idx < NUM_SENSORS - 1) ? farthest_idx + 1 : -1;

    // Step 3: 距離重み付けで目標角度を計算
    float weighted_sum = SENSOR_ANGLES[farthest_idx] * farthest_dist;
    float weight_total = farthest_dist;

    if (left_idx >= 0 && data[left_idx].valid) {
        weighted_sum += SENSOR_ANGLES[left_idx] * data[left_idx].distance;
        weight_total += data[left_idx].distance;
    }
    if (right_idx >= 0 && data[right_idx].valid) {
        weighted_sum += SENSOR_ANGLES[right_idx] * data[right_idx].distance;
        weight_total += data[right_idx].distance;
    }

    result.target_angle = weighted_sum / weight_total;
    result.farthest_distance = farthest_dist;

    return result;
}
