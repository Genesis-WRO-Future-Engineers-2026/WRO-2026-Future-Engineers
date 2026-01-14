/*
 * GapFinder.h
 *
 * 最遠+隣接センサー方式によるギャップ検出
 * 最も遠いセンサーとその隣接センサーの距離重み付けで目標角度を決定
 */

#ifndef GAP_FINDER_H
#define GAP_FINDER_H

#include <Arduino.h>

#include "Config.h"
#include "SensorReader.h"

// ギャップ検出結果構造体
struct GapResult {
    float target_angle;     // 目標方向角度（度）正=右、負=左
    float target_distance;  // 目標方向への推定距離（mm）- 線形補間で計算
};

class GapFinder {
   private:
    int _lastFarthestIdx;  // 前回の最遠センサーインデックス（ヒステリシス用）

    // 最も遠いセンサーを見つける（ヒステリシス適用前）
    int _findFarthestSensor(const SensorData* data, float& outDistance) const;

    // ヒステリシス処理を適用し、最終的な最遠センサーを決定
    int _applyHysteresis(const SensorData* data, int candidateIdx,
                         float candidateDist, float& outDistance);

    // 最遠センサーと隣接センサーから目標角度を計算
    float _calculateTargetAngle(const SensorData* data, int farthestIdx,
                                float farthestDist) const;

    // 目標角度方向への距離を線形補間で計算
    float _interpolateTargetDistance(const SensorData* data,
                                     float targetAngle) const;

   public:
    GapFinder();

    // メイン処理: センサーデータから目標角度と距離を決定
    GapResult find(const SensorData* sensorData);
};

#endif  // GAP_FINDER_H
