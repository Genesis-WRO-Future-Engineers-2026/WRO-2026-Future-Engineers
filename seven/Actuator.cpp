/*
 * Actuator.cpp
 *
 * アクチュエーター制御クラス（実装）
 * サーボ（ステアリング）とESC（速度）のPWM出力
 */

#include "Actuator.h"

#include "Logger.h"

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

void Actuator::stop() { setSpeed(ESC_STOP_US); }
