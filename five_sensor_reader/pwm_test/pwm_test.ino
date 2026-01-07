/*
 * pwm_test.ino
 *
 * 最小構成テスト: センサーなし、サーボとESCのみ
 * palse_check.inoと同じ構成で five_sensor_reader の設定値を使う
 */

#include <Servo.h>

// ピン設定（Config.hと同じ）
const uint8_t SERVO_PIN = 9;
const uint8_t ESC_PIN = 10;

// パルス幅設定（Config.hと同じ）
const uint16_t SERVO_CENTER = 1500;
const uint16_t SERVO_MIN = 1200;
const uint16_t SERVO_MAX = 1800;
const uint16_t ESC_STOP = 1500;
const uint16_t ESC_FORWARD = 1600;

Servo steeringServo;
Servo escController;

int testStep = 0;
unsigned long lastStepTime = 0;
const unsigned long STEP_INTERVAL = 2000;  // 2秒ごとにステップ進行

void setup() {
    Serial.begin(115200);
    while (!Serial) { delay(10); }

    Serial.println("========================================");
    Serial.println("  PWM Minimal Test (No Sensors)");
    Serial.println("========================================");
    Serial.println();
    Serial.print("Servo Pin: "); Serial.println(SERVO_PIN);
    Serial.print("ESC Pin: "); Serial.println(ESC_PIN);
    Serial.println();

    // サーボ初期化
    Serial.println("[INIT] Attaching Servo...");
    steeringServo.attach(SERVO_PIN);
    Serial.println("[INIT] Servo attached");

    // ESC初期化
    Serial.println("[INIT] Attaching ESC...");
    escController.attach(ESC_PIN);
    Serial.println("[INIT] ESC attached");

    // 初期位置設定
    Serial.println("[INIT] Setting initial positions...");
    steeringServo.writeMicroseconds(SERVO_CENTER);
    escController.writeMicroseconds(ESC_STOP);
    Serial.print("[INIT] Servo: "); Serial.print(SERVO_CENTER); Serial.println(" us");
    Serial.print("[INIT] ESC: "); Serial.print(ESC_STOP); Serial.println(" us");

    Serial.println();
    Serial.println("=== Initialization Complete ===");
    Serial.println("Starting test sequence in 2 seconds...");
    Serial.println();

    lastStepTime = millis();
}

void loop() {
    unsigned long now = millis();

    if (now - lastStepTime >= STEP_INTERVAL) {
        lastStepTime = now;

        switch (testStep) {
            // === 単体テスト ===
            case 0:
                Serial.println("[TEST 1/9] Servo RIGHT (1200us)");
                steeringServo.writeMicroseconds(SERVO_MIN);
                break;

            case 1:
                Serial.println("[TEST 2/9] Servo CENTER (1500us)");
                steeringServo.writeMicroseconds(SERVO_CENTER);
                break;

            case 2:
                Serial.println("[TEST 3/9] Servo LEFT (1800us)");
                steeringServo.writeMicroseconds(SERVO_MAX);
                break;

            case 3:
                Serial.println("[TEST 4/9] Servo CENTER (1500us)");
                steeringServo.writeMicroseconds(SERVO_CENTER);
                break;

            case 4:
                Serial.println("[TEST 5/9] ESC FORWARD (1600us)");
                escController.writeMicroseconds(ESC_FORWARD);
                break;

            case 5:
                Serial.println("[TEST 6/9] ESC STOP (1500us)");
                escController.writeMicroseconds(ESC_STOP);
                break;

            // === 同時動作テスト ===
            case 6:
                Serial.println("[TEST 7/9] SIMULTANEOUS: Servo LEFT + ESC FORWARD");
                steeringServo.writeMicroseconds(SERVO_MAX);
                escController.writeMicroseconds(ESC_FORWARD);
                break;

            case 7:
                Serial.println("[TEST 8/9] SIMULTANEOUS: Servo RIGHT + ESC FORWARD");
                steeringServo.writeMicroseconds(SERVO_MIN);
                escController.writeMicroseconds(ESC_FORWARD);
                break;

            case 8:
                Serial.println("[TEST 9/9] SIMULTANEOUS: Servo CENTER + ESC STOP");
                steeringServo.writeMicroseconds(SERVO_CENTER);
                escController.writeMicroseconds(ESC_STOP);
                break;

            case 9:
                Serial.println();
                Serial.println("=== Test Complete! Restarting... ===");
                Serial.println();
                testStep = -1;
                break;
        }

        testStep++;
    }
}
