/*
 * pwm_test.ino
 *
 * サーボモーターのパルス幅と実際の駆動の対応関係をテストする
 *
 * 使い方:
 *   1. シリアルモニターを開く（115200bps）
 *   2. パルス幅（500-2500）を入力してEnterを押す
 *   3. サーボが指定したパルス幅で動作する
 *
 * コマンド:
 *   数値（500-2500）: 指定パルス幅に移動
 *   s: スイープテスト（MIN→MAX→MIN）
 *   c: センター位置（1500us）に移動
 *   +: 現在値を+10us
 *   -: 現在値を-10us
 *   h: ヘルプ表示
 */

#include <Servo.h>

// ピン設定
const uint8_t SERVO_PIN = 9;

// パルス幅設定
const uint16_t PULSE_MIN = 500;
const uint16_t PULSE_MAX = 2500;
const uint16_t PULSE_CENTER = 1500;
const uint16_t PULSE_STEP = 10;

// スイープテスト設定
const uint16_t SWEEP_DELAY_MS = 20;  // スイープ時の各ステップ間の遅延

Servo servo;
uint16_t currentPulse = PULSE_CENTER;
String inputBuffer = "";

void setup() {
    Serial.begin(115200);
    while (!Serial) { delay(10); }

    printHeader();

    // サーボ初期化
    servo.attach(SERVO_PIN, PULSE_MIN, PULSE_MAX);
    servo.writeMicroseconds(PULSE_CENTER);
    currentPulse = PULSE_CENTER;

    Serial.println("[OK] サーボ初期化完了");
    Serial.print("[OK] 初期位置: ");
    Serial.print(PULSE_CENTER);
    Serial.println(" us (センター)");
    Serial.println();
    printHelp();
    printPrompt();
}

void loop() {
    // シリアル入力処理
    while (Serial.available() > 0) {
        char c = Serial.read();

        if (c == '\n' || c == '\r') {
            if (inputBuffer.length() > 0) {
                processCommand(inputBuffer);
                inputBuffer = "";
                printPrompt();
            }
        } else {
            inputBuffer += c;
            Serial.print(c);  // エコーバック
        }
    }
}

void processCommand(String cmd) {
    Serial.println();  // 改行

    cmd.trim();
    if (cmd.length() == 0) return;

    // 単一文字コマンド
    if (cmd.length() == 1) {
        char c = cmd.charAt(0);
        switch (c) {
            case 's':
            case 'S':
                runSweepTest();
                return;
            case 'c':
            case 'C':
                setAndShowPulse(PULSE_CENTER);
                return;
            case '+':
                setAndShowPulse(currentPulse + PULSE_STEP);
                return;
            case '-':
                setAndShowPulse(currentPulse - PULSE_STEP);
                return;
            case 'h':
            case 'H':
            case '?':
                printHelp();
                return;
        }
    }

    // 数値入力
    int pulse = cmd.toInt();
    if (pulse > 0) {
        setAndShowPulse(pulse);
    } else {
        Serial.println("[ERR] 不正なコマンド。'h'でヘルプ表示");
    }
}

void setAndShowPulse(int pulse) {
    // 範囲チェック
    if (pulse < PULSE_MIN) {
        Serial.print("[WARN] 下限に制限: ");
        Serial.print(PULSE_MIN);
        Serial.println(" us");
        pulse = PULSE_MIN;
    }
    if (pulse > PULSE_MAX) {
        Serial.print("[WARN] 上限に制限: ");
        Serial.print(PULSE_MAX);
        Serial.println(" us");
        pulse = PULSE_MAX;
    }

    currentPulse = pulse;
    servo.writeMicroseconds(currentPulse);

    // 結果表示
    Serial.print("[SET] パルス幅: ");
    Serial.print(currentPulse);
    Serial.print(" us");

    // 推定角度（線形補間）
    // 一般的なサーボ: 500us = -90度, 1500us = 0度, 2500us = +90度
    float angle = map(currentPulse, PULSE_MIN, PULSE_MAX, -90, 90);
    Serial.print(" (推定角度: ");
    Serial.print(angle, 1);
    Serial.println(" deg)");
}

void runSweepTest() {
    Serial.println("[TEST] スイープテスト開始...");
    Serial.println("       MIN → MAX → MIN");

    // MIN → MAX
    Serial.print("       MIN(");
    Serial.print(PULSE_MIN);
    Serial.print(") → MAX(");
    Serial.print(PULSE_MAX);
    Serial.println(")");

    for (int p = PULSE_MIN; p <= PULSE_MAX; p += PULSE_STEP) {
        servo.writeMicroseconds(p);
        delay(SWEEP_DELAY_MS);
    }

    delay(500);  // 端点で少し待つ

    // MAX → MIN
    Serial.print("       MAX(");
    Serial.print(PULSE_MAX);
    Serial.print(") → MIN(");
    Serial.print(PULSE_MIN);
    Serial.println(")");

    for (int p = PULSE_MAX; p >= PULSE_MIN; p -= PULSE_STEP) {
        servo.writeMicroseconds(p);
        delay(SWEEP_DELAY_MS);
    }

    // センターに戻す
    servo.writeMicroseconds(PULSE_CENTER);
    currentPulse = PULSE_CENTER;

    Serial.println("[TEST] スイープテスト完了");
    Serial.print("       センター(");
    Serial.print(PULSE_CENTER);
    Serial.println(" us)に復帰");
}

void printHeader() {
    Serial.println();
    Serial.println("========================================");
    Serial.println("  サーボ パルス幅テスト");
    Serial.println("========================================");
    Serial.print("サーボピン: ");
    Serial.println(SERVO_PIN);
    Serial.print("パルス範囲: ");
    Serial.print(PULSE_MIN);
    Serial.print(" - ");
    Serial.print(PULSE_MAX);
    Serial.println(" us");
    Serial.println();
}

void printHelp() {
    Serial.println("--- コマンド ---");
    Serial.println("  数値    : 指定パルス幅(us)に移動");
    Serial.println("  s       : スイープテスト");
    Serial.println("  c       : センター(1500us)に移動");
    Serial.println("  +       : +10us");
    Serial.println("  -       : -10us");
    Serial.println("  h       : ヘルプ表示");
    Serial.println();
}

void printPrompt() {
    Serial.print("現在: ");
    Serial.print(currentPulse);
    Serial.print("us > ");
}
