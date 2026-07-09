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

## VL53L0X Distance Sensor

For this project, we selected the **VL53L0X** sensor due to three key advantages:

* **Ultra-compact size:** Its small footprint allows for easy integration into tight spaces without compromising the prototype's design.
* **Easy integration:** It offers excellent compatibility and ready-to-use libraries, drastically simplifying programming.
* **High speed:** It is capable of performing laser-based distance measurements in record time, ensuring fast, accurate, real-time readings.
  <img width="461" height="500" alt="D_NQ_NP_864803-MLV96890987952_112025-O (1)" src="https://github.com/user-attachments/assets/4efda80d-3582-41ca-b3bc-08b254ad4229" />


### 3.3 Processing Units 

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
