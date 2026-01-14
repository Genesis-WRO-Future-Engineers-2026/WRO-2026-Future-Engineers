/*
 * Actuator.h
 *
 * アクチュエーター制御クラス（宣言）
 * サーボとESCのPWM制御（DEBUG_MODEに応じて出力制御）
 */

#ifndef ACTUATOR_H
#define ACTUATOR_H

#include <Arduino.h>
#include <Servo.h>

#include "Config.h"

class Actuator {
   private:
    Servo _steeringServo;
    Servo _escController;

   public:
    // コンストラクタ
    Actuator();

    // 初期化
    void begin();

    // ステアリング角度を設定（度数法）
    void setSteering(float angle_degrees);

    // 速度を設定（μs単位のパルス幅）
    void setSpeed(uint16_t speed_pulse_us);

    // 停止
    void stop();
};

#endif  // ACTUATOR_H
