import RPi.GPIO as GPIO
import time
import sys

trig_pin = 15                           # GPIO 15
echo_pin = 14                           # GPIO 14
speed_of_sound = 34370                  # 20℃での音速(cm/s)

GPIO.setmode(GPIO.BCM)                  # GPIOをBCMモードで使用
GPIO.setwarnings(False)                 # BPIO警告無効化
GPIO.setup(trig_pin, GPIO.OUT)          # Trigピン出力モード設定
GPIO.setup(echo_pin, GPIO.IN)           # Echoピン入力モード設定

def get_distance(): 
    #Trigピンを10μsだけHIGHにして超音波の発信開始
    GPIO.output(trig_pin, GPIO.HIGH)
    time.sleep(0.000010)
    GPIO.output(trig_pin, GPIO.LOW)

    while not GPIO.input(echo_pin):
        pass
    t1 = time.time() # 超音波発信時刻（EchoピンがHIGHになった時刻）格納

    while GPIO.input(echo_pin):
        pass
    t2 = time.time() # 超音波受信時刻（EchoピンがLOWになった時刻）格納

    return (t2 - t1) * speed_of_sound / 2 # 時間差から対象物までの距離計算


while True: # 繰り返し処理
    try:
        distance = '{:.1f}'.format(get_distance())  # 小数点1までまるめ
        print("Distance: " + distance + "cm")       # 表示
        time.sleep(1)                               # 1秒まつ

    except KeyboardInterrupt:                       # Ctrl + C押されたたら
        GPIO.cleanup()                              # GPIOお片付け
        sys.exit()                                  # プログラム終了