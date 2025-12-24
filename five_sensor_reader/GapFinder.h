/*
 * GapFinder.h
 *
 * Follow the Gap アルゴリズム（宣言）
 * 5センサーからギャップ（開けた空間）を検出し、最適な走行方向を決定
 */

#ifndef GAP_FINDER_H
#define GAP_FINDER_H

#include <Arduino.h>

#include "Config.h"
#include "SensorReader.h"

// ギャップ情報構造体
struct Gap {
    float start_angle;   // ギャップ開始角度（度）
    float end_angle;     // ギャップ終了角度（度）
    float center_angle;  // ギャップ中心角度（度）
    float width_angle;   // ギャップ幅（角度）
    float min_distance;  // ギャップ内の最小距離（mm）
    bool valid;          // 有効なギャップか
};

// ギャップ検出結果構造体
struct GapResult {
    Gap best_gap;        // 最適なギャップ
    float target_angle;  // 目標方向角度（度）正=右、負=左
    int num_gaps;        // 検出されたギャップ数
    bool has_valid_gap;  // 有効なギャップが存在するか
};

// 最大ギャップ数（5センサーで最大3つのギャップ）
const int MAX_GAPS = 3;

class GapFinder {
   private:
    Gap _gaps[MAX_GAPS];                    // 検出されたギャップ
    int _numGaps;                           // 検出されたギャップ数
    float _inflatedDistances[NUM_SENSORS];  // 膨張処理後の距離

    // 障害物膨張処理（安全マージン適用）
    void _inflateObstacles(const SensorData* data);

    // ギャップ検出
    void _findGaps(const SensorData* data);

    // ギャップを記録
    void _recordGap(int startIdx, int endIdx, const SensorData* data);

    // 最適ギャップ選択（スコアリング）
    Gap _selectBestGap();

    // ギャップスコア計算
    float _calculateGapScore(const Gap& gap);

   public:
    GapFinder();

    // メイン処理: センサーデータからギャップを検出
    GapResult find(const SensorData* sensorData);

    // 検出されたギャップ数を取得
    int getNumGaps() const { return _numGaps; }
};

#endif  // GAP_FINDER_H
