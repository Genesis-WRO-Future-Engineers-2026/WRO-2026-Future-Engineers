/*
 * GapFinder.cpp
 *
 * Follow the Gap アルゴリズム（実装）
 *
 * アルゴリズム概要:
 * 1. 各センサーの距離を取得
 * 2. 障害物膨張（安全マージン適用）
 * 3. 連続する「開いた空間」をギャップとして検出
 * 4. ギャップの幅・距離・前方優先度でスコアリング
 * 5. 最高スコアのギャップ中心を目標方向として返す
 */

#include "GapFinder.h"

GapFinder::GapFinder() {
    _numGaps = 0;
    for (int i = 0; i < MAX_GAPS; i++) {
        _gaps[i].valid = false;
    }
    for (int i = 0; i < NUM_SENSORS; i++) {
        _inflatedDistances[i] = 0;
    }
}

GapResult GapFinder::find(const SensorData* sensorData) {
    GapResult result;
    result.num_gaps = 0;
    result.target_angle = 0.0;
    result.has_valid_gap = false;
    result.best_gap.valid = false;

    // Step 1: 障害物膨張処理
    _inflateObstacles(sensorData);

    // Step 2: ギャップ検出
    _findGaps(sensorData);

    result.num_gaps = _numGaps;

    // Step 3: 最適ギャップ選択
    if (_numGaps > 0) {
        Gap bestGap = _selectBestGap();
        if (bestGap.valid) {
            result.best_gap = bestGap;
            result.target_angle = bestGap.center_angle;
            result.has_valid_gap = true;
        }
    }

    // ギャップが見つからない場合: 最も遠い方向へ
    if (!result.has_valid_gap) {
        float maxDist = 0;
        int maxIdx = 2;  // デフォルトは前方
        for (int i = 0; i < NUM_SENSORS; i++) {
            if (sensorData[i].valid && sensorData[i].distance > maxDist) {
                maxDist = sensorData[i].distance;
                maxIdx = i;
            }
        }
        result.target_angle = SENSOR_ANGLES[maxIdx];
    }

    return result;
}

void GapFinder::_inflateObstacles(const SensorData* data) {
    for (int i = 0; i < NUM_SENSORS; i++) {
        if (data[i].valid) {
            // 障害物が近い場合、安全マージン分だけ距離を短くする
            if (data[i].distance < OBSTACLE_THRESHOLD) {
                _inflatedDistances[i] =
                    max(0.0f, data[i].distance - OBSTACLE_INFLATION_RADIUS);
            } else {
                _inflatedDistances[i] = data[i].distance;
            }
        } else {
            // 無効なセンサーは障害物として扱う（安全側）
            _inflatedDistances[i] = 0;
        }
    }
}

void GapFinder::_findGaps(const SensorData* data) {
    _numGaps = 0;

    // 各センサーが「開いているか」判定
    bool isOpen[NUM_SENSORS];
    for (int i = 0; i < NUM_SENSORS; i++) {
        isOpen[i] =
            (data[i].valid && _inflatedDistances[i] > OBSTACLE_THRESHOLD);
    }

    // 連続するOPENをギャップとして検出
    int gapStart = -1;
    for (int i = 0; i < NUM_SENSORS; i++) {
        if (isOpen[i]) {
            if (gapStart < 0) {
                gapStart = i;  // ギャップ開始
            }
        } else {
            if (gapStart >= 0) {
                // ギャップ終了、記録
                _recordGap(gapStart, i - 1, data);
                gapStart = -1;
            }
        }
    }
    // 最後まで開いていた場合
    if (gapStart >= 0) {
        _recordGap(gapStart, NUM_SENSORS - 1, data);
    }
}

void GapFinder::_recordGap(int startIdx, int endIdx, const SensorData* data) {
    if (_numGaps >= MAX_GAPS) return;

    Gap& gap = _gaps[_numGaps];

    gap.start_angle = SENSOR_ANGLES[startIdx];
    gap.end_angle = SENSOR_ANGLES[endIdx];
    gap.width_angle = gap.end_angle - gap.start_angle;

    // ギャップ中心を距離で重み付けして計算
    // 距離が遠いセンサー方向に重心を寄せる
    float weightedAngleSum = 0.0;
    float weightSum = 0.0;
    float minDist = 99999;

    for (int i = startIdx; i <= endIdx; i++) {
        if (data[i].valid) {
            float dist = _inflatedDistances[i];
            // 距離を重みとして使用（遠いほど重み大）
            weightedAngleSum += SENSOR_ANGLES[i] * dist;
            weightSum += dist;

            if (dist < minDist) {
                minDist = dist;
            }
        }
    }

    // 重み付き中心角度を計算
    if (weightSum > 0) {
        gap.center_angle = weightedAngleSum / weightSum;
    } else {
        // フォールバック：単純な中央
        gap.center_angle = (gap.start_angle + gap.end_angle) / 2.0;
    }

    gap.min_distance = minDist;

    // 最小幅チェック
    gap.valid = (gap.width_angle >= MIN_GAP_WIDTH_ANGLE);

    if (gap.valid) {
        _numGaps++;
    }
}

Gap GapFinder::_selectBestGap() {
    Gap bestGap;
    bestGap.valid = false;
    float bestScore = -1;

    for (int i = 0; i < _numGaps; i++) {
        if (_gaps[i].valid) {
            float score = _calculateGapScore(_gaps[i]);
            if (score > bestScore) {
                bestScore = score;
                bestGap = _gaps[i];
            }
        }
    }

    return bestGap;
}

float GapFinder::_calculateGapScore(const Gap& gap) {
    // スコア計算:
    // - 距離: ギャップが遠いほど高スコア
    // - 幅: ギャップが広いほど高スコア
    // - 前方優先: 正面に近いほど高スコア

    // 正規化
    float distScore = gap.min_distance / RELIABLE_RANGE;  // 0-1
    float widthScore = gap.width_angle / 140.0;  // 0-1 (最大幅は-70〜+70=140度)
    float forwardScore = 1.0 - (fabs(gap.center_angle) / 70.0);  // 0-1

    // 重み付き合計
    float score = GAP_WEIGHT_DISTANCE * distScore +
                  GAP_WEIGHT_WIDTH * widthScore +
                  GAP_WEIGHT_FORWARD * forwardScore;

    return score;
}
