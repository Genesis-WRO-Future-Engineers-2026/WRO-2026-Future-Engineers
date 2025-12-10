# VL53L1X library for Arduino

Version: 1.0.0<br>
Release date: 2018-06-25<br>

## Summary

This is a library for the Arduino IDE that helps interface with ST's VL53L1X. The library makes it simple to configure the sensor and read range data from it via I2C.

## Supported platforms

This library is designed to work with the Arduino IDE versions 1.6.x or later; we have not tested it with earlier versions.  This library should support any Arduino-compatible board, including the [Pololu A-Star controllers](https://www.pololu.com/category/149/a-star-programmable-controllers).

## Getting started

### Hardware

VL53L1X Distance Sensor from Waveshare:https://www.waveshare.com/vl53l1x-distance-sensor.htm

Make the following connections between the Arduino and the VL53L1X board:

#### 5V Arduino boards

(including Arduino Uno, Leonardo, Mega; Pololu A-Star 32U4)

    Arduino   VL53L1X board
    -------   -------------
         5V - VIN
        GND - GND
        SDA - SDA
        SCL - SCL

#### 3.3V Arduino boards

(including Arduino Due)

    Arduino   VL53L1X board
    -------   -------------
        3V3 - VIN
        GND - GND
        SDA - SDA
        SCL - SCL

### Software

If you are using version 1.6.2 or later of the [Arduino software (IDE)](http://www.arduino.cc/en/Main/Software), you can use the Library Manager to install this library:

1. In the Arduino IDE, open the "Sketch" menu, select "Include Library", then "Manage Libraries...".
2. Search for "VL53L1X".
3. Click the VL53L1X entry in the list.
4. Click "Install".

If this does not work, you can manually install the library:

1. Download the latest release archive from Waveshare Wiki:http://www.waveshare.com/wiki/VL53L1X_Distance_Sensor
2. Move the "VL53L1X-Arduino-Library" folder into the "libraries" directory inside your Arduino sketchbook directory.  You can view your sketchbook location by opening the "File" menu and selecting "Preferences" in the Arduino IDE.  If there is not already a "libraries" folder in that location, you should make the folder yourself.
3. After installing the library, restart the Arduino IDE.

## Examples

Several example sketches are available that show how to use the library. You can access them from the Arduino IDE by opening the "File" menu, selecting "Examples", and then selecting "VL53L1X". If you cannot find these examples, the library was probably installed incorrectly and you should retry the installation instructions above.

## ST's VL53L1X API and this library

Most of the functionality of this library is based on the [VL53L1X API](http://www.st.com/content/st_com/en/products/embedded-software/proximity-sensors-software/stsw-img007.html) provided by ST (STSW-IMG007), and some of the explanatory comments in the code are quoted or paraphrased from the API source code, API user manual (UM2356), and the VL53L1X datasheet. For more explanation about the library code and how it was derived from the API, see the comments in VL53L1X.cpp.
