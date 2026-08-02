# sensor_reader.py
import time
from machine import Pin, I2C
from vl53l0x import VL53L0X
import Config
from Kalman import KalmanFilter1D  # Filtro Kalman 1D

class SensorData:

    def __init__(self):
        self.distance = 0
        self.valid = False

class SensorReader:
    def __init__(self):
        # Creamos el array de datos estáticos (como el _sensorData[NUM_SENSORS])
        self._sensor_data = [SensorData() for _ in range(Config.NUM_SENSORS)]
        self._sensors = []
        self._i2c = None
        self.historial_sensores = [[] for _ in range(Config.NUM_SENSORS)]
        self.kalman = KalmanFilter1D()
        self.VENTANA_FILTRO = 4 #Hacer variable de Config o variable de clase.

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
                
                self._sensors.append(sensor_instancia)
                
                if Config.ENABLE_SERIAL:
                    print(f" Asignada dirección en hexadecimal: {hex(Config.SENSOR_ADDRESSES[i])}")
                    
            except Exception as e:
                print(" ¡ERROR! No responde en 0x29")
                return False

        print("=== Todos los sensores inicializados con éxito ===")
        return True

    def read_all(self):
        for i in range(Config.NUM_SENSORS):
            try:
                # Llama a la lectura del sensor
                distance_mm = self._sensors[i].read()

                # Comprobamos si la lectura es válida
                # El driver devuelve 0 si hay error de fase o de lectura (Equivalente al RangeStatus != 4)
                if distance_mm > 0:
                    
                    # Filtro de seguridad cap (RELIABLE_RANGE)
                    if distance_mm > Config.RELIABLE_RANGE:
                        distance_mm = Config.RELIABLE_RANGE
                    
                    self._sensor_data[i].distance = distance_mm
                    self._sensor_data[i].valid = (distance_mm >= Config.MIN_VALID_DISTANCE)
                else:
                    # Lectura inválida (Status de error)
                    self._sensor_data[i].distance = 0
                    self._sensor_data[i].valid = False
                    
            except Exception:
                # Protección si falla la línea física I2C en pleno bucle
                self._sensor_data[i].distance = 0
                self._sensor_data[i].valid = False

    def get_all_data(self):
        # Equivalente al const SensorData* getAllData()
        return self._sensor_data
    
    def get_filtered_data(self):
        """
        Recorre sensor a sensor usando un ciclo for interno.
        Devuelve una lista limpia de 5 elementos con distancias promediadas.
        """
        distancias_filtradas = []
        for i in range(Config.NUM_SENSORS):
            lectura_cruda = self._sensor_data[i].distance
            
            # Descarte de picos erróneos (Outliers)
            if lectura_cruda > 4000 or lectura_cruda < 0:
                if len(self.historial_sensores[i]) > 0:
                    lectura_cruda = self.historial_sensores[i][-1]
                else:
                    lectura_cruda = 0
            
            self.historial_sensores[i].append(lectura_cruda)
            if len(self.historial_sensores[i]) > self.VENTANA_FILTRO:
                self.historial_sensores[i].pop(0)
                
            promedio = sum(self.historial_sensores[i]) / len(self.historial_sensores[i])
            distancias_filtradas.append(promedio)
            
        return distancias_filtradas
