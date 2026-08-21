/*
 * SensorReader.h
 *
 * Reads VL53L1X sensors through the TCA9548A I2C multiplexer.
 */

#ifndef SENSOR_READER_H
#define SENSOR_READER_H

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_VL53L0X.h> // Cambiado a la librería de tu .ino

#include "Config.h"

struct SensorData {
    uint16_t distance;  
    bool valid;         
};

class SensorReader {
   private:
    Adafruit_VL53L0X _sensors[NUM_SENSORS]; // Cambiado a VL53L0X
    SensorData _sensorData[NUM_SENSORS];

   public:
    SensorReader();
    bool begin();
    void readAll();
    const SensorData* getAllData() const;
};

#endif
