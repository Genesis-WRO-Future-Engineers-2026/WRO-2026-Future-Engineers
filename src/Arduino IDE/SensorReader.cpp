#include "SensorReader.h"
#include "Logger.h"

SensorReader::SensorReader() {
    for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
        _sensorData[i].distance = 0;
        _sensorData[i].valid = false;
    }
}

bool SensorReader::begin() {
    Wire.begin();
    Wire.setClock(400000); // 400 kHz

    Logger::println("=== Inicializando Sensores ToF vía XSHUT ===");

    // PASO 1: Configurar pines como salida y APAGAR todos los sensores
    for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
        pinMode(XSHUT_PINS[i], OUTPUT);
        digitalWrite(XSHUT_PINS[i], LOW);
    }
    delay(100); // Dar tiempo a que todos se reinicien

    // PASO 2: Encender y configurar uno por uno
    for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
        // Activamos el sensor actual poniendo su XSHUT en HIGH
        digitalWrite(XSHUT_PINS[i], HIGH);
        delay(10); 

        Logger::print("Iniciando Sensor ");
        Logger::print(i);
        Logger::print(" en pin ");
        Logger::print(XSHUT_PINS[i]);
        Logger::print(" con ángulo ");
        Logger::print(SENSOR_ANGLES[i]);
        Logger::print("°...");

        // Todos los sensores VL53L0X despiertan por defecto en la dirección de fábrica 0x29
        if (!_sensors[i].begin(0x29)) {
            Logger::println(" ¡ERROR! No responde en 0x29");
            return false;
        }

        // Cambiamos su dirección inmediatamente a su dirección única definitiva
        _sensors[i].setAddress(SENSOR_ADDRESSES[i]);
        
        Logger::print(" Asignada dirección en hexadecimal: ");
        // Imprimimos la dirección usando Serial directo para evitar el conflicto con el Logger
        #if ENABLE_SERIAL
        Serial.println(SENSOR_ADDRESSES[i], HEX);
        #endif
    }

    Logger::println("=== Todos los sensores inicializados con éxito ===");
    return true;
}

void SensorReader::readAll() {
    VL53L0X_RangingMeasurementData_t measurement;

    for (uint8_t i = 0; i < NUM_SENSORS; ++i) {
        // Ya no llamamos a _selectChannel. Leemos directamente del objeto.
        _sensors[i].rangingTest(&measurement, false);

        // Comprobamos si la lectura es válida (Status 4 suele ser error de fase/rango en Adafruit)
        if (measurement.RangeStatus != 4) {
            _sensorData[i].distance = measurement.RangeMilliMeter;
            
            if (_sensorData[i].distance > RELIABLE_RANGE) {
                _sensorData[i].distance = RELIABLE_RANGE;
            }
            
            _sensorData[i].valid = (_sensorData[i].distance >= MIN_VALID_DISTANCE);
        } else {
            _sensorData[i].distance = 0;
            _sensorData[i].valid = false;
        }
    }
}

const SensorData* SensorReader::getAllData() const { return _sensorData; }
