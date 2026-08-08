# main.py
import time
from machine import Pin, PWM
from SensorReader import SensorReader
from Mpu6050 import Mpu6050
from Navegacion import NavegadorPista  # Importamos NavegadorPista
import Config

# -------------------------------------------------------------
# 1. HARDWARE Y CLASES ADAPTADORAS
# -------------------------------------------------------------
pin_pwm_motor = PWM(Pin(14), freq=1000)
pin_dir_1 = Pin(12, Pin.OUT)
pin_dir_2 = Pin(13, Pin.OUT)
pin_servo = PWM(Pin(15), freq=50)

class Actuadores:
    """Clase para que NavegadorPista pueda controlar motores y servo"""
    def set_speed(self, velocidad):
        if velocidad == 0:
            pin_pwm_motor.duty_u16(0)
            pin_dir_1.value(0)
            pin_dir_2.value(0)
            return

        if velocidad > 0:
            pin_dir_1.value(1)
            pin_dir_2.value(0)
        else:
            pin_dir_1.value(0)
            pin_dir_2.value(1)

        duty = int((abs(velocidad) / 100) * 65535)
        pin_pwm_motor.duty_u16(duty)

    def set_steering(self, angulo_correccion):
        ANGULO_CENTRO = 60
        ANGULO_MIN = 0
        ANGULO_MAX = 120

        angulo_final = ANGULO_CENTRO + angulo_correccion

        if angulo_final < ANGULO_MIN:
            angulo_final = ANGULO_MIN
        elif angulo_final > ANGULO_MAX:
            angulo_final = ANGULO_MAX

        duty_min = 2500  # Duty cycle 0°
        duty_max = 8192  # Duty cycle 180°
        duty = int(duty_min + (angulo_final / 180.0) * (duty_max - duty_min))
        pin_servo.duty_u16(duty)

    def stop(self):
        self.set_speed(0)
        self.set_steering(0)

class Carro:
    """Contenedor principal requerido por NavegadorPista"""
    def __init__(self, sensores, actuadores):
        self.sensores = sensores
        self.actuadores = actuadores

class Pista:
    """Objeto para gestionar el sentido y estado de la pista"""
    SENTIDO_HORARIO = 1
    SENTIDO_ANTIHORARIO = -1

    def __init__(self):
        self.sentido = None
        self.resuelto = False

    def set_sentido(self, sentido):
        self.sentido = sentido

    def get_sentido(self):
        return self.sentido

    def set_resuelto(self, estado):
        self.resuelto = estado

# -------------------------------------------------------------
# 2. INICIALIZACIÓN DE COMPONENTES
# -------------------------------------------------------------
print("=== INICIALIZANDO VEHÍCULO AUTÓNOMO ===")

sensores = SensorReader()
actuadores = Actuadores()
carro = Carro(sensores, actuadores)
imu = Mpu6050()
pista = Pista()

# Inicializar sensores ToF
if not sensores.begin():
    print("❌ Error crítico: Fallo en sensores ToF. Abortando.")
    raise SystemExit

# Inicializar IMU
try:
    imu.begin()
    print("✓ MPU6050 Calibrado y listo.")
except Exception as e:
    print(f"❌ Error al iniciar IMU: {e}")
    raise SystemExit

# Instanciar el navegador con las referencias requeridas
navegacion = NavegadorPista(carro=carro, mpu=imu)

print("✅ ¡Vehículo Listo! Arrancando en 3 segundos...")
time.sleep(3)

# -------------------------------------------------------------
# 3. BUCLE PRINCIPAL DE CONDUCCIÓN
# -------------------------------------------------------------
try:
    while navegacion.estado != NavegadorPista.ESTADO_COMPLETADO:
        # Pasa el control a la máquina de estados de NavegadorPista
        navegacion.ejecutar_paso(pista)
        
        # Frecuencia de ciclo (~20ms / 50Hz)
        time.sleep_ms(20)

    print("🏁 ¡3 Vueltas completadas con éxito! Frenando...")

except KeyboardInterrupt:
    print("\n⚠️ Interrupción manual detectada. Frenando vehículo.")

finally:
    actuadores.stop()
    print("Vehículo detenido de forma segura.")
