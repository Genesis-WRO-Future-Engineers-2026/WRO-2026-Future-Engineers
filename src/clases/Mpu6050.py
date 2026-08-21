# Mpu6050.py
import machine
import time

class accel():
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto_mem(self.addr, 0x6B, b'\x00') # Despertar MPU6050

    def get_raw_values(self):
        a = self.i2c.readfrom_mem(self.addr, 0x3B, 14)
        return a

    def get_values(self):
        raw = self.get_raw_values()
        res = {}
        res["AcX"] = self.bytes_to_int(raw[0], raw[1])
        res["AcY"] = self.bytes_to_int(raw[2], raw[3])
        res["AcZ"] = self.bytes_to_int(raw[4], raw[5])
        res["Tmp"] = self.bytes_to_int(raw[6], raw[7]) / 340.00 + 36.53
        res["GyX"] = self.bytes_to_int(raw[8], raw[9])
        res["GyY"] = self.bytes_to_int(raw[10], raw[11])
        res["GyZ"] = self.bytes_to_int(raw[12], raw[13])
        return res

    def bytes_to_int(self, first_byte, second_byte):
        if not first_byte & 0x80:
            return first_byte << 8 | second_byte
        return -(((first_byte ^ 255) << 8) | (second_byte ^ 255) + 1)


class Mpu6050():
    """Clase adaptadora para que main.py pueda pedir get_yaw() directamente"""
    def __init__(self, scl_pin=9, sda_pin=8):
        self.scl_pin = scl_pin
        self.sda_pin = sda_pin
        self.sensor = None
        self.yaw = 0.0
        self.last_time = time.ticks_ms()
        self.gyro_z_offset = 0.0

    def begin(self):
        # Inicializa I2C en los mismos pines que usas para el bus
        i2c = machine.I2C(0, scl=machine.Pin(self.scl_pin), sda=machine.Pin(self.sda_pin), freq=100000)
        self.sensor = accel(i2c)
        
        # Calibración básica del Girosopio en reposo (Offset del Eje Z)
        print("Calibrando giroscopio... No muevas el vehículo...")
        suma = 0
        muestras = 50
        for _ in range(muestras):
            vals = self.sensor.get_values()
            suma += vals["GyZ"]
            time.sleep_ms(10)
        
        self.gyro_z_offset = suma / muestras
        self.last_time = time.ticks_ms()
        print("✓ Calibración completada.")

    def get_yaw(self):
        """Calcula el ángulo relativo de giro (Yaw) en grados integrando GyZ"""
        now = time.ticks_ms()
        dt = time.ticks_diff(now, self.last_time) / 1000.0 # Convertir ms a segundos
        self.last_time = now

        vals = self.sensor.get_values()
        
        # Restar el offset de calibración
        gyz_raw = vals["GyZ"] - self.gyro_z_offset
        
        # Convertir a grados por segundo (sensibilidad estándar del MPU6050 es 131 LSB/°/s)
        gyro_z_dps = gyz_raw / 131.0
        
        # Filtrar ruido pequeño cuando está detenido
        if abs(gyro_z_dps) < 0.5:
            gyro_z_dps = 0.0

        # Integrar la velocidad angular para obtener grados acumulados
        self.yaw += gyro_z_dps * dt
        return self.yaw
