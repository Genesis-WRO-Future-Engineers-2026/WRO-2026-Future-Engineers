
## 1. ⭐️Proceso de diseño

### 1.2 Optimización del chasis

La primera modificación durante el desarrollo del chasis del «zcar» consistió en rediseñar el modelo en Fusion 360 para adaptar los puntos de montaje a componentes más fáciles de conseguir en el mercado local. Para ello, se modificaron los orificios del archivo .stl original con el fin de sustituir los tornillos y tuercas M3 por otros de tamaño M4.

Sin embargo, las pruebas iniciales de impresión revelaron que al aumentar el diámetro de los orificios se reducía drásticamente el grosor de las paredes en las zonas del eje de dirección y del eje motriz, lo que comprometía la resistencia estructural frente a las tensiones mecánicas.

Para resolver este problema sin sacrificar la ventaja de utilizar componentes disponibles localmente, se adoptó un diseño híbrido: se mantuvieron los soportes M4 para la estructura principal del vehículo, mientras que los componentes M3 se reservaron exclusivamente para el eje de dirección y el eje motriz con el fin de preservar su integridad geométrica. Además, se aumentó el espesor del eje motriz y se reforzó el soporte del eje trasero.

Se modificó la pieza que limitaba el recorrido del mecanismo de dirección. Esta mejora resultó crucial, ya que permitió aumentar el ángulo de giro máximo del robot, optimizando significativamente su rendimiento y maniobrabilidad en la pista.

Un cambio clave en este proceso fue la sustitución del eje motriz incluido en el archivo .stl original de «zcar» por uno metálico.


<img width="400" alt="5048967179142892673" src="https://github.com/user-attachments/assets/d3d72d92-35cd-4e85-ae31-f3a42bcf580a" />

### 1.3 Desarrollo de la Placa de Control (Sensores y Actuadores)

Para integrar los sensores, el giroscopio y los actuadores (un servomotor y un motor de corriente continua), se desarrolló una placa de circuito personalizada. El primer paso consistió en montar el circuito en una placa de pruebas para validar el funcionamiento conjunto de todos los componentes.

Tras una fase de pruebas, se descubrió que el giroscopio no funcionaba simultáneamente con los sensores. En un principio, el fallo se atribuyó a la conexión en paralelo de las líneas de alimentación y comunicación (GND, VIN, SDA y SCL), mientras que los pines X-SHUT de los sensores se mantenían conectados de forma independiente a los pines GPIO del ESP32-S2 Mini. Sin embargo, el problema persistió incluso tras probar el giroscopio por separado con el microcontrolador. Ni la sustitución del componente físico ni la realización de una exhaustiva depuración del código dieron resultados positivos.

Ante esta limitación, se tomó la decisión de conectar el giroscopio directamente a una Raspberry Pi 3 Modelo B+. Finalmente, la parte validada del circuito se transfirió y se soldó a una placa de pruebas; dado el buen funcionamiento obtenido, esta solución se adoptó para el desarrollo final del proyecto.


Circuito en ProtoBoard

<img width="400" alt="5048967179142892676" src="https://github.com/user-attachments/assets/0bb81f95-cd65-4173-8f5b-3d8904faf203" />

Circuito en Perfboard
<img width="400" alt="5048967179142892677" src="https://github.com/user-attachments/assets/9f4607ee-f12c-4abe-8d11-6de3b640387c" />


