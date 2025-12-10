/*
  Reading distance from the laser based VL53L1X
  By: kaloha
  Waveshare Electronics
  VL53L1X Distance Sensor from Waveshare: https://www.waveshare.com/vl53l1x-distance-sensor.htm
  This example demonstrates how to read the distance in long mode(up to 4m).
*/

#include <Wire.h>
#include "VL53L1X.h"

VL53L1X Distance_Sensor;

void setup()
{
  Wire.begin();
  Wire.setClock(400000); // use 400 kHz I2C

  Serial.begin(115200);
  Serial.println("VL53L1X Distance Sensor tests in long distance mode(up to 4m).");
  Distance_Sensor.setTimeout(500);
  if (!Distance_Sensor.init())
  {
    Serial.println("Failed to initialize VL53L1X Distance_Sensor!");
    while (1);
  }
  
  // Use long distance mode and allow up to 50000 us (50 ms) for a measurement.
  // You can change these settings to adjust the performance of the sensor, but
  // the minimum timing budget is 33 ms for medium and long distance mode
  Distance_Sensor.setDistanceMode(VL53L1X::Long);
  Distance_Sensor.setMeasurementTimingBudget(50000);

  // Start continuous readings at a rate of one measurement every 50 ms (the
  // inter-measurement period). This period should be at least as long as the
  // timing budget.
  Distance_Sensor.startContinuous(50);
}

void loop()
{
  Distance_Sensor.read();
  Serial.print("Distance(mm): ");
  Serial.print(Distance_Sensor.ranging_data.range_mm);
  Serial.println();
}
