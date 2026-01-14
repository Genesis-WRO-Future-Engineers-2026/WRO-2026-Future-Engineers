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
    float target_angle;      // 目標方向角度（度）正=右、負=左
    float farthest_distance; // 最遠センサーの距離（mm）
};

class GapFinder {
   private:
    int _lastFarthestIdx;  // 前回の最遠センサーインデックス（ヒステリシス用）

   public:
    GapFinder();

    // メイン処理: センサーデータから目標角度を決定
    GapResult find(const SensorData* sensorData);
};

#endif  // GAP_FINDER_H
