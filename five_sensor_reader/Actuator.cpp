/*
 * Actuator.cpp
 *
 * アクチュエーター制御クラス（実装）
 */

#include "Actuator.h"

#include <math.h>

#include "Logger.h"
#include "SensorReader.h"

Actuator::Actuator() {
    // 何もしない
}

void Actuator::begin() {
#if ENABLE_PWM
    _steeringServo.attach(SERVO_PIN);
    _escController.attach(ESC_PIN);

    // 初期位置に設定
    _steeringServo.writeMicroseconds(SERVO_CENTER);
    _escController.writeMicroseconds(ESC_STOP_US);

    Logger::println("Actuators initialized:");
    Logger::print("  Servo: Pin ");
    Logger::println(SERVO_PIN);
    Logger::print("  ESC: Pin ");
    Logger::println(ESC_PIN);
#else
    Logger::println("DEBUG MODE: Actuators disabled (no PWM output)");
#endif
}

void Actuator::setSteering(float angle_degrees) {
    // 角度をパルス幅に変換（MAX_STEERING_ANGLEを基準にマッピング）
    int pulse_us =
        map((int)(angle_degrees * 10),
            (int)(-MAX_STEERING_ANGLE * 10),
            (int)(MAX_STEERING_ANGLE * 10),
            SERVO_MAX, SERVO_MIN);

    // 中央オフセット補正: SERVO_CENTERを基準に調整
    // map計算の中央は(SERVO_MIN+SERVO_MAX)/2、これとSERVO_CENTERの差分を補正
    pulse_us += SERVO_CENTER - (SERVO_MIN + SERVO_MAX) / 2;

    // 範囲チェック
    if (pulse_us < SERVO_MIN) pulse_us = SERVO_MIN;
    if (pulse_us > SERVO_MAX) pulse_us = SERVO_MAX;

// PWM出力
#if ENABLE_PWM
    _steeringServo.writeMicroseconds(pulse_us);
#endif

    Logger::printActuator("Servo", pulse_us);
}

void Actuator::setSpeed(uint16_t pulse_us) {
    // 範囲チェック
    if (pulse_us < ESC_MIN_US) pulse_us = ESC_MIN_US;
    if (pulse_us > ESC_MAX_US) pulse_us = ESC_MAX_US;

// PWM出力
#if ENABLE_PWM
    _escController.writeMicroseconds(pulse_us);
#endif

    Logger::printActuator("ESC", pulse_us);
}

uint16_t Actuator::calculateSpeed(float steering_angle, const SensorData* sensorData) {
    // ステアリング連動が無効の場合は固定速度
    if (!SPEED_STEERING_LINK_ENABLED) {
        return TOP_SPEED_US;
    }

    // 正面センサー（インデックス2）の距離を取得（無効時は最大距離）
    uint16_t front_distance = sensorData[2].valid ? sensorData[2].distance : RELIABLE_RANGE;

    // === 1. ステアリング角度による減速 ===
    uint16_t speed_from_steering = TOP_SPEED_US;
    float abs_angle = abs(steering_angle);

    if (abs_angle > STEERING_DEADZONE) {
        float effective_angle = abs_angle - STEERING_DEADZONE;
        float effective_max = MAX_STEERING_ANGLE - STEERING_DEADZONE;
        if (effective_angle > effective_max) {
            effective_angle = effective_max;
        }
        float ratio = effective_angle / effective_max;
        speed_from_steering = TOP_SPEED_US +
            (uint16_t)((CORNER_SPEED_US - TOP_SPEED_US) * sqrt(ratio));
    }

    // === 2. 正面距離による先行減速 ===
    // STRAIGHT_MODE_THRESHOLD以下で減速開始、EMERGENCY_FRONT_THRESHOLDで最大減速
    uint16_t speed_from_distance = TOP_SPEED_US;

    if (front_distance < STRAIGHT_MODE_THRESHOLD) {
        if (front_distance <= EMERGENCY_FRONT_THRESHOLD) {
            // 最大減速
            speed_from_distance = CORNER_SPEED_US;
        } else {
            // 線形補間: 距離が近いほど減速
            float dist_ratio = (float)(STRAIGHT_MODE_THRESHOLD - front_distance) /
                               (float)(STRAIGHT_MODE_THRESHOLD - EMERGENCY_FRONT_THRESHOLD);
            speed_from_distance = TOP_SPEED_US +
                (uint16_t)((CORNER_SPEED_US - TOP_SPEED_US) * dist_ratio);
        }
    }

    // === 3. より大きい減速を採用（小さいパルス幅 = より遅い） ===
    return min(speed_from_steering, speed_from_distance);
}

void Actuator::stop() { setSpeed(ESC_STOP_US); }
