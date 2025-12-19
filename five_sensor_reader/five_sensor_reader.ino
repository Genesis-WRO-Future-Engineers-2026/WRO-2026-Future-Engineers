/*
 * five_sensor_reader.ino
 *
 * 5つのVL53L0Xセンサーから距離データを読み取り、
 * 将来的にステアリングサーボとモーターへパルス出力を行うメインプログラム
 *
 * 接続:
 * - TCA9548A I2Cマルチプレクサ (アドレス: 0x70)
 * - VL53L0Xセンサー → マルチプレクサのチャンネル0, 1, 2, 3, 4に接続
 *
 * 使用方法:
 * 1. Arduino IDEでこのファイルを開く
 * 2. 必要なライブラリをインストール:
 *    - Adafruit_VL53L0X
 * 3. Arduino Nano R4に書き込み
 * 4. シリアルモニタ（9600bps）で確認
 */

#include <Wire.h>
#include "Adafruit_VL53L0X.h"

// ============================================================================
// TCA9548Aマルチプレクサ設定
// ============================================================================
#define TCA9548A_ADDR 0x70

// ============================================================================
// センサー設定
// ============================================================================
#define NUM_SENSORS 5

// 各センサーが接続されているチャンネル
const uint8_t sensorChannels[NUM_SENSORS] = {0, 1, 2, 3, 4};

// VL53L0Xセンサーオブジェクトの配列
Adafruit_VL53L0X sensors[NUM_SENSORS];

// 測定データの配列
VL53L0X_RangingMeasurementData_t measurements[NUM_SENSORS];

// ============================================================================
// 測定間隔設定
// ============================================================================
const unsigned long MEASUREMENT_INTERVAL = 100;  // 100ms = 10Hz

// ============================================================================
// ヘルパー関数
// ============================================================================

/**
 * TCA9548Aマルチプレクサのチャンネルを選択
 */
void tcaSelect(uint8_t channel) {
  if (channel > 7) return;

  Wire.beginTransmission(TCA9548A_ADDR);
  Wire.write(1 << channel);
  Wire.endTransmission();
}

// ============================================================================
// Setup関数
// ============================================================================
void setup() {
  // シリアル通信開始
  Serial.begin(9600);
  Wire.begin();

  Serial.print("VL53L0X Test with ");
  Serial.print(NUM_SENSORS);
  Serial.println(" Sensors");
  Serial.println("==========================================");

  // 全センサーを初期化
  for (int i = 0; i < NUM_SENSORS; ++i) {
    tcaSelect(sensorChannels[i]);
    delay(1000);

    Serial.print("Initializing sensor ");
    Serial.print(i);
    Serial.print(" on channel ");
    Serial.print(sensorChannels[i]);
    Serial.print("...");

    if (!sensors[i].begin()) {
      Serial.println("FAILED!");
      Serial.print("Check sensor ");
      Serial.print(i);
      Serial.println(" connections!");
      while (1);
    }

    Serial.println("OK!");
  }

  Serial.println();
  Serial.println("Initialization complete!");
  Serial.println("Starting continuous measurement...\n");
}

// ============================================================================
// Loop関数
// ============================================================================
void loop() {
  static unsigned long lastMeasurement = 0;
  unsigned long currentTime = millis();

  // 指定した間隔で測定
  if (currentTime - lastMeasurement >= MEASUREMENT_INTERVAL) {
    lastMeasurement = currentTime;

    // 全センサーから測定
    for (int i = 0; i < NUM_SENSORS; ++i) {
      tcaSelect(sensorChannels[i]);
      sensors[i].rangingTest(&measurements[i], false);
    }

    // 結果表示
    for (int i = 0; i < NUM_SENSORS; ++i) {
      Serial.print("Ch");
      Serial.print(sensorChannels[i]);
      Serial.print(": ");

      if (measurements[i].RangeStatus != 4) {
        Serial.print(measurements[i].RangeMilliMeter);
        Serial.print(" mm");
      } else {
        Serial.print("Out of range");
      }

      // 最後のセンサー以外は区切り文字を表示
      if (i < NUM_SENSORS - 1) {
        Serial.print("  |  ");
      }
    }

    Serial.println();

    // TODO: ここに将来パルス出力処理を追加
    // - センサーデータから壁までの距離を判断
    // - ステアリング角度を計算
    // - サーボへのPWM信号出力
    // - モーターへのPWM信号出力
  }
}
