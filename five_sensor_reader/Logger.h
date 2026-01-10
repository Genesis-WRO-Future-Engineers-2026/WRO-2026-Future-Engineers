/*
 * Logger.h
 *
 * デバッグ出力管理（ヘッダーオンリー）
 * DEBUG_MODEに応じてシリアル出力を制御
 */

#ifndef LOGGER_H
#define LOGGER_H

#include <Arduino.h>

#include "Config.h"

// ============================================================================
// デバッグモードに応じたシリアル出力制御
// ============================================================================
class Logger {
   public:
    // シリアル初期化
    static void begin(unsigned long baud = 9600) {
#if ENABLE_SERIAL
        Serial.begin(baud);
        while (!Serial) {
            delay(10);
        }  // シリアル接続待ち
#endif
#if ENABLE_BLUETOOTH_LOGGING || ENABLE_BLUETOOTH_EMERGENCY
        Serial1.begin(BLUETOOTH_BAUD);
#endif
    }

    // 汎用プリント（改行なし）
    template <typename T>
    static void print(const T& value) {
#if ENABLE_SERIAL
        Serial.print(value);
#endif
#if ENABLE_BLUETOOTH_LOGGING
        Serial1.print(value);
#endif
    }

    // float出力（小数点以下桁数指定）
    static void print(float value, int decimals) {
#if ENABLE_SERIAL
        Serial.print(value, decimals);
#endif
#if ENABLE_BLUETOOTH_LOGGING
        Serial1.print(value, decimals);
#endif
    }

    // 汎用プリント（改行あり）
    template <typename T>
    static void println(const T& value) {
#if ENABLE_SERIAL
        Serial.println(value);
#endif
#if ENABLE_BLUETOOTH_LOGGING
        Serial1.println(value);
#endif
    }

    // 改行のみ（引数なし版）
    static void println() {
#if ENABLE_SERIAL
        Serial.println();
#endif
#if ENABLE_BLUETOOTH_LOGGING
        Serial1.println();
#endif
    }

    // センサーデータのコンパクト表示
    static void printSensorData(uint8_t channel, uint16_t distance,
                                bool valid) {
#if ENABLE_SERIAL
        Serial.print("S");
        Serial.print(channel);
        Serial.print(":");
        if (valid) {
            Serial.print(distance);
        } else {
            Serial.print("---");
        }
#endif
#if ENABLE_BLUETOOTH_LOGGING
        Serial1.print("S");
        Serial1.print(channel);
        Serial1.print(":");
        if (valid) {
            Serial1.print(distance);
        } else {
            Serial1.print("---");
        }
#endif
    }

    // 壁検出状態の表示
    static void printWallStatus(bool left_valid, bool right_valid) {
#if ENABLE_SERIAL
        Serial.print(" | W:");
        Serial.print(left_valid ? "L" : "-");
        Serial.print(right_valid ? "R" : "-");
#endif
#if ENABLE_BLUETOOTH_LOGGING
        Serial1.print(" | W:");
        Serial1.print(left_valid ? "L" : "-");
        Serial1.print(right_valid ? "R" : "-");
#endif
    }

    // 壁までの距離の表示
    static void printWallDistances(bool left_valid, float left_dist,
                                   bool right_valid, float right_dist) {
#if ENABLE_SERIAL
        Serial.print(" D:");
        if (left_valid) {
            Serial.print((int)left_dist);
        } else {
            Serial.print("---");
        }
        Serial.print("/");
        if (right_valid) {
            Serial.print((int)right_dist);
        } else {
            Serial.print("---");
        }
#endif
#if ENABLE_BLUETOOTH_LOGGING
        Serial1.print(" D:");
        if (left_valid) {
            Serial1.print((int)left_dist);
        } else {
            Serial1.print("---");
        }
        Serial1.print("/");
        if (right_valid) {
            Serial1.print((int)right_dist);
        } else {
            Serial1.print("---");
        }
#endif
    }

    // 壁角度の表示
    static void printWallAngles(bool left_valid, float left_angle,
                                bool right_valid, float right_angle) {
#if ENABLE_SERIAL
        Serial.print(" A:");
        if (left_valid) {
            Serial.print(left_angle, 1);
        } else {
            Serial.print("---");
        }
        Serial.print("/");
        if (right_valid) {
            Serial.print(right_angle, 1);
        } else {
            Serial.print("---");
        }
#endif
#if ENABLE_BLUETOOTH_LOGGING
        Serial1.print(" A:");
        if (left_valid) {
            Serial1.print(left_angle, 1);
        } else {
            Serial1.print("---");
        }
        Serial1.print("/");
        if (right_valid) {
            Serial1.print(right_angle, 1);
        } else {
            Serial1.print("---");
        }
#endif
    }

    // ギャップ検出結果の表示
    static void printGapResult(float targetAngle, float farthestDistance) {
#if ENABLE_SERIAL
        Serial.print(" | T:");
        Serial.print(targetAngle, 1);
        Serial.print("° D:");
        Serial.print((int)farthestDistance);
#endif
#if ENABLE_BLUETOOTH_LOGGING
        Serial1.print(" | T:");
        Serial1.print(targetAngle, 1);
        Serial1.print("° D:");
        Serial1.print((int)farthestDistance);
#endif
    }

    // PIDエラー値の表示
    static void printError(float error) {
#if ENABLE_SERIAL
        Serial.print(" E:");
        Serial.print(error, 1);
#endif
#if ENABLE_BLUETOOTH_LOGGING
        Serial1.print(" E:");
        Serial1.print(error, 1);
#endif
    }

    // ステアリング角度の表示（視覚的インジケーター付き）
    static void printSteering(float angle) {
#if ENABLE_SERIAL
        Serial.print(" St:");
        Serial.print(angle, 1);
        Serial.print(" ");

        // 視覚的インジケーター
        if (angle < -5.0) {
            // 左に大きく切る
            int bars = constrain((int)(-angle / 5), 1, 6);
            for (int i = 0; i < bars; ++i) Serial.print("L");
        } else if (angle > 5.0) {
            // 右に大きく切る
            int bars = constrain((int)(angle / 5), 1, 6);
            for (int i = 0; i < bars; ++i) Serial.print("R");
        } else {
            // ほぼ中央
            Serial.print("|");
        }
#endif
#if ENABLE_BLUETOOTH_LOGGING
        Serial1.print(" St:");
        Serial1.print(angle, 1);
        Serial1.print(" ");

        // 視覚的インジケーター
        if (angle < -5.0) {
            int bars = constrain((int)(-angle / 5), 1, 6);
            for (int i = 0; i < bars; ++i) Serial1.print("L");
        } else if (angle > 5.0) {
            int bars = constrain((int)(angle / 5), 1, 6);
            for (int i = 0; i < bars; ++i) Serial1.print("R");
        } else {
            Serial1.print("|");
        }
#endif
    }

    // アクチュエーター情報の表示
    static void printActuator(const char* name, uint16_t pulse_us) {
#if ENABLE_SERIAL
        Serial.print(" [");
        Serial.print(name);
        Serial.print(":");
        Serial.print(pulse_us);
        Serial.print("]");
#endif
#if ENABLE_BLUETOOTH_LOGGING
        Serial1.print(" [");
        Serial1.print(name);
        Serial1.print(":");
        Serial1.print(pulse_us);
        Serial1.print("]");
#endif
    }

    // ループタイミング情報の表示（μs単位）
    static void printLoopTiming(unsigned long loop_us, unsigned long sensor_us) {
#if ENABLE_SERIAL
        Serial.print(" | T:");
        Serial.print(loop_us);
        Serial.print("us(S:");
        Serial.print(sensor_us);
        Serial.print("us)");
#endif
#if ENABLE_BLUETOOTH_LOGGING
        Serial1.print(" | T:");
        Serial1.print(loop_us);
        Serial1.print("us(S:");
        Serial1.print(sensor_us);
        Serial1.print("us)");
#endif
    }

    // タイミング設定のサマリー表示
    static void printTimingConfig() {
#if ENABLE_SERIAL
        Serial.println("--- Timing Configuration ---");
        Serial.print("  L1X Timing Budget: ");
        Serial.print(L1X_TIMING_BUDGET_US);
        Serial.println(" us");
        Serial.print("  L1X Inter-Measurement: ");
        Serial.print(L1X_INTER_MEASUREMENT_MS);
        Serial.println(" ms");
        Serial.print("  Loop Interval: ");
        Serial.print(MEASUREMENT_INTERVAL);
        Serial.println(" ms");
        Serial.print("  Expected Min Loop: ");
        Serial.print(L1X_INTER_MEASUREMENT_MS * NUM_SENSORS);
        Serial.println(" ms (sensor read time)");
        Serial.println("----------------------------");
#endif
#if ENABLE_BLUETOOTH_LOGGING
        Serial1.println("--- Timing Configuration ---");
        Serial1.print("  L1X Timing Budget: ");
        Serial1.print(L1X_TIMING_BUDGET_US);
        Serial1.println(" us");
        Serial1.print("  L1X Inter-Measurement: ");
        Serial1.print(L1X_INTER_MEASUREMENT_MS);
        Serial1.println(" ms");
        Serial1.print("  Loop Interval: ");
        Serial1.print(MEASUREMENT_INTERVAL);
        Serial1.println(" ms");
        Serial1.print("  Expected Min Loop: ");
        Serial1.print(L1X_INTER_MEASUREMENT_MS * NUM_SENSORS);
        Serial1.println(" ms (sensor read time)");
        Serial1.println("----------------------------");
#endif
    }
};

#endif  // LOGGER_H
