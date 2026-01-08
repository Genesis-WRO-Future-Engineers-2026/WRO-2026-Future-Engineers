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

// センサー読み取り用
unsigned long lastSensorRead = 0;
const unsigned long SENSOR_READ_INTERVAL = 60;  // 60msごとに読み取り
uint16_t sensorDistances[NUM_SENSORS] = {0};
bool sensorsReady = false;

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
    if (initSensors()) {
        sensorsReady = true;
    } else {
        Serial.println("ERROR: Sensor init failed! Continuing without sensors.");
        sensorsReady = false;
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
    Serial.println("Waiting 3 seconds for ESC arming...");
    delay(3000);  // ESCアーミング待ち
    Serial.println("Starting sensor-reactive control...");
    Serial.println();
}

// センサー読み取り
void readSensors() {
    for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
        selectChannel(SENSOR_CHANNELS[i]);
        sensors[i].read();
        sensorDistances[i] = sensors[i].ranging_data.range_mm;
        if (sensorDistances[i] > 4000) {
            sensorDistances[i] = 4000;
        }
    }
}

// シリアルプロッター用出力（ラベル:値 形式）
void printForPlotter() {
    Serial.print("S0:");
    Serial.print(sensorDistances[0]);
    Serial.print(",S1:");
    Serial.print(sensorDistances[1]);
    Serial.print(",S2:");
    Serial.print(sensorDistances[2]);
    Serial.print(",S3:");
    Serial.print(sensorDistances[3]);
    Serial.print(",S4:");
    Serial.println(sensorDistances[4]);
}

void loop() {
    unsigned long now = millis();

    // センサー読み取り（60msごと）
    if (sensorsReady && (now - lastSensorRead >= SENSOR_READ_INTERVAL)) {
        lastSensorRead = now;
        readSensors();
        printForPlotter();
    }

    // === センサー反応制御 ===

    // モーター: S2（正面）が1000mm以上なら前進
    if (sensorDistances[2] > 1000) {
        escController.writeMicroseconds(ESC_FORWARD);
    } else {
        escController.writeMicroseconds(ESC_STOP);
    }

    // サーボ: S1（左前）とS3（右前）の大小比較
    if (sensorDistances[1] > sensorDistances[3] + 200) {
        steeringServo.writeMicroseconds(SERVO_MAX);
    } else if (sensorDistances[3] > sensorDistances[1] + 200) {
        steeringServo.writeMicroseconds(SERVO_MIN);
    } else {
        steeringServo.writeMicroseconds(SERVO_CENTER);
    }
}
