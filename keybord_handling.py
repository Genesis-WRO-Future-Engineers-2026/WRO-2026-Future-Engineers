import RPi.GPIO as GPIO
import sys
import tty
import termios
import time

# GPIOの設定
esc_pin = 12  # GPIO 12
GPIO.setmode(GPIO.BCM)  # GPIOをBCMモードで使用
GPIO.setwarnings(False)  # GPIO警告無効化
GPIO.setup(esc_pin, GPIO.OUT)  # ESCピンを出力モードに設定

# PWM設定（50Hz）
pwm = GPIO.PWM(esc_pin, 50)
pwm.start(0)  # デューティサイクル0%で開始

def set_esc_speed(pulse_width_ms):
    """
    パルス幅をミリ秒からデューティサイクルに変換してESCに設定
    50Hzの場合、1周期は20ms
    デューティサイクル(%) = (パルス幅ms / 20ms) * 100
    """
    duty_cycle = (pulse_width_ms / 20.0) * 100
    pwm.ChangeDutyCycle(duty_cycle)

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
    print("矢印キーでESCを制御します")
    print("↑: 前進加速")
    print("↓: 後退加速")
    print("スペース: 停止（ニュートラル）")
    print("q: 終了")
    print("-" * 40)
    
    current_pulse = 1.5  # ニュートラル位置（1.5ms）
    set_esc_speed(current_pulse)
    time.sleep(0.1)  # 初期化待機
    
    while True:
        key = get_key()
        
        if key == 'q':
            print("\nプログラムを終了します...")
            break
        elif key == '[A':  # 上矢印
            current_pulse = min(1.6, current_pulse + 0.05)  # 最大1.6ms
            set_esc_speed(current_pulse)
            print(f"\r前進: パルス幅 {current_pulse:.2f} ms", end='', flush=True)
        elif key == '[B':  # 下矢印
            current_pulse = max(1.4, current_pulse - 0.05)  # 最小1.4ms
            set_esc_speed(current_pulse)
            print(f"\r後退: パルス幅 {current_pulse:.2f} ms", end='', flush=True)
        elif key == ' ':  # スペースキー
            current_pulse = 1.5  # ニュートラルに戻す
            set_esc_speed(current_pulse)
            print(f"\r停止: パルス幅 {current_pulse:.2f} ms", end='', flush=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nプログラムを終了します...")
    finally:
        # 終了時にニュートラルに戻してクリーンアップ
        set_esc_speed(1.5)
        time.sleep(0.5)
        pwm.stop()
        GPIO.cleanup()
        sys.exit()