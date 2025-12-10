/*
 * ESC（Electric Speed Controller）制御プログラム
 *
 * 【機能】
 * シリアル通信で受信したパーセント値（0～100%）をPWMパルス幅に変換して
 * ESCに送信し、モーターの速度を制御します。
 *
 * 【使用方法】
 * シリアルモニタから "P<数値>" の形式でコマンドを送信
 * 例: "P0"   → 停止（1000us）
 *     "P50"  → 50%速度（1500us）
 *     "P100" → 最高速度（2000us）
 *
 * 【接続】
 * ESC信号線: Arduinoのピン9
 */

// ESC制御用のServoライブラリをインクルード
#include <Servo.h>

// ESC制御用のServoオブジェクト
Servo esc;

// ESCが接続されているピン番号
const int ESC_PIN = 9;

// ESCのパルス幅の最小値（マイクロ秒）- 停止/最低速度
const int MIN_PULSE = 1000;

// ESCのパルス幅の最大値（マイクロ秒）- 最高速度
const int MAX_PULSE = 2000;

// 初期化処理
void setup() {
  // シリアル通信を115200bpsで開始
  Serial.begin(115200);

  // ESCをピンに接続し、パルス幅の範囲を設定
  esc.attach(ESC_PIN, MIN_PULSE, MAX_PULSE);

  // ESCを最小パルス幅（停止状態）に初期化
  esc.writeMicroseconds(MIN_PULSE);

  // ESCの初期化待機時間（2秒）
  delay(2000);
}

// メインループ処理
void loop() {
  // シリアル通信でデータが受信されているかチェック
  if (Serial.available()) {
    // 改行までの文字列を読み取る
    String command = Serial.readStringUntil('\n');
    command.trim();

    // コマンドが'P'または'p'で始まる場合（例: "P50" = 50%）
    if (command.charAt(0) == 'P' || command.charAt(0) == 'p') {
      // 'P'以降の数値をパーセント値として取得
      float percent = command.substring(1).toFloat();

      // パーセント値を0～100の範囲に制限
      if (percent < 0) percent = 0;
      if (percent > 100) percent = 100;

      // パーセント値をパルス幅（マイクロ秒）に変換
      // 0% → 1000us, 100% → 2000us
      int pulse_us = MIN_PULSE + (int)((MAX_PULSE - MIN_PULSE) * percent / 100.0);

      // 計算したパルス幅をESCに送信
      esc.writeMicroseconds(pulse_us);
    }
  }
}
