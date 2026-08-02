# actuator.py
from machine import Pin, PWM

import Config

def _map_value(x, in_min, in_max, out_min, out_max):
    """Función helper para replicar el map() de Arduino"""
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

class Actuator:
    def __init__(self):
        self._current_speed = 0
        self._servo = None
        self._motor_pwm = None
        self._motor_in1 = None
        self._motor_in2 = None

    def begin(self):
        if Config.ENABLE_PWM:
            # 1. Inicialización del Servo (50Hz para servos estándar)
            self._servo = PWM(Pin(Config.SERVO_PIN), freq=50)
            
            # Colocamos el servo en su posición central de arranque
            # 0° a 180° mapea a pulsos de 1000us a 2000us
            pulse_center_us = _map_value(Config.SERVO_CENTER_DEG, 0, 180, 1000, 2000)
            
            # En MicroPython, duty_ns acepta nanosegundos (1000us = 1,000,000ns)
            self._servo.duty_ns(int(pulse_center_us * 1000))

            # 2. Inicialización del Puente H del Motor (TB6612FNG)
            self._motor_in1 = Pin(Config.MOTOR_IN1_PIN, Pin.OUT)
            self._motor_in2 = Pin(Config.MOTOR_IN2_PIN, Pin.OUT)
            
            # PWM a 20kHz tal como en Arduino para evitar ruidos audibles en el motor
            self._motor_pwm = PWM(Pin(Config.MOTOR_PWMA_PIN), freq=20000)

            # Estado inicial seguro: Detenido
            self.stop()

            print("Actuadores Inicializados con Calibración en Grados:")
            print(f"  Servo Pin: {Config.SERVO_PIN} | Centro: {Config.SERVO_CENTER_DEG}°")
            print(f"  Motor Pines: IN1={Config.MOTOR_IN1_PIN}, IN2={Config.MOTOR_IN2_PIN}, PWM={Config.MOTOR_PWMA_PIN}")
        else:
            print("DEBUG MODE: Actuadores desactivados (Sin salidas físicas PWM)")

    def set_steering(self, float_angle_degrees):
        # 1. Traducir el ángulo teórico (Pure Pursuit) a grados físicos del servo
        target_servo_deg = _map_value(
            float_angle_degrees,
            -Config.MAX_STEERING_ANGLE,
            Config.MAX_STEERING_ANGLE,
            Config.SERVO_LEFT_MAX_DEG,
            Config.SERVO_RIGHT_MAX_DEG
        )

        # 2. Filtro de seguridad (Clamp) basado en tus límites máximos físicos
        min_allowed = min(Config.SERVO_RIGHT_MAX_DEG, Config.SERVO_LEFT_MAX_DEG)
        max_allowed = max(Config.SERVO_RIGHT_MAX_DEG, Config.SERVO_LEFT_MAX_DEG)
        
        final_deg = max(min_allowed, min(max_allowed, target_servo_deg))

        if Config.ENABLE_PWM and self._servo is not None:
            # 3. Convertir grados a microsegundos (0-180deg -> 1000-2000us) y pasarlo a ns
            pulse_us = _map_value(final_deg, 0, 180, 1000, 2000)
            self._servo.duty_ns(int(pulse_us * 1000))

        print(f"Servo Grados Reales {int(final_deg)}")

    def set_speed(self, speed_pwm):
        self._current_speed = speed_pwm
        
        if not Config.ENABLE_PWM or self._motor_pwm is None:
            return

        if self._current_speed == 0:
            self.stop()
            return

        # Marcha adelante según el puente H
        self._motor_in1.value(1)
        self._motor_in2.value(0)
        
        # MicroPython maneja duty de 10 bits por defecto (0-1023). 
        # Para mantener tu rango original de 8 bits (0-255), escalamos multiplicando por 4.
        duty_10bit = min(1023, max(0, self._current_speed * 4))
        self._motor_pwm.duty(duty_10bit)

    def stop(self):
        self._current_speed = 0
        if Config.ENABLE_PWM and self._motor_pwm is not None:
            # Modo standby / Freno corto del TB6612FNG
            self._motor_in1.value(0)
            self._motor_in2.value(0)
            self._motor_pwm.duty(0)
            
    def set_angle_dg(self, angle):
        if Config.ENABLE_PWM and self._servo is not None:
            # 3. Convertir grados a microsegundos (0-180deg -> 1000-2000us) y pasarlo a ns
            pulse_us = _map_value(angle, 0, 180, 1000, 2000)
            self._servo.duty_ns(int(pulse_us * 1000))
        
