/*
 * Actuator.cpp
 *
 * アクチュエーター制御クラス（実装）
 */

#include "Actuator.h"

#include "Logger.h"

Actuator::Actuator() {
    // 何もしない
}

void Actuator::begin() {
#if !DEBUG_MODE
    _steeringServo.attach(SERVO_PIN);
    _escController.attach(ESC_PIN);

    // 初期位置に設定
    _steeringServo.writeMicroseconds(SERVO_CENTER);
    _escController.writeMicroseconds((uint16_t)(STOP_SPEED_PULSE * 1000));

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
    // 角度をパルス幅に変換
    int pulse_us =
        map((int)(angle_degrees * 10), -900, 900, SERVO_MIN, SERVO_MAX);

    // 範囲チェック
    if (pulse_us < SERVO_MIN) pulse_us = SERVO_MIN;
    if (pulse_us > SERVO_MAX) pulse_us = SERVO_MAX;

// PWM出力
#if !DEBUG_MODE
    _steeringServo.writeMicroseconds(pulse_us);
#endif

    Logger::printActuator("Servo", pulse_us);
}

void Actuator::setSpeed(float speed_pulse_ms) {
    // msをμsに変換
    uint16_t pulse_us = (uint16_t)(speed_pulse_ms * 1000);

    // 範囲チェック
    if (pulse_us < ESC_MIN_US) pulse_us = ESC_MIN_US;
    if (pulse_us > ESC_MAX_US) pulse_us = ESC_MAX_US;

// PWM出力
#if !DEBUG_MODE
    _escController.writeMicroseconds(pulse_us);
#endif

    Logger::printActuator("ESC", pulse_us);
}

float Actuator::calculateSpeedFromSteering(float steering_angle) {
    // ステアリング連動が無効の場合は固定速度
    if (!SPEED_STEERING_LINK_ENABLED) {
        return TOP_SPEED_PULSE;
    }

    // ステアリング角度の絶対値を取得（左右どちらでも同じ減速）
    float abs_angle = abs(steering_angle);

    // 最大ステアリング角度でクランプ
    if (abs_angle > MAX_STEERING_ANGLE) {
        abs_angle = MAX_STEERING_ANGLE;
    }

    // 0度 → TOP_SPEED_PULSE (1.40ms)
    // 30度 → CORNER_SPEED_PULSE (1.43ms)
    // 線形補間: speed = TOP + (CORNER - TOP) * (angle / MAX_ANGLE)
    float speed_pulse =
        TOP_SPEED_PULSE + (CORNER_SPEED_PULSE - TOP_SPEED_PULSE) *
                              (abs_angle / MAX_STEERING_ANGLE);

    return speed_pulse;
}

void Actuator::stop() { setSpeed(STOP_SPEED_PULSE); }
