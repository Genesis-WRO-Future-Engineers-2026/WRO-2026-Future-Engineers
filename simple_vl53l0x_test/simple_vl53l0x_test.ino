/*
  シンプルなVL53L0Xセンサー読み取りテスト
  TCA9548Aマルチプレクサ経由で1つのセンサーからデータを取得

  接続:
  - TCA9548A I2Cマルチプレクサ (アドレス: 0x70)
  - VL53L0Xセンサー → マルチプレクサのチャンネル0に接続
*/

#include <Wire.h>
#include "Adafruit_VL53L0X.h"

// TCA9548Aマルチプレクサのアドレス
#define TCA9548A_ADDR 0x70

// センサーを接続するチャンネル
#define SENSOR_CHANNEL 0

// VL53L0Xセンサーオブジェクト
Adafruit_VL53L0X lox = Adafruit_VL53L0X();

// 測定データ
VL53L0X_RangingMeasurementData_t measure;

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

  Serial.println("VL53L0X Simple Test with Multiplexer");
  Serial.println("=====================================");

  // マルチプレクサのチャンネルを選択
  tcaSelect(SENSOR_CHANNEL);
  delay(10);

  // センサー初期化
  Serial.print("Initializing sensor on channel ");
  Serial.print(SENSOR_CHANNEL);
  Serial.print("...");

  if (!lox.begin()) {
    Serial.println("FAILED!");
    Serial.println("Check connections!");
    while (1);
  }

  Serial.println("OK!");
  Serial.println();
}

void loop() {
  // チャンネル選択
  tcaSelect(SENSOR_CHANNEL);

  // 距離測定
  lox.rangingTest(&measure, false);

  // 結果表示
  Serial.print("Channel ");
  Serial.print(SENSOR_CHANNEL);
  Serial.print(": ");

  if (measure.RangeStatus != 4) {
    Serial.print(measure.RangeMilliMeter);
    Serial.println(" mm");
  } else {
    Serial.println("Out of range");
  }

  delay(500);
}
