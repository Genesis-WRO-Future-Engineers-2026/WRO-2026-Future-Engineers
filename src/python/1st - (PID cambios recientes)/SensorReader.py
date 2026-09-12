# SensorReader.py

import time
from machine import Pin, I2C
from vl53l0x import VL53L0X
import Config


class SensorFrame:
    def __init__(self, distances, valid, age_ms):
        self.distances = distances
        self.valid = valid
        self.age_ms = age_ms

        self.fresh = [
            distance is not None and age == 0
            for distance, age in zip(distances, age_ms)
        ]


class SensorReader:

    def __init__(self):
        self._sensors = [None] * Config.NUM_SENSORS[cite: 9]
        self._i2c = None
        self.historial_sensores = [
            [] for _ in range(Config.NUM_SENSORS)[cite: 9]
        ]
        self.VENTANA_FILTRO = 5
        self.available = [False] * Config.NUM_SENSORS[cite: 9]
        self.filtered = [None] * Config.NUM_SENSORS[cite: 9]
        self.last_valid = [None] * Config.NUM_SENSORS[cite: 9]
        self.last_valid_ms = [0] * Config.NUM_SENSORS[cite: 9]

    def begin(self):
        self._i2c = I2C(
            Config.I2C_ID,
            scl=Pin(Config.I2C_SCL_PIN),
            sda=Pin(Config.I2C_SDA_PIN),
            freq=Config.I2C_FREQ
        )

        print("=== Inicializando Sensores ToF vía XSHUT ===")

        xshut_objects = []

        for i in range(Config.NUM_SENSORS):
            pin_out = Pin(
                Config.XSHUT_PINS[i],
                Pin.OUT
            )
            pin_out.value(0)
            xshut_objects.append(pin_out)

        time.sleep_ms(Config.SENSOR_RESET_MS)

        for i in range(Config.NUM_SENSORS):
            xshut_objects[i].value(1)
            time.sleep_ms(Config.SENSOR_BOOT_MS)

            try:
                devices = self._i2c.scan()
                if 0x29 not in devices:
                    xshut_objects[i].value(0)
                    continue
            except Exception:
                xshut_objects[i].value(0)
                continue

            try:
                sensor_instancia = VL53L0X(
                    self._i2c,
                    address=0x29
                )
            except Exception:
                xshut_objects[i].value(0)
                continue

            try:
                nueva_direccion = Config.SENSOR_ADDRESSES[i]
                sensor_instancia.set_address(nueva_direccion)
            except Exception:
                xshut_objects[i].value(0)
                continue

            try:
                offset = Config.SENSOR_OFFSETS[i]
                sensor_instancia.set_offset(offset)
            except Exception:
                xshut_objects[i].value(0)
                continue

            self._sensors[i] = sensor_instancia
            self.available[i] = True

        initialized = sum(1 for x in self.available if x)[cite: 9]
        return initialized > 0

    def _read_one(self, i):
        sensor = self._sensors[i]

        if sensor is None:
            return None

        try:
            value = sensor.read()

            if value is None:
                return None

            value = int(value) + Config.SENSOR_OFFSETS[i][cite: 9]

            # =====================================================
            # CORRECCIÓN INDIVIDUAL POR CANAL (Ajustado a tus pruebas)
            # =====================================================
            if i == Config.LEFT:         # L
                value = int(value * 0.8)  
            elif i == Config.LEFT_DIAG:  # LD (Estaba muy bajo)
                value = int(value * 3.5) + 40 
            elif i == Config.FRONT:      # F
                value = int(value * 0.85)
            elif i == Config.RIGHT_DIAG: # RD (Estaba muy alto)
                value = int(value * 0.5)
            elif i == Config.RIGHT:      # R (Estaba muy bajo)
                value = int(value * 4.0) + 20

            # Validación física
            if value < Config.MIN_VALID_DISTANCE_MM:
                return Config.MIN_VALID_DISTANCE_MM

            if value > Config.MAX_VALID_DISTANCE_MM:
                return Config.MAX_VALID_DISTANCE_MM

            return value 

        except Exception:
            return None

    def read_all(self):
        now = time.ticks_ms()[cite: 9]
        distances = [None] * Config.NUM_SENSORS[cite: 9]
        valid = [False] * Config.NUM_SENSORS[cite: 9]
        ages = [999999] * Config.NUM_SENSORS[cite: 9]

        for i in range(Config.NUM_SENSORS):
            raw = self._read_one(i)

            if raw is not None:
                if self.filtered[i] is None:
                    self.filtered[i] = float(raw)
                else:
                    a = Config.FILTER_ALPHA
                    self.filtered[i] = (
                        a * raw
                        + (1.0 - a) * self.filtered[i]
                    )

                self.last_valid[i] = self.filtered[i]
                self.last_valid_ms[i] = now
                distances[i] = self.last_valid[i]
                valid[i] = True
                ages[i] = 0

            elif self.last_valid[i] is not None:
                age = time.ticks_diff(now, self.last_valid_ms[i])[cite: 9]
                ages[i] = age

                if age <= Config.STALE_TIMEOUT_MS:
                    distances[i] = self.last_valid[i]
                    valid[i] = True
                else:
                    distances[i] = None
                    valid[i] = False
            else:
                distances[i] = None
                valid[i] = False
                ages[i] = 999999

        return SensorFrame(distances, valid, ages)[cite: 9]