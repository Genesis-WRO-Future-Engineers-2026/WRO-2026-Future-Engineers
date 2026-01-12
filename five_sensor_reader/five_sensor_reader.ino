/*
 * five_sensor_reader.ino
 *
 * 5つのVL53L1Xセンサーを使った Follow the Gap + P制御
 *
 * 接続:
 * - TCA9548A I2Cマルチプレクサ (アドレス: 0x70)
 * - VL53L1Xセンサー → マルチプレクサのチャンネル0-4に接続
 * - サーボモーター → Pin 9
 * - ESC → Pin 10
 *
 * 使用方法:
 * 1. Arduino IDEでこのファイルを開く
 * 2. 必要なライブラリをインストール:
 *    - VL53L1X (Pololu)
 *    - Servo (Arduino標準ライブラリ)
 * 3. Config.hでRUN_MODEを設定
 *    - MODE_DEBUG: デバッグ専用（PWMなし、シリアルあり）
 *    - MODE_PRODUCTION: 本番走行（PWMあり、シリアルなし）
 *    - MODE_DEBUG_RUN: デバッグ走行（PWMあり、シリアルあり）
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
    Logger::print("Run Mode: ");
#if RUN_MODE == MODE_DEBUG
    Logger::println("DEBUG (No PWM, Serial ON)");
#elif RUN_MODE == MODE_PRODUCTION
    Logger::println("PRODUCTION (PWM ON, Serial OFF)");
#else
    Logger::println("DEBUG_RUN (PWM ON, Serial ON)");
#endif
    Logger::print("Measurement Interval: ");
    Logger::print(MEASUREMENT_INTERVAL);
    Logger::println("ms");
    Logger::print("Steering Kp: ");
    Logger::println(STEERING_KP);
    Logger::print("Steering Kd: ");
    Logger::println(STEERING_KD);
    Logger::println();

    // タイミング設定のサマリー表示
    Logger::printTimingConfig();
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

    // ESCアーミング待ち
    Logger::println("Waiting 3 seconds for ESC arming...");
    delay(3000);

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

#if ENABLE_BLUETOOTH_EMERGENCY
    // Bluetooth経由で入力があれば緊急停止
    if (Serial1.available()) {
        actuator.setSteering(0.0);
        actuator.stop();
        while (1) {
            delay(1000);
        }  // 終了
    }
#endif

    // 指定した間隔で測定・制御（固定周期を維持）
    if (currentTime - lastMeasurement >= MEASUREMENT_INTERVAL) {
        lastMeasurement += MEASUREMENT_INTERVAL;

        // タイミング計測開始
        unsigned long loopStartUs = micros();

        // =========================================================================
        // Phase 1: センサーデータ取得
        // =========================================================================
        unsigned long sensorStartUs = micros();
        sensorReader.readAll();
        unsigned long sensorEndUs = micros();
        unsigned long sensorElapsedUs = sensorEndUs - sensorStartUs;

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
        // Phase 3: ギャップ検出（最遠+隣接センサー方式）
        // =========================================================================
        GapResult gap = gapFinder.find(sensorData);

        // デバッグ: ギャップ検出結果表示
        Logger::printGapResult(gap.target_angle, gap.farthest_distance);

        // =========================================================================
        // Phase 4: ステアリング角度計算（PD制御 + 直進モード判定）
        // =========================================================================
        float steering_angle = steeringController.calculate(gap, sensorData);

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
            // 通常走行：ステアリング角度とセンサーデータに応じた可変速度
            actuator.setSteering(steering_angle);
            uint16_t variable_speed =
                actuator.calculateSpeed(steering_angle, sensorData);
            actuator.setSpeed(variable_speed);
        }

        // タイミング計測終了・表示
        unsigned long loopEndUs = micros();
        unsigned long loopElapsedUs = loopEndUs - loopStartUs;
        Logger::printLoopTiming(loopElapsedUs, sensorElapsedUs);

        Logger::println("");
    }
}
