# main.py - MODO SIMULACIÓN / SIN HARDWARE
import time
from machine import Pin, PWM

# -------------------------------------------------------------
# 1. HARDWARE Y CLASES ADAPTADORAS
# -------------------------------------------------------------
pin_pwm_motor = PWM(Pin(14), freq=1000)
pin_dir_1 = Pin(12, Pin.OUT)
pin_dir_2 = Pin(13, Pin.OUT)
pin_servo = PWM(Pin(15), freq=50)

class Actuadores:
    def set_speed(self, velocidad):
        print(f"[MOTORES] Velocidad actual: {velocidad}%")

    def set_steering(self, angulo_correccion):
        print(f"[SERVO] Ángulo corrección: {angulo_correccion}°")

    def stop(self):
        print("[MOTORES] Frenando vehículo.")

# --- SIMULADOR DE SENSORES Y MPU ---
class SensorReaderMock:
    def begin(self):
        print("⚠️ MODO SIMULACIÓN: Sensores ToF simulados activos.")
        return True

    def read_all(self):
        pass

    def get_filtered_data(self):
        # Devuelve distancias simuladas en mm: [Izq90, Izq45, Frontal, Der45, Der90]
        return [400.0, 500.0, 600.0, 500.0, 400.0]

class Mpu6050Mock:
    def begin(self):
        print("⚠️ MODO SIMULACIÓN: MPU6050 simulada activa.")

    def get_values(self):
        # Devuelve lecturas simuladas en reposo
        return {"GyZ": 0.0, "AcX": 0, "AcY": 0, "AcZ": 0}

class Carro:
    def __init__(self, sensores, actuadores):
        self.sensores = sensores
        self.actuadores = actuadores

class Pista:
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

# Importar NavegadorPista seguro
try:
    from Navegacion import NavegadorPista
except Exception as e:
    print(f"Error importando Navegacion: {e}")

# -------------------------------------------------------------
# 2. INICIALIZACIÓN (CON MOCKS)
# -------------------------------------------------------------
print("=== INICIALIZANDO VEHÍCULO AUTÓNOMO (MODO PRUEBA) ===")

sensores = SensorReaderMock() # Usamos simulador
actuadores = Actuadores()
carro = Carro(sensores, actuadores)
imu = Mpu6050Mock()           # Usamos simulador
pista = Pista()

sensores.begin()
imu.begin()

navegacion = NavegadorPista(carro=carro, mpu=imu)

print("✅ ¡Vehículo Simulado Listo! Arrancando...")
time.sleep(1)

# -------------------------------------------------------------
# 3. BUCLE PRINCIPAL DE CONDUCCIÓN
# -------------------------------------------------------------
try:
    pasos = 0
    # Corremos solo 20 iteraciones para probar el bucle
    while navegacion.estado != NavegadorPista.ESTADO_COMPLETADO and pasos < 20:
        navegacion.ejecutar_paso(pista)
        pasos += 1
        time.sleep_ms(100)

    print("🏁 Prueba finalizada con éxito en la consola.")

except KeyboardInterrupt:
    print("\n⚠️ Interrupción manual detectada.")

finally:
    actuadores.stop()
