# SensorReader.py

import time
from machine import Pin, I2C
from vl53l0x import VL53L0X
import Config


class SensorFrame:
    """
    Contiene el estado completo de los sensores en un instante.

    distances[i]:
        Distancia disponible para el sensor i.
        Puede ser una lectura nueva o la última lectura válida conocida.

    valid[i]:
        True  -> el dato todavía se considera utilizable.
        False -> no existe un dato suficientemente reciente.

    fresh[i]:
        True  -> la distancia corresponde a una lectura obtenida
                 en este mismo ciclo.
        False -> se está utilizando una lectura anterior.

    age_ms[i]:
        Edad de la última lectura válida en milisegundos.
    """

    def __init__(self, distances, valid, age_ms):
        self.distances = distances
        self.valid = valid
        self.age_ms = age_ms

        # Una lectura es "fresh" únicamente cuando su edad es 0.
        self.fresh = [
            distance is not None and age == 0
            for distance, age in zip(distances, age_ms)
        ]


class SensorReader:

    def __init__(self):

        # IMPORTANTE:
        # Mantener una posición fija para cada sensor.
        # No usar append() durante la inicialización porque si un sensor
        # falla se desplazarían los índices.
        self._sensors = [None] * Config.NUM_SENSORS

        self._i2c = None

        # Historial, si posteriormente quieres implementar otros filtros.
        self.historial_sensores = [
            [] for _ in range(Config.NUM_SENSORS)
        ]

        self.VENTANA_FILTRO = 3

        # Indica si el hardware del sensor fue inicializado correctamente.
        self.available = [False] * Config.NUM_SENSORS

        # Estado del filtro.
        self.filtered = [None] * Config.NUM_SENSORS

        # ---------------------------------------------------------
        # ÚLTIMA LECTURA VÁLIDA
        # ---------------------------------------------------------
        #
        # Esta es la memoria que utilizaremos cuando una lectura
        # nueva falle temporalmente.
        #
        self.last_valid = [None] * Config.NUM_SENSORS

        # Momento en que se recibió la última lectura válida.
        self.last_valid_ms = [0] * Config.NUM_SENSORS

    # =============================================================
    # INICIALIZACIÓN
    # =============================================================

    def begin(self):

        self._i2c = I2C(
            Config.I2C_ID,
            scl=Pin(Config.I2C_SCL_PIN),
            sda=Pin(Config.I2C_SDA_PIN),
            freq=Config.I2C_FREQ
        )

        print("=== Inicializando Sensores ToF vía XSHUT ===")

        # ---------------------------------------------------------
        # PASO 1:
        # Apagar todos los sensores.
        # ---------------------------------------------------------

        xshut_objects = []

        for i in range(Config.NUM_SENSORS):

            pin_out = Pin(
                Config.XSHUT_PINS[i],
                Pin.OUT
            )

            pin_out.value(0)
            xshut_objects.append(pin_out)

        time.sleep_ms(Config.SENSOR_RESET_MS)

        # ---------------------------------------------------------
        # PASO 2:
        # Inicializar uno por uno.
        # ---------------------------------------------------------

        for i in range(Config.NUM_SENSORS):

            # Encendemos solamente este sensor.
            xshut_objects[i].value(1)

            time.sleep_ms(Config.SENSOR_BOOT_MS)

            print(
                "Iniciando Sensor {} en pin {} con ángulo {}°...".format(
                    i,
                    Config.XSHUT_PINS[i],
                    Config.SENSOR_ANGLES[i]
                )
            )

            # -----------------------------------------------------
            # Comprobación opcional del bus.
            # -----------------------------------------------------

            try:

                devices = self._i2c.scan()

                if Config.ENABLE_SERIAL:
                    print(
                        " I2C detectado: {}".format(
                            [hex(x) for x in devices]
                        )
                    )

                if 0x29 not in devices:

                    print(
                        " ¡ERROR! Sensor {} no aparece en 0x29".format(i)
                    )

                    # Apagamos este sensor y continuamos.
                    xshut_objects[i].value(0)

                    continue

            except Exception as e:

                print(
                    " ¡ERROR! No se pudo escanear I2C: {}".format(
                        repr(e)
                    )
                )

                xshut_objects[i].value(0)

                continue

            # -----------------------------------------------------
            # Crear instancia del driver.
            # -----------------------------------------------------

            try:

                sensor_instancia = VL53L0X(
                    self._i2c,
                    address=0x29
                )

            except Exception as e:

                print(
                    " ¡ERROR! Falló la inicialización del "
                    "sensor {}: {}".format(i, repr(e))
                )

                # MUY IMPORTANTE:
                # No continuar con set_address() si el constructor
                # del driver falló.
                #
                # Si continuáramos, podríamos escribir sobre un
                # dispositivo que realmente no fue inicializado.
                xshut_objects[i].value(0)

                continue

            # -----------------------------------------------------
            # Cambiar dirección.
            # -----------------------------------------------------

            try:

                nueva_direccion = Config.SENSOR_ADDRESSES[i]

                sensor_instancia.set_address(
                    nueva_direccion
                )

                if Config.ENABLE_SERIAL:
                    print(
                        " Dirección asignada: {}".format(
                            hex(nueva_direccion)
                        )
                    )

            except Exception as e:

                print(
                    " ¡ERROR! No se pudo cambiar la dirección "
                    "del sensor {}: {}".format(
                        i,
                        repr(e)
                    )
                )

                xshut_objects[i].value(0)

                continue

            # -----------------------------------------------------
            # Offset.
            # -----------------------------------------------------

            try:

                offset = Config.SENSOR_OFFSETS[i]

                if Config.ENABLE_SERIAL:
                    print(
                        " Offset sensor {}: {}".format(
                            i,
                            offset
                        )
                    )

                sensor_instancia.set_offset(offset)

            except Exception as e:

                print(
                    " ¡ERROR! No se pudo configurar offset "
                    "del sensor {}: {}".format(
                        i,
                        repr(e)
                    )
                )

                xshut_objects[i].value(0)

                continue

            # -----------------------------------------------------
            # Guardar sensor en su posición.
            # -----------------------------------------------------

            self._sensors[i] = sensor_instancia
            self.available[i] = True

            print(
                " Sensor {} inicializado correctamente.".format(i)
            )

        # ---------------------------------------------------------
        # Resultado final.
        # ---------------------------------------------------------

        initialized = sum(
            1 for x in self.available if x
        )

        print(
            "=== Sensores inicializados: {}/{} ===".format(
                initialized,
                Config.NUM_SENSORS
            )
        )

        # No exigimos necesariamente que estén los 5 sensores.
        # El controlador decidirá qué hacer según los sensores
        # disponibles.
        return initialized > 0

    # =============================================================
    # LECTURA DE UN SENSOR
    # =============================================================

    def _read_one(self, i):

        sensor = self._sensors[i]

        if sensor is None:
            return None

        try:

            value = sensor.read()

            if value is None:
                return None

            value = int(value)

            # -----------------------------------------------------
            # Validación física.
            # -----------------------------------------------------

            if value < Config.MIN_VALID_DISTANCE_MM:
                return Config.MIN_VALID_DISTANCE_MM

            if value > Config.MAX_VALID_DISTANCE_MM:
                return Config.MAX_VALID_DISTANCE_MM

            return value

        except Exception:

            # Una lectura individual que falla no debe derribar
            # todo el sistema.
            return None

    # =============================================================
    # LECTURA DE TODOS LOS SENSORES
    # =============================================================

    def read_all(self):

        now = time.ticks_ms()

        distances = [None] * Config.NUM_SENSORS

        valid = [False] * Config.NUM_SENSORS

        ages = [999999] * Config.NUM_SENSORS

        # ---------------------------------------------------------
        # Leer sensores individualmente.
        # ---------------------------------------------------------

        for i in range(Config.NUM_SENSORS):

            raw = self._read_one(i)

            # =====================================================
            # CASO 1:
            # Lectura nueva y válida.
            # =====================================================

            if raw is not None:

                # -------------------------------------------------
                # Filtro exponencial.
                # -------------------------------------------------

                if self.filtered[i] is None:

                    self.filtered[i] = float(raw)

                else:

                    a = Config.FILTER_ALPHA

                    self.filtered[i] = (
                        a * raw
                        + (1.0 - a) * self.filtered[i]
                    )

                # -------------------------------------------------
                # Guardamos explícitamente la última lectura válida.
                # -------------------------------------------------

                self.last_valid[i] = self.filtered[i]

                # -------------------------------------------------
                # Actualizamos el timestamp.
                # -------------------------------------------------

                self.last_valid_ms[i] = now

                # -------------------------------------------------
                # El dato está disponible y es fresco.
                # -------------------------------------------------

                distances[i] = self.last_valid[i]

                valid[i] = True

                ages[i] = 0

            # =====================================================
            # CASO 2:
            # La lectura nueva falló.
            # =====================================================

            elif self.last_valid[i] is not None:

                age = time.ticks_diff(
                    now,
                    self.last_valid_ms[i]
                )

                ages[i] = age

                # -------------------------------------------------
                # La última lectura todavía es suficientemente
                # reciente como para reutilizarla.
                # -------------------------------------------------

                if age <= Config.STALE_TIMEOUT_MS:

                    distances[i] = self.last_valid[i]

                    # IMPORTANTE:
                    #
                    # El dato sigue siendo válido para el
                    # controlador, pero NO es fresco.
                    #
                    valid[i] = True

                # -------------------------------------------------
                # La última lectura ya es demasiado antigua.
                # -------------------------------------------------

                else:

                    distances[i] = None

                    valid[i] = False

            # =====================================================
            # CASO 3:
            # Nunca hemos tenido una lectura válida.
            # =====================================================

            else:

                distances[i] = None

                valid[i] = False

                ages[i] = 999999

        # ---------------------------------------------------------
        # Crear frame.
        # ---------------------------------------------------------

        return SensorFrame(
            distances,
            valid,
            ages
        )