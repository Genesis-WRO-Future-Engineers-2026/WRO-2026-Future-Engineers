/*
 * five_sensor_reader.ino
 *
 * 5つのVL53L0Xセンサーから距離データを読み取るメインプログラム
 *
 * 使用方法:
 * 1. Arduino IDEでこのファイルを開く
 * 2. 必要なライブラリをインストール:
 *    - Adafruit_VL53L0X
 * 3. Arduino Nano R4に書き込み
 * 4. シリアルモニタ（115200bps）で確認
 *
 * 出力形式の切り替え:
 * - COMPACT: 1行表示（デフォルト）
 * - DETAILED: 詳細表示
 * - CSV: データ解析用
 * - JSON: シリアル通信用
 */

#include "SensorManager.h"

// ============================================================================
// グローバル変数
// ============================================================================
SensorManager sensorManager;

// ============================================================================
// 出力モード設定
// ============================================================================
enum OutputMode {
  COMPACT,   // コンパクト表示（1行）
  DETAILED,  // 詳細表示（複数行）
  CSV,       // CSV形式
  JSON       // JSON形式
};

// 使用する出力モードを選択（デフォルト: COMPACT）
const OutputMode OUTPUT_MODE = COMPACT;

// 測定間隔（ミリ秒）
const unsigned long MEASUREMENT_INTERVAL = 100;  // 100ms = 10Hz

// ============================================================================
// Setup関数
// ============================================================================
void setup() {
  // シリアル通信開始
  Serial.begin(115200);

  // シリアルポートが開くまで待機（ネイティブUSBデバイス用）
  while (!Serial) {
    delay(1);
  }

  // 起動メッセージ
  printStartupMessage();

  // センサーマネージャーの初期化
  if (!sensorManager.begin()) {
    Serial.println(F("\n❌ ERROR: Sensor initialization failed!"));
    Serial.println(F("Please check:"));
    Serial.println(F("  1. I2C connections (SDA/SCL)"));
    Serial.println(F("  2. Power supply (3.3V/5V)"));
    Serial.println(F("  3. Shutdown pin connections"));
    Serial.println(F("  4. Sensor hardware"));

    // エラー時は無限ループで停止
    while (1) {
      delay(1000);
    }
  }

  Serial.println();
  Serial.println(F("✓ Initialization complete!"));
  Serial.println(F("Starting continuous measurement...\n"));

  // CSV形式の場合はヘッダーを出力
  if (OUTPUT_MODE == CSV) {
    Serial.println(F("S1,S2,S3,S4,S5"));
  }

  // 初回測定前に少し待機
  delay(500);
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

    // 全センサーから距離を読み取る
    sensorManager.readAllSensors();

    // 選択した形式で出力
    switch (OUTPUT_MODE) {
      case COMPACT:
        sensorManager.printCompact();
        break;

      case DETAILED:
        sensorManager.printDetailed();
        Serial.println();  // 読みやすさのため空行を追加
        break;

      case CSV:
        sensorManager.printCSV();
        break;

      case JSON:
        sensorManager.printJSON();
        break;
    }
  }

  // シリアルコマンド受信処理（オプション）
  handleSerialCommands();
}

// ============================================================================
// ヘルパー関数
// ============================================================================

/*
 * 起動メッセージを表示
 */
void printStartupMessage() {
  Serial.println(F("\n\n"));
  Serial.println(F("╔═══════════════════════════════════════════════╗"));
  Serial.println(F("║  5-Sensor VL53L0X Reader (OOP Design)         ║"));
  Serial.println(F("║  Version 1.0                                  ║"));
  Serial.println(F("╚═══════════════════════════════════════════════╝"));
  Serial.println();

  Serial.print(F("Output Mode: "));
  switch (OUTPUT_MODE) {
    case COMPACT:  Serial.println(F("COMPACT")); break;
    case DETAILED: Serial.println(F("DETAILED")); break;
    case CSV:      Serial.println(F("CSV")); break;
    case JSON:     Serial.println(F("JSON")); break;
  }

  Serial.print(F("Measurement Rate: "));
  Serial.print(1000 / MEASUREMENT_INTERVAL);
  Serial.println(F(" Hz"));
  Serial.println();
}

/*
 * シリアルコマンド処理（デバッグ用）
 *
 * コマンド:
 * 'c' - COMPACT表示に切り替え
 * 'd' - DETAILED表示に切り替え
 * 'v' - CSV表示に切り替え
 * 'j' - JSON表示に切り替え
 * 'i' - 初期化状態を表示
 * '1'-'5' - 特定のセンサー情報を表示
 */
void handleSerialCommands() {
  if (Serial.available() > 0) {
    char command = Serial.read();

    switch (command) {
      case 'c':
      case 'C':
        Serial.println(F("\n[Switched to COMPACT mode]"));
        // 実際の切り替えは定数なので、再コンパイルが必要
        break;

      case 'd':
      case 'D':
        Serial.println(F("\n[DETAILED mode]"));
        sensorManager.printDetailed();
        break;

      case 'v':
      case 'V':
        Serial.println(F("\n[CSV mode]"));
        Serial.println(F("S1,S2,S3,S4,S5"));
        break;

      case 'j':
      case 'J':
        Serial.println(F("\n[JSON mode]"));
        sensorManager.printJSON();
        break;

      case 'i':
      case 'I':
        Serial.println();
        sensorManager.printInitializationStatus();
        break;

      case '1':
      case '2':
      case '3':
      case '4':
      case '5':
        Serial.println();
        sensorManager.printSensorInfo(command - '1');
        break;

      case 'h':
      case 'H':
      case '?':
        printHelp();
        break;

      default:
        // 未知のコマンドは無視
        break;
    }
  }
}

/*
 * ヘルプメッセージを表示
 */
void printHelp() {
  Serial.println(F("\n=== Available Commands ==="));
  Serial.println(F("c - Switch to COMPACT mode (requires recompile)"));
  Serial.println(F("d - Show DETAILED output"));
  Serial.println(F("v - Show CSV output"));
  Serial.println(F("j - Show JSON output"));
  Serial.println(F("i - Show initialization status"));
  Serial.println(F("1-5 - Show specific sensor info"));
  Serial.println(F("h/? - Show this help"));
  Serial.println(F("=========================\n"));
}
