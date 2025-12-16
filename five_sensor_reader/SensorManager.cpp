/*
 * SensorManager.cpp
 *
 * SensorManagerクラスの実装
 */

#include "SensorManager.h"

// ============================================================================
// コンストラクタ
// ============================================================================
SensorManager::SensorManager() {
  // センサーデータの初期化
  for (int i = 0; i < NUM_SENSORS; i++) {
    sensorData[i] = SensorData(i, SENSOR_ANGLES[i]);
  }
}

// ============================================================================
// プライベートメソッド
// ============================================================================

/*
 * 全センサーのシャットダウンピンをLOWにしてリセット
 */
void SensorManager::resetAllSensors() {
  for (int i = 0; i < NUM_SENSORS; i++) {
    digitalWrite(SHUTDOWN_PINS[i], LOW);
  }
  delay(10);
}

/*
 * 指定したセンサーを起動
 */
void SensorManager::activateSensor(uint8_t sensorId) {
  if (sensorId < NUM_SENSORS) {
    digitalWrite(SHUTDOWN_PINS[sensorId], HIGH);
    delay(10);
  }
}

/*
 * 指定したセンサーをシャットダウン
 */
void SensorManager::deactivateSensor(uint8_t sensorId) {
  if (sensorId < NUM_SENSORS) {
    digitalWrite(SHUTDOWN_PINS[sensorId], LOW);
    delay(10);
  }
}

// ============================================================================
// パブリックメソッド
// ============================================================================

/*
 * 初期化処理
 * 全センサーを順番に起動し、I2Cアドレスを設定
 *
 * 戻り値: 初期化成功時true、失敗時false
 */
bool SensorManager::begin() {
  Serial.println(F("=== Sensor Manager Initialization ==="));

  // シャットダウンピンの設定
  for (int i = 0; i < NUM_SENSORS; i++) {
    pinMode(SHUTDOWN_PINS[i], OUTPUT);
  }
  Serial.println(F("✓ Shutdown pins configured"));

  // 全センサーをリセット
  resetAllSensors();
  Serial.println(F("✓ All sensors reset"));

  // 各センサーを順番に初期化
  for (int i = 0; i < NUM_SENSORS; i++) {
    Serial.print(F("Initializing Sensor "));
    Serial.print(i + 1);
    Serial.print(F(" ["));
    Serial.print(SENSOR_NAMES[i]);
    Serial.print(F(", "));

    // 角度表示（符号付き）
    if (SENSOR_ANGLES[i] >= 0) {
      Serial.print(F("+"));
    }
    Serial.print(SENSOR_ANGLES[i], 0);
    Serial.print(F("°, 0x"));
    Serial.print(SENSOR_ADDRESSES[i], HEX);
    Serial.print(F("]... "));

    // このセンサーのみ起動
    activateSensor(i);

    // I2Cアドレスを設定して初期化
    if (!sensors[i].begin(SENSOR_ADDRESSES[i])) {
      Serial.println(F("❌ FAILED!"));
      Serial.print(F("Error: Sensor "));
      Serial.print(i + 1);
      Serial.println(F(" initialization failed."));
      Serial.println(F("Check I2C connection and power supply."));
      return false;
    }

    Serial.println(F("✓ OK"));
  }

  Serial.println(F("=== All sensors initialized successfully ==="));
  return true;
}

/*
 * 全センサーから距離を読み取る
 */
void SensorManager::readAllSensors() {
  for (int i = 0; i < NUM_SENSORS; i++) {
    // 測定実行
    sensors[i].rangingTest(&measurements[i], false);

    // データを構造体に格納
    sensorData[i].rangeStatus = measurements[i].RangeStatus;

    // RangeStatus == 0 が正常測定
    // RangeStatus == 4 が測定範囲外
    if (measurements[i].RangeStatus != 4) {
      sensorData[i].distance = measurements[i].RangeMilliMeter;
      sensorData[i].isValid = true;
    } else {
      sensorData[i].distance = 0;
      sensorData[i].isValid = false;
    }
  }
}

/*
 * 指定したセンサーのデータを取得
 */
SensorData SensorManager::getSensorData(uint8_t sensorId) const {
  if (sensorId < NUM_SENSORS) {
    return sensorData[sensorId];
  }
  return SensorData();  // 無効なIDの場合は空データを返す
}

/*
 * 全センサーのデータ配列を取得
 */
const SensorData* SensorManager::getAllSensorData() const {
  return sensorData;
}

// ============================================================================
// 出力メソッド
// ============================================================================

/*
 * 全センサーのデータをシリアル出力（1行形式）
 */
void SensorManager::printCompact() const {
  for (int i = 0; i < NUM_SENSORS; i++) {
    Serial.print(F("S"));
    Serial.print(i + 1);
    Serial.print(F(":"));

    if (sensorData[i].isValid) {
      // 距離を4桁で右詰め表示
      if (sensorData[i].distance < 1000) {
        Serial.print(F(" "));
        if (sensorData[i].distance < 100) {
          Serial.print(F(" "));
          if (sensorData[i].distance < 10) {
            Serial.print(F(" "));
          }
        }
      }
      Serial.print(sensorData[i].distance);
      Serial.print(F("mm"));
    } else {
      Serial.print(F("  ---"));
    }

    if (i < NUM_SENSORS - 1) {
      Serial.print(F(" | "));
    }
  }
  Serial.println();
}

/*
 * 全センサーのデータを詳細表示
 */
void SensorManager::printDetailed() const {
  Serial.println(F("╔═══════════════════════════════════════╗"));
  Serial.println(F("║         Sensor Readings               ║"));
  Serial.println(F("╠═══════════════════════════════════════╣"));

  for (int i = 0; i < NUM_SENSORS; i++) {
    Serial.print(F("║ Sensor "));
    Serial.print(i + 1);
    Serial.print(F(" ["));
    Serial.print(SENSOR_NAMES[i]);

    // スペース調整（名前の長さに応じて）
    int nameLen = strlen(SENSOR_NAMES[i]);
    for (int j = 0; j < (11 - nameLen); j++) {
      Serial.print(F(" "));
    }
    Serial.print(F("] "));

    // 角度表示（符号付き、3桁固定）
    if (sensorData[i].angle >= 0) {
      Serial.print(F("+"));
    }
    if (abs(sensorData[i].angle) < 10) {
      Serial.print(F(" "));
    }
    Serial.print(sensorData[i].angle, 0);
    Serial.print(F("° ║\n"));

    Serial.print(F("║   Distance: "));
    if (sensorData[i].isValid) {
      // 距離を4桁で右詰め表示
      if (sensorData[i].distance < 1000) Serial.print(F(" "));
      if (sensorData[i].distance < 100) Serial.print(F(" "));
      if (sensorData[i].distance < 10) Serial.print(F(" "));
      Serial.print(sensorData[i].distance);
      Serial.print(F(" mm"));
    } else {
      Serial.print(F(" Out of range       "));
    }
    Serial.print(F("  Status: "));
    Serial.print(sensorData[i].rangeStatus);
    Serial.println(F("      ║"));

    if (i < NUM_SENSORS - 1) {
      Serial.println(F("╟───────────────────────────────────────╢"));
    }
  }

  Serial.println(F("╚═══════════════════════════════════════╝"));
}

/*
 * CSV形式で出力（データ解析用）
 */
void SensorManager::printCSV() const {
  for (int i = 0; i < NUM_SENSORS; i++) {
    Serial.print(sensorData[i].distance);
    if (i < NUM_SENSORS - 1) {
      Serial.print(F(","));
    }
  }
  Serial.println();
}

/*
 * JSON形式で出力（将来のシリアル通信用）
 */
void SensorManager::printJSON() const {
  Serial.print(F("{\"sensors\":["));
  for (int i = 0; i < NUM_SENSORS; i++) {
    Serial.print(F("{\"id\":"));
    Serial.print(sensorData[i].id);
    Serial.print(F(",\"angle\":"));
    Serial.print(sensorData[i].angle);
    Serial.print(F(",\"distance\":"));
    Serial.print(sensorData[i].distance);
    Serial.print(F(",\"valid\":"));
    Serial.print(sensorData[i].isValid ? F("true") : F("false"));
    Serial.print(F(",\"status\":"));
    Serial.print(sensorData[i].rangeStatus);
    Serial.print(F("}"));
    if (i < NUM_SENSORS - 1) {
      Serial.print(F(","));
    }
  }
  Serial.println(F("]}"));
}

// ============================================================================
// デバッグ用メソッド
// ============================================================================

/*
 * 初期化状態を表示
 */
void SensorManager::printInitializationStatus() const {
  Serial.println(F("=== Sensor Configuration ==="));
  for (int i = 0; i < NUM_SENSORS; i++) {
    Serial.print(F("Sensor "));
    Serial.print(i + 1);
    Serial.print(F(": Pin="));
    Serial.print(SHUTDOWN_PINS[i]);
    Serial.print(F(", Addr=0x"));
    Serial.print(SENSOR_ADDRESSES[i], HEX);
    Serial.print(F(", Angle="));
    Serial.print(SENSOR_ANGLES[i]);
    Serial.println(F("°"));
  }
  Serial.println(F("==========================="));
}

/*
 * 特定のセンサー情報を表示
 */
void SensorManager::printSensorInfo(uint8_t sensorId) const {
  if (sensorId >= NUM_SENSORS) {
    Serial.println(F("Error: Invalid sensor ID"));
    return;
  }

  Serial.print(F("Sensor "));
  Serial.print(sensorId + 1);
  Serial.println(F(" Information:"));
  Serial.print(F("  Name: "));
  Serial.println(SENSOR_NAMES[sensorId]);
  Serial.print(F("  Angle: "));
  Serial.print(SENSOR_ANGLES[sensorId]);
  Serial.println(F("°"));
  Serial.print(F("  I2C Address: 0x"));
  Serial.println(SENSOR_ADDRESSES[sensorId], HEX);
  Serial.print(F("  Shutdown Pin: "));
  Serial.println(SHUTDOWN_PINS[sensorId]);
  Serial.print(F("  Current Distance: "));
  if (sensorData[sensorId].isValid) {
    Serial.print(sensorData[sensorId].distance);
    Serial.println(F(" mm"));
  } else {
    Serial.println(F("Invalid"));
  }
  Serial.print(F("  Range Status: "));
  Serial.println(sensorData[sensorId].rangeStatus);
}
