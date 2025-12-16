/*
 * SensorManager.h
 *
 * SensorManagerクラスの宣言
 * 5つのVL53L0Xセンサーを統合管理
 */

#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include <Arduino.h>
#include "Adafruit_VL53L0X.h"
#include "SensorConfig.h"
#include "SensorData.h"

// ============================================================================
// SensorManagerクラス - 5つのセンサーを統合管理
// ============================================================================
class SensorManager {
private:
  // センサーオブジェクト配列
  Adafruit_VL53L0X sensors[NUM_SENSORS];

  // VL53L0X測定データ配列（生データ）
  VL53L0X_RangingMeasurementData_t measurements[NUM_SENSORS];

  // 構造化データ配列（処理済みデータ）
  SensorData sensorData[NUM_SENSORS];

  // プライベートメソッド
  void resetAllSensors();
  void activateSensor(uint8_t sensorId);
  void deactivateSensor(uint8_t sensorId);

public:
  // コンストラクタ
  SensorManager();

  // 初期化処理
  bool begin();

  // 全センサーから距離を読み取る
  void readAllSensors();

  // 指定したセンサーのデータを取得
  SensorData getSensorData(uint8_t sensorId) const;

  // 全センサーのデータ配列を取得
  const SensorData* getAllSensorData() const;

  // 出力メソッド
  void printCompact() const;      // コンパクト表示（1行）
  void printDetailed() const;     // 詳細表示（複数行）
  void printCSV() const;          // CSV形式
  void printJSON() const;         // JSON形式（将来のシリアル通信用）

  // デバッグ用
  void printInitializationStatus() const;
  void printSensorInfo(uint8_t sensorId) const;
};

#endif // SENSOR_MANAGER_H
