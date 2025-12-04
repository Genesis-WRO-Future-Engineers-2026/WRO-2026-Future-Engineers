import RPi.GPIO as GPIO
import sys
import tty
import termios
import time

# GPIOの設定
servo_pin = 12  # サーボ用GPIO 12
esc_pin = 13    # ESC用GPIO 13

GPIO.setmode(GPIO.BCM)      # GPIOをBCMモードで使用
GPIO.setwarnings(False)     # GPIO警告無効化
GPIO.setup(servo_pin, GPIO.OUT)  # サーボピンを出力モードに設定
GPIO.setup(esc_pin, GPIO.OUT)    # ESCピンを出力モードに設定

# PWM設定（50Hz）
servo_pwm = None
esc_pwm = None

try:
    servo_pwm = GPIO.PWM(servo_pin, 50)  # サーボ用PWM 50Hz
    esc_pwm = GPIO.PWM(esc_pin, 50)      # ESC用PWM 50Hz
    servo_pwm.start(0)  # デューティサイクル0%で開始
    esc_pwm.start(0)    # デューティサイクル0%で開始
except Exception as e:
    print(f"GPIOの初期化中にエラーが発生しました: {e}")
    GPIO.cleanup()
    sys.exit(1)

def set_servo_angle(angle):
    """
    サーボの角度を設定します。角度は-90度から90度の範囲です。
    """
    # 角度をパルス幅に変換（0.5ms～2.4ms）
    min_pulse_width_ms = 0.5
    max_pulse_width_ms = 2.4
    
    # 角度からパルス幅を計算
    pulse_width_ms = ((angle + 90) / 180) * (max_pulse_width_ms - min_pulse_width_ms) + min_pulse_width_ms
    
    # パルス幅をデューティサイクルに変換（50Hzの場合、1周期は20ms）
    duty_cycle = (pulse_width_ms / 20.0) * 100
    servo_pwm.ChangeDutyCycle(duty_cycle)

def set_esc_speed(pulse_width_ms):
    """
    ESCの速度を設定します。パルス幅はミリ秒単位で指定します。
    """
    # パルス幅をデューティサイクルに変換（50Hzの場合、1周期は20ms）
    duty_cycle = (pulse_width_ms / 20.0) * 100
    esc_pwm.ChangeDutyCycle(duty_cycle)

def initialize_devices():
    """
    サーボとESCを安全な初期状態に設定します。
    """
    set_servo_angle(0)       # サーボを中央に設定
    set_esc_speed(1.5)       # ESCを停止状態に設定
    time.sleep(1)            # 安定するまで待機

def shutdown_devices():
    """
    サーボとESCを安全な停止状態に設定します。
    """
    set_servo_angle(0)       # サーボを中央に設定
    set_esc_speed(1.5)       # ESCを停止状態に設定
    time.sleep(1)            # 安定するまで待機
    servo_pwm.stop()
    esc_pwm.stop()
    GPIO.cleanup()

def get_key():
    """ターミナルからキー入力を即座に取得"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        # エスケープシーケンスの処理（矢印キー）
        if ch == '\x1b':
            ch = sys.stdin.read(2)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def main():
    print("キーボードでサーボとESCを制御します")
    print("←→: サーボ左右回転")
    print("↑↓: モーター前進/後退")
    print("スペース: 停止（中央/ニュートラル）")
    print("q: 終了")
    print("-" * 50)

    # デバイスの初期化
    initialize_devices()

    # 現在の状態
    current_angle = 0.0      # サーボの角度
    current_pulse = 1.5      # ESCのパルス幅

    try:
        while True:
            key = get_key()

            if key == 'q':
                print("\nプログラムを終了します...")
                break

            elif key == '[C':  # 右矢印
                current_angle = min(90, current_angle + 10)  # 最大90度
                set_servo_angle(current_angle)
                print(f"\rサーボ: {current_angle:+.0f}° | モーター: {current_pulse:.2f}ms", end='', flush=True)

            elif key == '[D':  # 左矢印
                current_angle = max(-90, current_angle - 10)  # 最小-90度
                set_servo_angle(current_angle)
                print(f"\rサーボ: {current_angle:+.0f}° | モーター: {current_pulse:.2f}ms", end='', flush=True)

            elif key == '[A':  # 上矢印
                current_pulse = min(1.6, current_pulse + 0.05)  # 最大1.6ms
                set_esc_speed(current_pulse)
                print(f"\rサーボ: {current_angle:+.0f}° | モーター: {current_pulse:.2f}ms", end='', flush=True)

            elif key == '[B':  # 下矢印
                current_pulse = max(1.4, current_pulse - 0.05)  # 最小1.4ms
                set_esc_speed(current_pulse)
                print(f"\rサーボ: {current_angle:+.0f}° | モーター: {current_pulse:.2f}ms", end='', flush=True)

            elif key == ' ':  # スペースキー
                current_angle = 0
                current_pulse = 1.5
                set_servo_angle(current_angle)
                set_esc_speed(current_pulse)
                print(f"\rサーボ: {current_angle:+.0f}° | モーター: {current_pulse:.2f}ms (停止)", end='', flush=True)

    except KeyboardInterrupt:
        print("\nプログラムを終了します...")

    except Exception as e:
        print(f"\nエラーが発生しました: {e}")

    finally:
        # デバイスを安全な状態にシャットダウン
        shutdown_devices()
        print("\nデバイスを安全な状態に設定しました。")

if __name__ == "__main__":
    main()