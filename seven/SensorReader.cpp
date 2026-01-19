/*
 * SensorReader.cpp
 *
 * センサー読み取りクラス（実装）
 */

#include "SensorReader.h"

#include "Logger.h"

SensorReader::SensorReader() {
    // 初期化
    for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
        _sensorData[i].distance = 0;
        _sensorData[i].valid = false;
    }
}

void SensorReader::_selectChannel(uint8_t channel) {
    if (channel > 7) return;

    Wire.beginTransmission(TCA9548A_ADDR);
    Wire.write(1 << channel);
    Wire.endTransmission();
}

bool SensorReader::begin() {
    Wire.begin();
    Wire.setClock(400000);  // I2C高速モード（400kHz）

    Logger::println("=== VL53L1X Sensor Initialization ===");

    // 各センサーを初期化
    for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
        _selectChannel(SENSOR_CHANNELS[i]);
        delay(10);  // チャンネル切替後の安定待ち

        Logger::print("Sensor ");
        Logger::print(i);
        Logger::print(" (Ch");
        Logger::print(SENSOR_CHANNELS[i]);
        Logger::print(", ");
        Logger::print(SENSOR_ANGLES[i]);
        Logger::print("deg)...");

        _sensors[i].setTimeout(500);
        if (!_sensors[i].init()) {
            Logger::println(" FAILED!");
            return false;
        }

        // VL53L1X設定: 長距離モード、測定時間50ms
        _sensors[i].setDistanceMode(VL53L1X::Long);
        _sensors[i].setMeasurementTimingBudget(L1X_TIMING_BUDGET_US);

        // 連続測定モード開始
        _sensors[i].startContinuous(L1X_INTER_MEASUREMENT_MS);

        Logger::println(" OK");
    }

    Logger::println("=== All VL53L1X sensors initialized ===");
    return true;
}

void SensorReader::readAll() {
    for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
        _selectChannel(SENSOR_CHANNELS[i]);

        // VL53L1Xから読み取り（連続測定モード）
        _sensors[i].read();

        // 距離データを取得
        _sensorData[i].distance = _sensors[i].ranging_data.range_mm;

        // デバッグ: 全センサーのステータスを表示
#if ENABLE_SERIAL
        Serial.print("[");
        Serial.print(i);
        Serial.print(":");
        Serial.print(_sensors[i].ranging_data.range_status);
        Serial.print(",");
        Serial.print(_sensors[i].ranging_data.peak_signal_count_rate_MCPS);
        Serial.print(",");
        Serial.print(_sensors[i].ranging_data.ambient_count_rate_MCPS);
        Serial.print("]");
#endif

        if(_sensorData[i].distance > RELIABLE_RANGE) {
            // VL53L1Xの信頼できる測定範囲を超えた場合は上限値にクランプ
            _sensorData[i].distance = RELIABLE_RANGE;
        }
        _sensorData[i].valid =
            (_sensorData[i].distance >= MIN_VALID_DISTANCE) &&
            (_sensorData[i].distance <= RELIABLE_RANGE);
    }
}

SensorData SensorReader::getSensorData(uint8_t index) const {
    if (index < NUM_SENSORS) {
        return _sensorData[index];
    }
    SensorData empty = {0, false};
    return empty;
}

const SensorData* SensorReader::getAllData() const { return _sensorData; }
