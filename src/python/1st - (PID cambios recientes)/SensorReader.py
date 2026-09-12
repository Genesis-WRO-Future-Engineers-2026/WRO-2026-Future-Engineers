# sensor_reader.py
import time
from machine import Pin, I2C
from vl53l0x import VL53L0X
import Config

class SensorFrame:
    def __init__(self, distances, valid, age_ms):
        self.distances = distances
        self.valid = valid
        self.age_ms = age_ms

class SensorReader:
    
    
    def __init__(self):
        self._sensors = []
        self._i2c = None
        self.historial_sensores = [[] for _ in range(Config.NUM_SENSORS)]
        self.VENTANA_FILTRO = 3 #Hacer variable de Config o variable de clase.
        self.available = [False] * Config.NUM_SENSORS
        self.filtered = [None] * Config.NUM_SENSORS
        self.last_valid_ms = [0] * Config.NUM_SENSORS

    def begin(self):
        # Inicializa I2C a 400 kHz (Wire.setClock(400000))
        # Ajusta pin SCL y SDA según tus conexiones en el ESP32-S2 Mini
        self._i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100000)

        print("=== Inicializando Sensores ToF vía XSHUT ===")

        # PASO 1: Configurar pines como salida y APAGAR todos los sensores (LOW)
        xshut_objects = []
        for i in range(Config.NUM_SENSORS):
            pin_out = Pin(Config.XSHUT_PINS[i], Pin.OUT)
            pin_out.value(0)  # digitalWrite(XSHUT_PINS[i], LOW)
            xshut_objects.append(pin_out)
        
        time.sleep_ms(100)  # delay(100) para el reset de hardware

        # PASO 2: Encender y configurar uno por uno
        for i in range(Config.NUM_SENSORS):
            # Activamos el sensor actual poniendo su XSHUT en HIGH (1)
            xshut_objects[i].value(1)
            time.sleep_ms(10)  # delay(10)

            print(f"Iniciando Sensor {i} en pin {Config.XSHUT_PINS[i]} con ángulo {Config.SENSOR_ANGLES[i]}°...")

            try:
                # Todos los sensores despiertan en 0x29 de fábrica
                sensor_instancia = VL53L0X(self._i2c, address=0x29)
                
                # Cambiamos su dirección inmediatamente a su dirección única definitiva
                sensor_instancia.set_address(Config.SENSOR_ADDRESSES[i])
                
                if Config.ENABLE_SERIAL:
                    print(f"Desfase sensor {i} {Config.SENSOR_OFFSETS[i]}")
                
                sensor_instancia.set_offset(Config.SENSOR_OFFSETS[i])
                
                self._sensors.append(sensor_instancia)
                self.available.append(True)
                
                if Config.ENABLE_SERIAL:
                    print(f" Asignada dirección en hexadecimal: {hex(Config.SENSOR_ADDRESSES[i])}")
                    
            except Exception as e:
                print(" ¡ERROR! No responde en 0x29")
                return False

        print("=== Todos los sensores inicializados con éxito ===")
        return True

    def _read_one(self, i):
        sensor = self._sensors[i]
        if sensor is None:
            return None
        try:
            value = sensor.read() #Agregar offsets de sensores
            if value is None:
                return None
            value = int(value)
            if value < Config.MIN_VALID_DISTANCE_MM or value > Config.MAX_VALID_DISTANCE_MM:
                return None
            return value
        except Exception:
            return None

    def read_all(self):
        now = time.ticks_ms()
        distances = [None] * Config.NUM_SENSORS
        valid = [False] * Config.NUM_SENSORS
        ages = [999999] * Config.NUM_SENSORS

        for i in range(Config.NUM_SENSORS):
            raw = self._read_one(i)
            if raw is not None:
                if self.filtered[i] is None:
                    self.filtered[i] = float(raw)
                else:
                    a = Config.FILTER_ALPHA
                    self.filtered[i] = a * raw + (1.0 - a) * self.filtered[i]
                self.last_valid_ms[i] = now
                distances[i] = self.filtered[i]
                valid[i] = True
                ages[i] = 0
            elif self.filtered[i] is not None:
                age = time.ticks_diff(now, self.last_valid_ms[i])
                ages[i] = age
                if age <= Config.STALE_TIMEOUT_MS:
                    distances[i] = self.filtered[i]
                    valid[i] = False  # dato disponible pero no fresco

        return SensorFrame(distances, valid, ages)

