/*
 * PWMパルス生成プログラム（Raspberry Pi連携用）
 *
 * 【概要】
 * Raspberry Piからシリアル通信でパルス幅を受信し、
 * サーボとESC用のPWMパルスを生成します。
 *
 * 【通信プロトコル】
 * - サーボ制御: "S<パルス幅μs>\n"  例: "S1500\n" → 1500マイクロ秒
 * - ESC制御:   "E<パルス幅μs>\n"  例: "E1500\n" → 1500マイクロ秒
 *
 * 【動作】
 * - Raspberry Piから新しい値が来るまで、同じパルス幅を出力し続けます
 * - 一定時間通信が途切れた場合、安全のため停止状態になります
 *
 * 【接続】
 * - サーボ信号線: Arduinoのピン9
 * - ESC信号線:   Arduinoのピン10
 * - シリアル通信: Arduino NanoのTX/RX ⇔ Raspberry PiのGPIO14/15
 */

#include <Servo.h>

// ============================================================================
// ピン定義
// ============================================================================
const int SERVO_PIN = 9;   // サーボモーター用ピン
const int ESC_PIN = 10;    // ESC（モータースピードコントローラー）用ピン

// ============================================================================
// パルス幅の範囲設定
// ============================================================================
// サーボの一般的な範囲: 500～2400マイクロ秒
const int SERVO_MIN_PULSE = 500;
const int SERVO_MAX_PULSE = 2400;

// ESCの一般的な範囲: 1000～2000マイクロ秒
const int ESC_MIN_PULSE = 1000;
const int ESC_MAX_PULSE = 2000;

// ============================================================================
// 初期値・停止値
// ============================================================================
const int SERVO_NEUTRAL_PULSE = 1500;  // サーボのニュートラル位置（中央）
const int ESC_STOP_PULSE = 1500;       // ESCの停止パルス

// ============================================================================
// 通信タイムアウト設定
// ============================================================================
const unsigned long COMM_TIMEOUT_MS = 1000;  // 1秒間通信がない場合はタイムアウト

// ============================================================================
// グローバル変数
// ============================================================================
Servo servo;  // サーボ制御オブジェクト
Servo esc;    // ESC制御オブジェクト

// 現在のパルス幅（マイクロ秒）
int current_servo_pulse = SERVO_NEUTRAL_PULSE;
int current_esc_pulse = ESC_STOP_PULSE;

// 最後に通信があった時刻
unsigned long last_comm_time = 0;

// タイムアウト状態フラグ
bool is_timeout = false;

// ============================================================================
// 初期化処理
// ============================================================================
void setup() {
  // シリアル通信を115200bpsで開始
  Serial.begin(115200);

  // サーボとESCをピンに接続
  servo.attach(SERVO_PIN, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
  esc.attach(ESC_PIN, ESC_MIN_PULSE, ESC_MAX_PULSE);

  // 初期状態: ニュートラル・停止に設定
  servo.writeMicroseconds(current_servo_pulse);
  esc.writeMicroseconds(current_esc_pulse);

  // 初期化完了メッセージ
  Serial.println("Arduino Pulse Generator Ready");
  Serial.println("Waiting for commands from Raspberry Pi...");

  // 通信タイマー開始
  last_comm_time = millis();
}

// ============================================================================
// メインループ処理
// ============================================================================
void loop() {
  // シリアル通信でデータが受信されているかチェック
  if (Serial.available() > 0) {
    // 改行までの文字列を読み取る
    String command = Serial.readStringUntil('\n');
    command.trim();

    // コマンドを処理
    if (command.length() > 0) {
      processCommand(command);
      // 通信タイマーをリセット
      last_comm_time = millis();
      // タイムアウト状態を解除
      if (is_timeout) {
        is_timeout = false;
        Serial.println("Communication restored");
      }
    }
  }

  // 通信タイムアウトチェック
  if (!is_timeout && (millis() - last_comm_time > COMM_TIMEOUT_MS)) {
    // タイムアウト発生 → 安全のため停止状態に
    is_timeout = true;
    current_servo_pulse = SERVO_NEUTRAL_PULSE;
    current_esc_pulse = ESC_STOP_PULSE;
    servo.writeMicroseconds(current_servo_pulse);
    esc.writeMicroseconds(current_esc_pulse);
    Serial.println("Communication timeout - Emergency stop");
  }

  // 現在のパルス幅を維持（Servoライブラリが自動的に継続出力）
  // ※特に処理不要、Servoライブラリが50Hzで自動的にパルスを出力し続けます
}

// ============================================================================
// コマンド処理関数
// ============================================================================
void processCommand(String command) {
  if (command.length() < 2) {
    Serial.println("Error: Invalid command format");
    return;
  }

  // コマンドの種類を判定（'S'=サーボ, 'E'=ESC）
  char command_type = command.charAt(0);

  // コマンドの2文字目以降を数値として取得
  int pulse_width = command.substring(1).toInt();

  // サーボコマンド処理
  if (command_type == 'S' || command_type == 's') {
    // パルス幅を範囲内に制限
    pulse_width = constrain(pulse_width, SERVO_MIN_PULSE, SERVO_MAX_PULSE);

    // パルス幅を更新
    current_servo_pulse = pulse_width;
    servo.writeMicroseconds(current_servo_pulse);

    // デバッグ出力
    Serial.print("Servo: ");
    Serial.print(current_servo_pulse);
    Serial.println(" us");
  }
  // ESCコマンド処理
  else if (command_type == 'E' || command_type == 'e') {
    // パルス幅を範囲内に制限
    pulse_width = constrain(pulse_width, ESC_MIN_PULSE, ESC_MAX_PULSE);

    // パルス幅を更新
    current_esc_pulse = pulse_width;
    esc.writeMicroseconds(current_esc_pulse);

    // デバッグ出力
    Serial.print("ESC: ");
    Serial.print(current_esc_pulse);
    Serial.println(" us");
  }
  // 不明なコマンド
  else {
    Serial.print("Error: Unknown command type '");
    Serial.print(command_type);
    Serial.println("'");
  }
}
