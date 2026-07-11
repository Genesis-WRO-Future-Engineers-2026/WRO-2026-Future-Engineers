# Hello! We are the Génesis team from Venezuela.
<img width="903" height="675" alt="2afa2ad2-66f1-48aa-bc96-628adb1001fa" src="https://github.com/user-attachments/assets/f253592e-f094-4885-bef9-549df2e346e6" />

# WRO - Future Engineers - Robotics Project Documentation

## 👥Team Members
- **Johelis Acosta**
  *Role*: Electronics and Mechanics
- **Miguel Mejías**
  *Role*: Programmer
- **Wilber Pacheco**
*Role*: Designer

## 🧑🏻‍🔧Coach
- **Oswal Melean**
  *Mechanical Engineer*

Welcome to our repository. We are a student group dedicated to robotics and innovation, and in this space we document our design process: hardware architecture, code development, parts selection, and the robot's testing history.

<a name="top"></a>

## 🔍Table of Contents

<!-- toc -->

- [1. 📚Overview](#1-overview)
  - [1.1 About the Project](#11-about-the-project)
  - [1.2 Robot Images](#12-robot-images)
  - [1.3 Performance Video](#13-performance-video)
- [2. 🔩Mobility and mechanical design](#2-mobility-and-mechanical-design)
  - [2.1 Drive System](#21-drive-system)
  - [2.2 Steering](#22-steering)
  - [2.3 Chassis Design](#23-chassis-design)
-  [3. 🔋Power architecture and sensors](#3-Power-architecture-and-sensors)
   - [3.1 Power Source](#31-power-source)
   - [3.2 Sensors and Camera](#32-sensors-and-camera)
   - [3.3 Processing Units](#33-processing-units)
   - [3.4 Circuit Diagram](#34-circuit-diagram)
   - [3.5 Power Consumption](#35-power-consumption)
- [4. 📐Software architecture and obstacle strategy](#4-Software-architecture-and-obstacle-strategy)
  - [4.1 Open Challenge](#41-open-challenge)
  - [4.2 Obstacle Challenge](#42-obstacle-challenge)
  - [4.3 Parallel Parking](#43-parallel-parking)
- [5. ⚙Systems thinking and engineering decisions](#5-Systems-thinking-and-engineering-decisions)
  - [5.1 Code Structure](#52-code-structure)
  - [5.2 Compilation / Upload Instructions](#53-compilation--upload-instructions)
- [6. 📝List of Components](#6-list-of-components)
- [7. 💎3D Model Files](#7-3d-model-files)
  - [7.1 STL Files](#72-stl-files)
  - [7.2 Modified Files](#73-slicer-files)
- [8. 🛠️Building Instructions](#8-building-instructions)

  
    <!-- tocstop -->

## 1. 📚Overview

### 1.1 About the Project

This project focuses on the design, construction, and programming of an autonomous vehicle capable of overcoming the complex challenges and obstacles of the WRO Future Engineers competition with precision and speed.

For Team Genesis, this challenge represents the perfect opportunity to put theory into practice, combining a passion for technological innovation with creative problem-solving through a systematic process of research, prototyping, and constant iteration.

Our robot’s structure is based on a robust architecture inspired by the *zcar* hardware (https://github.com/alexyu132/zcar). We subjected this design to an extensive re-engineering process using Fusion 360 and Blender to optimize screw and nut housing dimensions, as well as to customize parts for a perfect fit of our components.

The system's core is controlled by a Raspberry Pi 3 B+ that manages the main logic, supported by an ESP32 S2 Mini module to control the sensors and motors. To achieve precise navigation and efficient obstacle avoidance, the robot integrates Time-of-Flight (ToF) sensors alongside a gyroscope for stabilization and track orientation.

This entire development process has been backed by detailed documentation that not only optimizes our workflow but also demonstrates our technical and collaborative skills, as well as our commitment to hands-on learning.

### 1.2 Robot Images

### 1.3 Performance Video

[Part 1: Open Challenge Video]()

[Part 2: Obstacle Challenge Video]()


<p align="right">
  <a href="#top">Back To Top</a>
</p>

## 2. 🔩Mobility and mechanical design

### 2.1 Drive System

### 2.2 Steering

### 2.3 Chassis Design

<p align="right">
  <a href="#top">Back To Top</a>
</p>

## 3. 🔋Power architecture and sensors

### 3.1 Power Source

### 3.2 Sensor and Camera

#### VL53L0X Distance Sensor

The VL53L0X is a small, popular distance sensor that uses Time-of-Flight (ToF) technology to measure the distance to an object by emitting a pulse of invisible infrared laser light and calculating the time it takes to return.

We selected it for this project due to three key advantages:

-  **Ultra-compact size**: Its small footprint allows for easy integration into tight spaces without compromising the prototype's design.
  
-  **Easy integration**: It offers excellent compatibility and ready-to-use libraries, drastically simplifying programming.
  
-  **High speed**: It is capable of performing laser-based distance measurements in record time, ensuring fast, accurate, real-time readings.
  
  <img width="800" height="800" alt="GY-53VL53L0XLaserToFFlightTimeRangeSensorfront_1" src="https://github.com/user-attachments/assets/66a3e217-320e-4afe-9cc8-b6d77926fc41" />


| **Extent** | **Value** |
|------------|-----------|
| Largo      | 25 mm     |
| Alto       | 1 mm      |
| Ancho      | 10.7 mm   |
| Peso       | 0.8 g     |

#### Inertial Measurement Unit (IMU MPU-6050) Sensor

The MPU-6050 is a widely used Inertial Measurement Unit (IMU) that integrates a 3-axis gyroscope and a 3-axis accelerometer onto a single chip. It uses this combination to accurately measure linear acceleration and angular velocity, enabling the determination of the prototype's orientation, tilt, and movement in space.

Key advantages of the device:

- **Ultra-compact size**: By integrating the accelerometer and gyroscope onto a tiny board, it maximizes space efficiency within our circuit.
  
- **Easy integration**: Thanks to I2C protocol communication and a vast array of available libraries, setup and data reading are extremely straightforward.
  
- **High speed**: It features an internal Digital Motion Processor (DMP) that rapidly executes complex algorithms, delivering stable, real-time data without overloading the main microcontroller.

<img width="1200" height="1200" alt="modulo-mpu6050-acelerometro-giroscopio-i2c" src="https://github.com/user-attachments/assets/da02f10c-e98b-41c9-a799-f0f82457208e" />


| **Extent** | **Value** |
|------------|-----------|
| Largo      | 21.2 mm   |
| Ancho      | 16.4 mm   |
| Alto       | 3.3 mm    |
| Peso       | 2.1 g     |

#### Computer Vision Camera (Modified 1080p FHD Webcam)

To equip the vehicle with a computer vision system, we integrated a high-definition (1080p FHD) webcam. However, because the original commercial unit—including its casing and mount—was too large and heavy (80 mm x 33 mm x 40 mm), we performed a hardware modification by removing the entire external plastic structure. This allowed us to extract the internal camera module, resulting in a functional circuit board measuring just **25 mm x 28.5 mm**.

Key advantages of the modified device:

- **Ultra-compact size (post-modification)**: By drastically reducing its dimensions to just 25 mm x 28.5 mm, we were able to mount it on the front of the vehicle without compromising aerodynamics or the chassis design.
  
- **Easy integration and stability**: Despite being disassembled, it retains native USB connectivity and direct compatibility with computer vision algorithms (such as OpenCV), simplifying programming.
  
- **High speed and resolution**: It maintains 1080p FHD capture, processing sharp images in real-time—a critical factor for decision-making while the vehicle is in motion.

#### Dimensions Comparison (Webcam)


<div align="center">
  <i>Before</i>
  <br>
 <img width="1024" height="1024" alt="productos34_25510" src="https://github.com/user-attachments/assets/64d0bc72-e8c2-4080-8f3f-c7b37652012b" />
</div> 


|          **State**           |**Long** |**Broad**|**High**|
|------------------------------|---------|---------|--------|
| With Casing (Original)       | 80 mm   | 40 mm   | 33 mm  |



<div align="center">
 <i>After</i>
 <img width="1702" height="1599" alt="1783617511143" src="https://github.com/user-attachments/assets/4e1c87a2-014d-4601-af65-98bbfaef934c" />
 <br>
</div>
  
 
|          **State**           |**Long** |**Broad**|**High**|
|------------------------------|---------|---------|--------|
| Without Casing (Modified)    | 25 mm   | 28.5 mm | 2mm    |



### 3.3 Processing Units 

Equipped with a 1.4 GHz 64-bit ARM Cortex-A53 processor, the Raspberry Pi 3 B+ is our primary controller of choice. We decided to use the Raspberry Pi 3 B+ for several reasons, including:

- **Compatibility**: There are many components (such as standard USB webcams) that are easy to implement with the Raspberry Pi 3 B+.
  
- **Power**: The Raspberry Pi 3 B+ offers efficient, balanced performance; thanks to this, demanding tasks—such as real-time image processing—are easily handled by the device.
  
- **Portability**: The Raspberry Pi 3 B+ stands out among controllers; weighing just 45 g, it is lightweight, making it a practical and reliable choice for integration into the Eva 01.


<div align="center">
 <i>Raspberry Pi 3 B+</i>
 <img width="1200" height="1200" alt="raspberry-pi-3-b-plus" src="https://github.com/user-attachments/assets/fb22d270-ab59-46c8-af45-43ecbb1fe371" />
 <br>
</div>

|**Dimension**|**Value**|
|-------------|---------|
| Length      | 85 mm   |
| Height      | 17 mm   |
| Width       | 56 mm   |
| Weight      | 45 g    |

While the Raspberry Pi 3 B+ is capable of real-time image processing, we recognized that it needed some assistance to avoid being overloaded by the sensors; consequently, we decided to incorporate an ESP32-S2 Mini to control the sensors and their actuators in order to achieve the necessary level of processing.

|**Dimension**|**Value**|
|-------------|---------|
| Length      | 34,3 mm |
| Height      | 17 mm   |
| Width       | 25,4 mm |
| Weight      | 5,31 g  |

### 3.4 Circuit Diagram 

### 3.5 Power Consumption

<p align="right">
  <a href="#top">Back To Top</a>
</p>

## 4. 📐Software architecture and obstacle strategy

### 4.1 Open Challenge

### 4.2 Obstacle Challenge

### 4.3 Parallel Parking

<p align="right">
  <a href="#top">Back To Top</a>
</p>

## 5. ⚙Systems thinking and engineering decisions
   
### 5.1 Code Structure

### 5.2 Compilation / Upload Instructions

<p align="right">
  <a href="#top">Back To Top</a>
</p>

## 6. 📝List of Components

<p align="right">
  <a href="#top">Back To Top</a>
</p>

## 7. 💎3D Model Files

### 7.1 STL Files

### 7.2 Modified Files

<p align="right">
  <a href="#top">Back To Top</a>
</p>


## 8. 🛠️Building Instructions

<p align="right">
  <a href="#top">Back To Top</a>
</p>
