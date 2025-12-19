/*
  シンプルなVL53L0Xセンサー読み取りテスト
  TCA9548Aマルチプレクサ経由で2つのセンサーからデータを取得

  接続:
  - TCA9548A I2Cマルチプレクサ (アドレス: 0x70)
  - VL53L0Xセンサー1 → マルチプレクサのチャンネル0に接続
  - VL53L0Xセンサー2 → マルチプレクサのチャンネル1に接続
*/

#include <Wire.h>
#include "Adafruit_VL53L0X.h"

// TCA9548Aマルチプレクサのアドレス
#define TCA9548A_ADDR 0x70

// センサーを接続するチャンネル
#define SENSOR1_CHANNEL 0
#define SENSOR2_CHANNEL 1

// VL53L0Xセンサーオブジェクト
Adafruit_VL53L0X lox1 = Adafruit_VL53L0X();
Adafruit_VL53L0X lox2 = Adafruit_VL53L0X();

// 測定データ
VL53L0X_RangingMeasurementData_t measure1;
VL53L0X_RangingMeasurementData_t measure2;

/**
 * TCA9548Aマルチプレクサのチャンネルを選択
 */
void tcaSelect(uint8_t channel) {
  if (channel > 7) return;

  Wire.beginTransmission(TCA9548A_ADDR);
  Wire.write(1 << channel);
  Wire.endTransmission();
}

void setup() {
  Serial.begin(9600);
  Wire.begin();

  Serial.println("VL53L0X Dual Sensor Test with Multiplexer");
  Serial.println("==========================================");

  // センサー1の初期化
  tcaSelect(SENSOR1_CHANNEL);
  delay(10);

  Serial.print("Initializing sensor 1 on channel ");
  Serial.print(SENSOR1_CHANNEL);
  Serial.print("...");

  if (!lox1.begin()) {
    Serial.println("FAILED!");
    Serial.println("Check sensor 1 connections!");
    while (1);
  }

  Serial.println("OK!");

  // センサー2の初期化
  tcaSelect(SENSOR2_CHANNEL);
  delay(10);

  Serial.print("Initializing sensor 2 on channel ");
  Serial.print(SENSOR2_CHANNEL);
  Serial.print("...");

  if (!lox2.begin()) {
    Serial.println("FAILED!");
    Serial.println("Check sensor 2 connections!");
    while (1);
  }

  Serial.println("OK!");
  Serial.println();
}

void loop() {
  // センサー1の測定
  tcaSelect(SENSOR1_CHANNEL);
  lox1.rangingTest(&measure1, false);

  // センサー2の測定
  tcaSelect(SENSOR2_CHANNEL);
  lox2.rangingTest(&measure2, false);

  // 結果表示
  Serial.print("Ch");
  Serial.print(SENSOR1_CHANNEL);
  Serial.print(": ");

  if (measure1.RangeStatus != 4) {
    Serial.print(measure1.RangeMilliMeter);
    Serial.print(" mm");
  } else {
    Serial.print("Out of range");
  }

  Serial.print("  |  ");

  Serial.print("Ch");
  Serial.print(SENSOR2_CHANNEL);
  Serial.print(": ");

  if (measure2.RangeStatus != 4) {
    Serial.print(measure2.RangeMilliMeter);
    Serial.print(" mm");
  } else {
    Serial.print("Out of range");
  }

  Serial.println();

  delay(500);
}
