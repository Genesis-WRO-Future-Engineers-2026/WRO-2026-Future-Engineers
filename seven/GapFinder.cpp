/*
 * GapFinder.cpp
 *
 * 最遠+隣接センサー方式によるギャップ検出（実装）
 *
 * アルゴリズム概要:
 * 1. 有効な7センサーから距離が最も遠い1つを選択（ヒステリシス付き）
 * 2. その隣接センサー（左右）を取得（端の場合は片側のみ）
 * 3. 三角形面積按分で目標角度を計算（両側隣接あり）
 *    または距離重み付けで計算（片側のみ）
 *
 * 三角形面積按分:
 * - 左三角形面積 = d_left × d_farthest × sin(角度差)
 * - 右三角形面積 = d_farthest × d_right × sin(角度差)
 * - target = (左角度 × 左面積 + 右角度 × 右面積) / (左面積 + 右面積)
 */

#include "GapFinder.h"

#include <math.h>

// 度からラジアンへの変換定数
#ifndef DEG_TO_RAD
#define DEG_TO_RAD 0.017453292519943295  // PI / 180.0
#endif

GapFinder::GapFinder() : _lastFarthestIdx(FRONT_SENSOR_INDEX) {}  // 初期値は正面センサー

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

    // Step 3: 目標角度を計算
    bool has_left = (left_idx >= 0 && data[left_idx].valid);
    bool has_right = (right_idx >= 0 && data[right_idx].valid);

    if (has_left && has_right) {
        // 両側に隣接センサーあり: 三角形面積按分（方式A）
        // 面積 = d1 × d2 × sin(角度差)、(1/2)は比率計算で消えるので省略
        float angle_diff_left = fabs(SENSOR_ANGLES[farthest_idx] - SENSOR_ANGLES[left_idx]);
        float angle_diff_right = fabs(SENSOR_ANGLES[right_idx] - SENSOR_ANGLES[farthest_idx]);

        float area_left = data[left_idx].distance * farthest_dist *
                          sin(angle_diff_left * DEG_TO_RAD);
        float area_right = farthest_dist * data[right_idx].distance *
                           sin(angle_diff_right * DEG_TO_RAD);

        result.target_angle = (SENSOR_ANGLES[left_idx] * area_left +
                               SENSOR_ANGLES[right_idx] * area_right) /
                              (area_left + area_right);
    } else {
        // 片側のみ or 隣接なし: 従来の距離重み付け
        float weighted_sum = SENSOR_ANGLES[farthest_idx] * farthest_dist;
        float weight_total = farthest_dist;

        if (has_left) {
            weighted_sum += SENSOR_ANGLES[left_idx] * data[left_idx].distance;
            weight_total += data[left_idx].distance;
        }
        if (has_right) {
            weighted_sum += SENSOR_ANGLES[right_idx] * data[right_idx].distance;
            weight_total += data[right_idx].distance;
        }

        result.target_angle = weighted_sum / weight_total;
    }
    result.farthest_distance = farthest_dist;

    return result;
}
