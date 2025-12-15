#!/usr/bin/env python3
"""
シリアル通信版アクチュエーターのテストプログラム

【動作】
サーボとESCに様々なパルス幅を送信して、
Arduinoとの通信が正しく動作するか確認します。

【使い方】
1. ArduinoにPWM生成プログラム(pulse_generator.ino)を書き込む
2. RaspberryPiとArduinoをシリアル接続(GPIO14/15 ⇔ TX/RX)
3. このスクリプトを実行: python3 test_serial_actuator.py
"""

import time
from serial_comm import ArduinoSerial


def test_servo(arduino: ArduinoSerial):
    """
    サーボのテスト

    -90度 → 0度 → +90度 → 0度の順にステアリングを動かします
    """
    print("\n" + "=" * 60)
    print("サーボテスト開始")
    print("=" * 60)

    # 角度とパルス幅の対応（-90°～+90°）
    # -90° → 500μs, 0° → 1500μs, +90° → 2400μs
    test_angles = [
        (-90, 500),
        (-45, 975),
        (0, 1500),
        (45, 2025),
        (90, 2400),
        (0, 1500)  # 最後は中央に戻す
    ]

    for angle, pulse_us in test_angles:
        print(f"\nステアリング角度: {angle:+4d}° → パルス幅: {pulse_us} μs")
        # 2秒間、100ms間隔で継続的にパルスを送信（Arduinoのタイムアウト対策）
        for _ in range(20):
            arduino.send_servo_pulse(pulse_us)
            time.sleep(0.1)

    print("\nサーボテスト完了")


def test_esc(arduino: ArduinoSerial):
    """
    ESCのテスト

    停止 → 低速 → 中速 → 高速 → 停止の順にモーターを動かします
    """
    print("\n" + "=" * 60)
    print("ESCテスト開始")
    print("=" * 60)

    # 速度とパルス幅の対応
    # 前進: 1500 → 1400（最大速）、後退: 1500 → 1600（バック）
    test_speeds = [
        ("停止", 1500),
        ("低速前進", 1450),
        ("中速前進", 1425),
        ("高速前進（最大速）", 1400),
        ("停止", 1500),
        ("低速後退", 1550),
        ("中速後退", 1575),
        ("後退（バック）", 1600),
        ("停止", 1500)  # 最後は停止
    ]

    for speed_name, pulse_us in test_speeds:
        print(f"\nモーター速度: {speed_name} → パルス幅: {pulse_us} μs")
        # 2秒間、100ms間隔で継続的にパルスを送信（Arduinoのタイムアウト対策）
        for _ in range(20):
            arduino.send_esc_pulse(pulse_us)
            time.sleep(0.1)

    print("\nESCテスト完了")


def test_combined(arduino: ArduinoSerial):
    """
    サーボとESCの同時制御テスト

    ステアリングとモーターを同時に動かします
    """
    print("\n" + "=" * 60)
    print("サーボ＋ESC同時制御テスト開始")
    print("=" * 60)

    # (ステアリング角度, サーボパルス, 速度名, ESCパルス)
    test_commands = [
        ("左旋回 + 前進", -45, 975, 1425),
        ("直進 + 前進", 0, 1500, 1425),
        ("右旋回 + 前進", 45, 2025, 1425),
        ("直進 + 停止", 0, 1500, 1500)
    ]

    for description, angle, servo_pulse, esc_pulse in test_commands:
        print(f"\n{description}")
        print(f"  ステアリング: {angle:+4d}° ({servo_pulse} μs)")
        print(f"  モーター: {esc_pulse} μs")

        # 2秒間、100ms間隔で継続的にパルスを送信（Arduinoのタイムアウト対策）
        for _ in range(20):
            arduino.send_servo_pulse(servo_pulse)
            arduino.send_esc_pulse(esc_pulse)
            time.sleep(0.1)

    print("\n同時制御テスト完了")


def main():
    """メインテストプログラム"""
    print("=" * 60)
    print("シリアル通信版アクチュエーター テストプログラム")
    print("=" * 60)

    # シリアルポートの選択
    print("\nシリアルポートを指定してください")
    print("  1: /dev/serial0 (GPIO14/15)")
    print("  2: /dev/ttyUSB0 (USB-シリアル変換)")
    print("  3: /dev/ttyACM0 (Arduino USB)")

    choice = input("\n選択 (デフォルト: 1): ").strip()

    if choice == "2":
        serial_port = "/dev/ttyUSB0"
    elif choice == "3":
        serial_port = "/dev/ttyACM0"
    else:
        serial_port = "/dev/serial0"

    print(f"\n選択されたポート: {serial_port}")

    # Arduino接続
    arduino = ArduinoSerial(port=serial_port)

    if arduino.serial_connection is None:
        print("\nエラー: Arduinoに接続できませんでした")
        print("以下を確認してください:")
        print("  1. Arduinoが正しく接続されているか")
        print("  2. シリアルポートのパーミッション（sudo usermod -a -G dialout $USER）")
        print("  3. Arduinoにpulse_generator.inoが書き込まれているか")
        return

    try:
        # テストメニュー
        while True:
            print("\n" + "=" * 60)
            print("テストメニュー")
            print("=" * 60)
            print("  1: サーボテスト")
            print("  2: ESCテスト")
            print("  3: サーボ＋ESC同時制御テスト")
            print("  4: すべてのテストを実行")
            print("  0: 終了")

            choice = input("\n選択: ").strip()

            if choice == "1":
                test_servo(arduino)
            elif choice == "2":
                test_esc(arduino)
            elif choice == "3":
                test_combined(arduino)
            elif choice == "4":
                test_servo(arduino)
                test_esc(arduino)
                test_combined(arduino)
            elif choice == "0":
                break
            else:
                print("無効な選択です")

    except KeyboardInterrupt:
        print("\n\nプログラムが中断されました")
    finally:
        # 安全のため停止状態に
        print("\n停止処理中...")
        arduino.send_servo_pulse(1500)  # ニュートラル
        arduino.send_esc_pulse(1500)    # 停止
        time.sleep(0.5)
        arduino.close()
        print("テスト終了")


if __name__ == "__main__":
    main()
