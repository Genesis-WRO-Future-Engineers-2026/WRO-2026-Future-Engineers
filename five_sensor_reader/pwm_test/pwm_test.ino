/*
 * pwm_test.ino
 *
 * センサー初期化 + サーボ/ESC同時動作テスト
 * センサーとPWMの干渉を確認する
 */

#include <Servo.h>
#include <Wire.h>
#include <VL53L1X.h>

// ピン設定（Config.hと同じ）
const uint8_t SERVO_PIN = 9;
const uint8_t ESC_PIN = 10;

// パルス幅設定（Config.hと同じ）
const uint16_t SERVO_CENTER = 1500;
const uint16_t SERVO_MIN = 1200;
const uint16_t SERVO_MAX = 1800;
const uint16_t ESC_STOP = 1500;
const uint16_t ESC_FORWARD = 1600;

// センサー設定（Config.hと同じ）
const uint8_t TCA9548A_ADDR = 0x70;
const uint8_t NUM_SENSORS = 5;
const uint8_t SENSOR_CHANNELS[NUM_SENSORS] = {0, 1, 2, 3, 4};
const float SENSOR_ANGLES[NUM_SENSORS] = {-70.0, -20.0, 0.0, 20.0, 70.0};
const uint32_t L1X_TIMING_BUDGET_US = 50000;
const uint32_t L1X_INTER_MEASUREMENT_MS = 50;

Servo steeringServo;
Servo escController;
VL53L1X sensors[NUM_SENSORS];

int testStep = 0;
unsigned long lastStepTime = 0;
const unsigned long STEP_INTERVAL = 2000;  // 2秒ごとにステップ進行

// TCA9548Aチャンネル選択
void selectChannel(uint8_t channel) {
    if (channel > 7) return;
    Wire.beginTransmission(TCA9548A_ADDR);
    Wire.write(1 << channel);
    Wire.endTransmission();
}

// センサー初期化
bool initSensors() {
    Wire.begin();
    Wire.setClock(400000);  // I2C高速モード

    Serial.println("=== VL53L1X Sensor Initialization ===");

    for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
        selectChannel(SENSOR_CHANNELS[i]);
        delay(10);

        Serial.print("Sensor ");
        Serial.print(i);
        Serial.print(" (Ch");
        Serial.print(SENSOR_CHANNELS[i]);
        Serial.print(", ");
        Serial.print(SENSOR_ANGLES[i]);
        Serial.print("deg)...");

        sensors[i].setTimeout(500);
        if (!sensors[i].init()) {
            Serial.println(" FAILED!");
            return false;
        }

        sensors[i].setDistanceMode(VL53L1X::Long);
        sensors[i].setMeasurementTimingBudget(L1X_TIMING_BUDGET_US);
        sensors[i].startContinuous(L1X_INTER_MEASUREMENT_MS);

        Serial.println(" OK");
    }

    Serial.println("=== All sensors initialized ===");
    return true;
}

void setup() {
    Serial.begin(115200);
    while (!Serial) { delay(10); }

    Serial.println("========================================");
    Serial.println("  PWM + Sensor Test");
    Serial.println("========================================");
    Serial.println();

    // === センサー初期化 ===
    Serial.println("[PHASE 1] Initializing Sensors...");
    if (!initSensors()) {
        Serial.println("ERROR: Sensor init failed! Continuing without sensors.");
    }
    Serial.println();

    // === サーボ/ESC初期化 ===
    Serial.println("[PHASE 2] Initializing Servo/ESC...");
    Serial.print("Servo Pin: "); Serial.println(SERVO_PIN);
    Serial.print("ESC Pin: "); Serial.println(ESC_PIN);

    Serial.println("[INIT] Attaching Servo...");
    steeringServo.attach(SERVO_PIN);
    Serial.println("[INIT] Servo attached");

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
    Serial.println("=== All Initialization Complete ===");
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
