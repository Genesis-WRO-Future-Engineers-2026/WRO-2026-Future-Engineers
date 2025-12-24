/*
 * five_sensor_reader.ino
 *
 * 5つのVL53L1Xセンサーを使った Follow the Gap + P制御
 *
 * 接続:
 * - TCA9548A I2Cマルチプレクサ (アドレス: 0x70)
 * - VL53L0Xセンサー → マルチプレクサのチャンネル0-4に接続
 * - サーボモーター → Pin 9
 * - ESC → Pin 10
 *
 * 使用方法:
 * 1. Arduino IDEでこのファイルを開く
 * 2. 必要なライブラリをインストール:
 *    - Adafruit_VL53L0X
 *    - Servo (Arduino標準ライブラリ)
 * 3. Config.hでDEBUG_MODEを設定
 *    - true: デバッグ（PWMなし、シリアル出力あり）
 *    - false: 実機（PWMあり、シリアル出力なし）
 * 4. Arduino Nano R4に書き込み
 */

#include "Actuator.h"
#include "Config.h"
#include "GapFinder.h"
#include "Logger.h"
#include "SensorReader.h"
#include "SteeringController.h"

// ============================================================================
// グローバルオブジェクト
// ============================================================================
SensorReader sensorReader;
GapFinder gapFinder;
SteeringController steeringController;
Actuator actuator;

// ============================================================================
// Setup関数
// ============================================================================
void setup() {
    // ロガー初期化（115200bpsで詳細データ表示）
    Logger::begin(115200);

    Logger::println("==========================================");
    Logger::println("  VL53L1X Follow the Gap + P Control");
    Logger::println("==========================================");
    Logger::print("Debug Mode: ");
    Logger::println(DEBUG_MODE ? "ON (No PWM)" : "OFF (PWM Active)");
    Logger::print("Measurement Interval: ");
    Logger::print(MEASUREMENT_INTERVAL);
    Logger::println("ms");
    Logger::print("Steering Kp: ");
    Logger::println(STEERING_KP);
    Logger::print("Obstacle Threshold: ");
    Logger::print(OBSTACLE_THRESHOLD);
    Logger::println("mm");
    Logger::println();

    // センサー初期化
    if (!sensorReader.begin()) {
        Logger::println("ERROR: Sensor initialization failed!");
        while (1) {
            delay(100);
        }
    }

    // ステアリングコントローラー初期化
    steeringController.begin();

    // アクチュエーター初期化
    actuator.begin();

    Logger::println();
    Logger::println("System ready!");
    Logger::println();
}

// ============================================================================
// Loop関数
// ============================================================================
void loop() {
    static unsigned long lastMeasurement = 0;
    unsigned long currentTime = millis();

    // 指定した間隔で測定・制御（固定周期を維持）
    if (currentTime - lastMeasurement >= MEASUREMENT_INTERVAL) {
        lastMeasurement += MEASUREMENT_INTERVAL;

        // =========================================================================
        // Phase 1: センサーデータ取得
        // =========================================================================
        sensorReader.readAll();
        const SensorData* sensorData = sensorReader.getAllData();

        // デバッグ: センサーデータ表示
        for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
            Logger::printSensorData(SENSOR_CHANNELS[i], sensorData[i].distance,
                                    sensorData[i].valid);
            if (i < NUM_SENSORS - 1) {
                Logger::print(" | ");
            }
        }

        // =========================================================================
        // Phase 2: 緊急停止チェック（前方障害物検出）
        // =========================================================================
        bool emergency_stop = false;
        if (sensorData[2].valid &&
            sensorData[2].distance < EMERGENCY_FRONT_THRESHOLD) {
            emergency_stop = true;
            Logger::print(" | EMERGENCY!");
        }

        // =========================================================================
        // Phase 3: ギャップ検出（Follow the Gap）
        // =========================================================================
        GapResult gap = gapFinder.find(sensorData);

        // デバッグ: ギャップ検出結果表示
        Logger::printGapResult(gap.num_gaps, gap.target_angle,
                               gap.has_valid_gap);
        if (gap.has_valid_gap) {
            Logger::printGapDetail(gap.best_gap.center_angle,
                                   gap.best_gap.width_angle,
                                   gap.best_gap.min_distance);
        }

        // =========================================================================
        // Phase 4: ステアリング角度計算（P制御）
        // =========================================================================
        float steering_angle = steeringController.calculate(gap);

        // デバッグ: 目標角度とステアリング表示
        Logger::printSteering(steering_angle);

        // =========================================================================
        // Phase 5: アクチュエーター制御
        // =========================================================================
        if (emergency_stop) {
            // 緊急停止：中央ステアリング + 停止
            actuator.setSteering(0.0);
            actuator.stop();
        } else {
            // 通常走行
            actuator.setSteering(steering_angle);
            actuator.setSpeed(BASE_SPEED_PULSE);
        }

        Logger::println("");
    }
}
