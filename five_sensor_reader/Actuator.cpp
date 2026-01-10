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
#if !DEBUG_MODE
    _steeringServo.writeMicroseconds(pulse_us);
#endif

    Logger::printActuator("Servo", pulse_us);
}

void Actuator::setSpeed(uint16_t pulse_us) {
    // 範囲チェック
    if (pulse_us < ESC_MIN_US) pulse_us = ESC_MIN_US;
    if (pulse_us > ESC_MAX_US) pulse_us = ESC_MAX_US;

// PWM出力
#if !DEBUG_MODE
    _escController.writeMicroseconds(pulse_us);
#endif

    Logger::printActuator("ESC", pulse_us);
}

uint16_t Actuator::calculateSpeedFromSteering(float steering_angle) {
    // ステアリング連動が無効の場合は固定速度
    if (!SPEED_STEERING_LINK_ENABLED) {
        return TOP_SPEED_US;
    }

    // ステアリング角度の絶対値を取得（左右どちらでも同じ減速）
    float abs_angle = abs(steering_angle);

    // デッドゾーン内では最速維持（小角度での無駄な減速を回避）
    if (abs_angle <= STEERING_DEADZONE) {
        return TOP_SPEED_US;
    }

    // デッドゾーン以降の有効角度を計算
    float effective_angle = abs_angle - STEERING_DEADZONE;
    float effective_max = MAX_STEERING_ANGLE - STEERING_DEADZONE;

    // 最大角度でクランプ
    if (effective_angle > effective_max) {
        effective_angle = effective_max;
    }

    // 二次関数で大角度ほど急激に減速
    // 5度以下  → 1580μs（最速）
    // 20度    → 1520μs（最大減速）
    float ratio = effective_angle / effective_max;
    uint16_t speed_us =
        TOP_SPEED_US +
        (uint16_t)((CORNER_SPEED_US - TOP_SPEED_US) * ratio * ratio);

    return speed_us;
}

void Actuator::stop() { setSpeed(ESC_STOP_US); }
