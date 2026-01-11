/*
 * WallAvoider.h
 *
 * 壁回避補正クラス（宣言）
 * 壁に近すぎる時に「逃げる」補正角度を計算
 */

#ifndef WALL_AVOIDER_H
#define WALL_AVOIDER_H

#include <Arduino.h>

#include "Config.h"

// 前方宣言
struct SensorData;

class WallAvoider {
   public:
    WallAvoider();

    // 壁回避補正角度を計算（度）
    // 壁が近いセンサーがあれば逆方向への補正値を返す
    // 問題なければ0を返す
    float calculate(const SensorData* sensorData);
};

#endif  // WALL_AVOIDER_H
