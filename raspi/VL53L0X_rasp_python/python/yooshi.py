#!/usr/bin/python

# MIT License
# 
# Copyright (c) 2017 John Bryan Moore
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time
import VL53L0X
import RPi.GPIO as GPIO

# GPIO for Sensor 1 shutdown pin
SENSOR1_SHUTDOWN = 20
# GPIO for Sensor 2 shutdown pin
SENSOR2_SHUTDOWN = 16


def initialize_gpio():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SENSOR1_SHUTDOWN, GPIO.OUT)
    GPIO.setup(SENSOR2_SHUTDOWN, GPIO.OUT)


def initialize_sensors():
    GPIO.output(SENSOR1_SHUTDOWN, GPIO.LOW)
    GPIO.output(SENSOR2_SHUTDOWN, GPIO.LOW)
    time.sleep(0.50)

    tof = VL53L0X.VL53L0X(address=0x2B)
    tof1 = VL53L0X.VL53L0X(address=0x2D)

    GPIO.output(SENSOR1_SHUTDOWN, GPIO.HIGH)
    time.sleep(0.50)
    tof.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)

    GPIO.output(SENSOR2_SHUTDOWN, GPIO.HIGH)
    time.sleep(0.50)
    tof1.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)

    return tof, tof1


def get_timing(tof):
    timing = tof.get_timing()
    if timing < 20000:
        timing = 20000
    print("Timing %d ms" % (timing/1000))
    return timing


def read_distance(tof, sensor_name):
    distance = tof.get_distance()
    if distance > 0:
        print("sensor %d - %d mm, %d cm" % (tof.my_object_number, distance, distance/10))
        return distance
    else:
        print("%d - Error" % tof.my_object_number)
        return None


def run_measurement_loop(tof, tof1, timing, iterations=100):
    for count in range(1, iterations + 1):
        distance = tof.get_distance()
        if distance > 0:
            print("sensor %d - %d mm, %d cm, iteration %d" % (tof.my_object_number, distance, distance/10, count))
        else:
            print("%d - Error" % tof.my_object_number)

        distance = tof1.get_distance()
        if distance > 0:
            print("sensor %d - %d mm, %d cm, iteration %d" % (tof1.my_object_number, distance, distance/10, count))
        else:
            print("%d - Error" % tof.my_object_number)

        time.sleep(timing/1000000.00)


def cleanup_sensors(tof, tof1):
    tof1.stop_ranging()
    GPIO.output(SENSOR2_SHUTDOWN, GPIO.LOW)
    tof.stop_ranging()
    GPIO.output(SENSOR1_SHUTDOWN, GPIO.LOW)


def main():
    initialize_gpio()
    tof, tof1 = initialize_sensors()
    timing = get_timing(tof)
    run_measurement_loop(tof, tof1, timing)
    cleanup_sensors(tof, tof1)


if __name__ == "__main__":
    main()

