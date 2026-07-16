# ¡Hola! Somos el equipo Génesis de Venezuela.
<img width="903" height="675" alt="2afa2ad2-66f1-48aa-bc96-628adb1001fa" src="https://github.com/user-attachments/assets/f253592e-f094-4885-bef9-549df2e346e6" />

# WRO - Future Engineers - Documentación del proyecto de robótica

## 👥Miembros del equipo
- **Johelis Acosta**
 *Rol*: Electrónica y mecánica
- **Miguel Mejías**
 *Rol*: Programador
- **Wilber Pacheco**
 *Rol*: Diseñador

## 🧑🏻‍🔧Entrenador
- **Oswal Melean**
  *Ingeniero mecánico*


Bienvenidos a nuestro repositorio. Somos un grupo estudiantil dedicado a la robótica y la innovación, y en este espacio documentamos nuestro proceso de diseño: arquitectura de hardware, desarrollo de código, selección de componentes y el historial de pruebas del robot.

<a name="top"></a>

## 🔍Tabla de contenido

<!-- toc -->

- [1. 📚Descripción general](#1-descripción-general)
  - [1.1 Sobre el proyecto](#11-sobre-el-proyecto)
  - [1.2 Imagenes robot](#12-imagenes-robot)
  - [1.3 Video demostrativo](#13-video-demostrativo)
- [2. 🔩Movilidad y diseño mecánico](#2-movilidad-y-diseño-mecánico)
  - [2.1 Sistema de tracción](#21-sistema-de-tracción)
  - [2.2 Dirección](#22-direccion)
  - [2.3 Diseño del chasis](#23-diseño-del-chasis)
-  [3. 🔋Arquitectura de potencia y sensores](#3-arquitectura-de-potencia-y-sensores)
   - [3.1 Fuente de alimentación](#31-fuente-de-alimentación)
   - [3.2 Sensores y cámara](#32-sensores-y-cámara)
   - [3.3 Unidades de procesamiento](#33-unidades-de-procesamiento)
   - [3.4 Diagrama eléctrico](#34-diagrama-eléctrico)
   - [3.5 Consumo de energía](#35-consumo-de-energía)
- [4. 📐Arquitectura de software y estrategia para obstáculos](#4-arquitectura-de-software-y-estrategia-para-sortear-obstáculos)
  - [4.1 Reto abierto](#41-reto-abierto)
  - [4.2 Reto de obstáculos](#42-reto-de-obstáculos)
  - [4.3 Estacionamiento en paralelo](#43-estacionamiento-en-paralelo)
- [5. ⚙Pensamiento sistémico y decisiones de ingeniería](#5-pensamiento-sistémico-y-decisiones-de-ingeniería)
  - [5.1 Estructura del código](#52-estructura-del-código)
- [6. 📝Lista de componentes](#6-lista-de-componentes)
- [7. 💎Archivos de modelos 3D](#7-archivos-de-modelos-3d)
  - [7.1 Archivos STL](#72-archivos-stl)
  - [7.2 Archivos modificados](#73-archivos-de-slicer)
- [8. 🛠️Instrucciones de montaje](#8-instrucciones-de-montaje)


  
    <!-- tocstop -->

## 1. 📚Descripción general

### 1.1 Sobre el proyecto

Este proyecto se centra en el diseño, la construcción y la programación de un vehículo autónomo capaz de superar con precisión y rapidez los retos y obstáculos de la competición «WRO Future Engineers».

Para el equipo Genesis, este reto representa la oportunidad perfecta para poner en práctica la teoría, combinando la pasión por la innovación tecnológica con la resolución creativa de problemas a través de un proceso sistemático de investigación, creación de prototipos e iteración constante.

La estructura de nuestro robot se basa en una arquitectura robusta inspirada en el hardware *zcar* (https://github.com/alexyu132/zcar). Hemos sometido este diseño a un exhaustivo proceso de reingeniería utilizando Fusion 360 y Blender para optimizar las dimensiones de los alojamientos de tornillos y tuercas, así como para personalizar las piezas y lograr un ajuste perfecto de nuestros componentes.

El núcleo del sistema está controlado por una Raspberry Pi 3 B+, que gestiona la lógica principal, con el apoyo de un módulo ESP32 S2 Mini para controlar los sensores y actuadores. Para lograr una navegación precisa y una evitación eficiente de obstáculos, el robot integra sensores de tiempo de vuelo (ToF) junto con un giroscopio para la estabilización y la orientación de la trayectoria.

Todo este proceso de desarrollo ha estado respaldado por una documentación detallada que no solo optimiza nuestro flujo de trabajo, sino que también demuestra nuestras habilidades técnicas y de colaboración, así como nuestro compromiso con el aprendizaje práctico.


### 1.2 Imagenes robot

### 1.3 Video demostrativo

[Parte 1: Vídeo del reto abierto]()

[Parte 2: Vídeo del reto de obstáculos]()



<p align="right">
  <a href="#top">Back To Top</a>
</p>

## 2. 🔩Movilidad y diseño mecánico

### 2.1 Sistema de tracción

### 2.2 Dirección

### 2.3 Diseño del chasis

<p align="right">
  <a href="#top">Back To Top</a>
</p>

## 3. 🔋Arquitectura de potencia y sensores

### 3.1 Fuente de alimentación

<table>
  <tr>
    <td align="center" width="300" >
    <img width="400" height="400" alt="baeria 7 4v" src="https://github.com/user-attachments/assets/86bdc3d4-b1c2-4ccb-b713-f20bda4fbcf7" />
    </td>
    <td>
      <h3>Específicacones:</h3>
      <ul>
          <li>Capacidad: 1000 mAh</li>
          <li>Tensión nominal: 7.4V 2S</li>
          <li>Corriente de descarga estándar:75C </li>
          <li>Peso: 84g</li>
      </ul>
    </td>
  </tr>
</table>


### 3.2 Sensores y cámara

#### Sensor de distancia VL53L0X

El VL53L0X es un sensor de distancia pequeño y muy utilizado que emplea la tecnología de tiempo de vuelo (ToF) para medir la distancia a un objeto mediante la emisión de un pulso de luz láser infrarroja invisible y el cálculo del tiempo que tarda en regresar.

Lo hemos elegido para este proyecto debido a tres ventajas clave:

-  **Tamaño ultracompacto**: su reducido tamaño permite integrarlo fácilmente en espacios reducidos sin comprometer el diseño del prototipo.
  
-  **Fácil integración**: ofrece una excelente compatibilidad y bibliotecas listas para usar, lo que simplifica enormemente la programación.
  
-  **Alta velocidad**: es capaz de realizar mediciones de distancia por láser en un tiempo récord, lo que garantiza lecturas rápidas, precisas y en tiempo real.

  <img width="800" height="800" alt="GY-53VL53L0XLaserToFFlightTimeRangeSensorfront_1" src="https://github.com/user-attachments/assets/66a3e217-320e-4afe-9cc8-b6d77926fc41" />


|**Dimensiones**|**Valor**|
|---------------|---------|
| Largo         | 25 mm   |
| Alto          | 1 mm    |
| Ancho         | 10,7 mm |
| Peso          | 0,8 g   |
  
#### Sensor de unidad de medición inercial (IMU MPU-6050)

El MPU-6050 es una unidad de medición inercial (IMU) muy utilizada que integra un giroscopio de 3 ejes y un acelerómetro de 3 ejes en un único chip. Utiliza esta combinación para medir con precisión la aceleración lineal y la velocidad angular, lo que permite determinar la orientación, la inclinación y el movimiento del prototipo en el espacio.

Ventajas clave del dispositivo:

- **Tamaño ultracompacto**: al integrar el acelerómetro y el giroscopio en una placa minúscula, maximiza la eficiencia del espacio dentro de nuestro circuito.
  
- **Fácil integración**: gracias a la comunicación mediante el protocolo I2C y a una amplia gama de bibliotecas disponibles, la configuración y la lectura de datos son extremadamente sencillas.
  
- **Alta velocidad**: cuenta con un procesador de movimiento digital (DMP) interno que ejecuta rápidamente algoritmos complejos, proporcionando datos estables en tiempo real sin sobrecargar el microcontrolador principal.

<img width="1200" height="1200" alt="modulo-mpu6050-acelerometro-giroscopio-i2c" src="https://github.com/user-attachments/assets/da02f10c-e98b-41c9-a799-f0f82457208e" />


|**Dimensiones**|**Valor**|
|---------------|---------|
| Largo         | 21.2 mm |
| Ancho         | 16.4 mm |
| Alto          | 3.3 mm  |
| Peso          | 2.1 g   |

#### Cámara de visión artificial (cámara web FHD de 1080p modificada)

Para equipar el vehículo con un sistema de visión artificial, integramos una cámara web de alta definición (FHD de 1080p). Sin embargo, dado que la unidad comercial original (incluidas su carcasa y su soporte) era demasiado grande y pesada (80 mm x 33 mm x 40 mm), llevamos a cabo una modificación del hardware eliminando toda la estructura plástica externa. Esto nos permitió extraer el módulo interno de la cámara, lo que dio como resultado una placa de circuito funcional que mide tan solo **25 mm x 28,5 mm**.

Ventajas clave del dispositivo modificado:

- **Tamaño ultracompacto (tras la modificación)**: al reducir drásticamente sus dimensiones a tan solo 25 mm x 28,5 mm, pudimos montarlo en la parte delantera del vehículo sin comprometer la aerodinámica ni el diseño del chasis.
  
- **Fácil integración y estabilidad**: A pesar de estar desmontado, conserva la conectividad USB nativa y la compatibilidad directa con algoritmos de visión por ordenador (como OpenCV), lo que simplifica la programación.
  
- **Alta velocidad y resolución**: Mantiene la captura en 1080p FHD, procesando imágenes nítidas en tiempo real, un factor crítico para la toma de decisiones mientras el vehículo está en movimiento.

#### Comparación de dimensiones (cámara web)


<div align="center">
  <i>Antes</i>
  <br>
 <img width="1024" height="1024" alt="productos34_25510" src="https://github.com/user-attachments/assets/64d0bc72-e8c2-4080-8f3f-c7b37652012b" />
</div> 


|          **Estado**          |**Largo** |**Ancho**|**Alto**|
|------------------------------|----------|---------|--------|
| Con carcasa (original)       | 80 mm    | 40 mm   | 33 mm  |




<div align="center">
 <i>Después</i>
 <img width="1702" height="1599" alt="1783617511143" src="https://github.com/user-attachments/assets/4e1c87a2-014d-4601-af65-98bbfaef934c" />
 <br>
</div>
  
 
|          **Estado**          |**Largo** |**Ancho**|**Alto**|
|------------------------------|----------|---------|--------|
| Sin carcasa (modificado)     | 25 mm    | 28,5 mm | 2 mm   |



### 3.3 Unidades de procesamiento 

Equipada con un procesador ARM Cortex-A53 de 64 bits y 1,4 GHz, la Raspberry Pi 3 B+ es nuestro controlador principal. Decidimos utilizar la Raspberry Pi 3 B+ por varias razones, entre ellas:

- **Compatibilidad**: hay muchos componentes (como las cámaras web USB estándar) que son fáciles de integrar con la Raspberry Pi 3 B+.
  
- **Potencia**: la Raspberry Pi 3 B+ ofrece un rendimiento eficiente y equilibrado; gracias a ello, el dispositivo gestiona con facilidad tareas exigentes, como el procesamiento de imágenes en tiempo real.
  
- **Portabilidad**: La Raspberry Pi 3 B+ destaca entre los controladores; con un peso de tan solo 45 g, es ligera, lo que la convierte en una opción práctica y fiable para su integración en el Eva 01.


<div align="center">
 <i>Raspberry Pi 3 B+</i>
 <img width="1200" height="1200" alt="raspberry-pi-3-b-plus" src="https://github.com/user-attachments/assets/fb22d270-ab59-46c8-af45-43ecbb1fe371" />
 <br>
</div>

|**Dimensión**|**Valor**|
|-------------|---------|
| Longitud    | 85 mm   |
| Altura      | 17 mm   |
| Anchura     | 56 mm   |
| Peso        | 45 g    |

Aunque la Raspberry Pi 3 B+ es capaz de procesar imágenes en tiempo real, nos dimos cuenta de que necesitaba algo de ayuda para evitar que se sobrecargara de información; por ello, decidimos incorporar un ESP32-S2 Mini para controlar los sensores y sus actuadores con el fin de alcanzar el nivel de procesamiento necesario. Asimismo, aprovechamos la conectividad Wi-Fi integrada de este microcontrolador para transmitir y visualizar en tiempo real (únicamente  durante las prácticas) las lecturas de los sensores a traves de una app realizada en Firebase.


<div align="center">
 <i>ESP32-S2 Mini</i>
 <img width="447" height="447" alt="1783780004798" src="https://github.com/user-attachments/assets/cfa1950d-ffea-486f-afad-d26f989b30ea" />
 <br>
</div>

|**Dimensión**|**Valor**|
|-------------|---------|
| Longitud    | 34.3 mm |
| Altura      | 25.4 mm |
| Anchura     | 25.4 mm |
| Peso        | 5.3 g   |



### 3.4 Diagrama eléctrico 

**Diagrama General:**


### 3.5 Consumo de energía

<p align="right">
  <a href="#top">Back To Top</a>
</p>

## 4. 📐Arquitectura de software y estrategia para obstáculos

### 4.1 Reto abierto

### 4.2 Reto de osbtáculos

### 4.3 Estacionamiento en paralelo

<p align="right">
  <a href="#top">Back To Top</a>
</p>

## 5. ⚙Pensamiento sistémico y decisiones de ingeniería
   
### 5.1 Estructura del código


<p align="right">
  <a href="#top">Back To Top</a>
</p>

## 6. 📝Lista de componentes

<p align="right">
  <a href="#top">Back To Top</a>
</p>

## 7. 💎Archivos de modelos 3D

### 7.1 Archivos STL

### 7.2 Aarchivos modificados

<p align="right">
  <a href="#top">Back To Top</a>
</p>


## 8. 🛠️Instrucciones de montaje

<p align="right">
  <a href="#top">Back To Top</a>
</p>
