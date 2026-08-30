# 🏎️ Eva 01 - Vehículo Autónomo (WRO Future Engineers)

Esta carpeta contiene el código fuente en MicroPython/Python diseñado para el vehículo autónomo **Eva 01**, configurado para abordar los desafíos de la competencia *World Robot Olympiad (WRO) Future Engineers*.

El sistema orquesta la gestión secuencial y lectura de sensores de distancia por tiempo de vuelo (ToF VL53L0X), el filtrado digital de datos, el control de tracción y dirección del chasis, y la transmisión de telemetría IoT en tiempo real.

---

## 📌 Inspiración y Créditos

Este proyecto toma como base conceptual, arquitectónica y de referencia el trabajo del repositorio **ichis-lab**:
* **Repositorio de Referencia:** (https://github.com/ichis-lab/minicar-battle) Módulo *seven*

* **Elementos Clave Adoptados y Adaptados:**

  - Direccionamiento I2C Dinámico (VL53L0X): Encendido secuencial utilizando pines `XSHUT` para reasignar la dirección I2C por defecto (`0x29`) de múltiples sensores al arrancar.

  - Control de Sensores (`set_address` y `set_offset`): Uso de una librería basada en Adafruit adaptada para MicroPython, que permite reasignar direcciones I2C al vuelo (registro `0x8A`) y calibrar el desfase físico en milímetros directamente en el registro `0x28`.
 
  - Arquitectura Modular del Vehículo: Organización del código dividida en clases independientes para la gestión de sensores, actuadores y estado general del vehículo.
  
  - Gestión de Modos de Ejecución: Uso de `Config.py` para alternar entre pruebas de banco, depuración y modo competencia.



