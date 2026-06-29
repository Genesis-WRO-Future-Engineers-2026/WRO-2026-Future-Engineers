
## 1. ⭐️Design process

### 1.2 Chassis Optimization

The first modification during the development of the "zcar" chassis involved redesigning the model in Fusion 360 to adapt the mounting points for components more readily available on the local market. To achieve this, the holes in the original .stl file were modified to replace M3 screws and nuts with M4-sized ones.

However, initial printing tests revealed that increasing the hole diameter drastically reduced wall thickness in the steering and drive axle areas, thereby compromising structural strength against mechanical stress.

To resolve this issue without sacrificing the advantage of using locally available components, a hybrid design was adopted: M4 mounts were retained for the vehicle's main structure, while M3 components were kept exclusively for the steering and drive axle to preserve their geometric integrity. Additionally, the thickness of the drive axle was increased, and the rear axle support was reinforced.

The part limiting the steering mechanism's travel was modified. This improvement proved crucial, as it allowed for an increase in the robot's maximum turning angle, significantly optimizing its performance and maneuverability on the track.

A key change in this process was replacing the drive axle included in the original "zcar" .stl file with a metal one.

<img width="1273" height="1278" alt="5048967179142892673" src="https://github.com/user-attachments/assets/d3d72d92-35cd-4e85-ae31-f3a42bcf580a" />

### 1.3 Desarrollo de la Placa de Control (Sensores y Actuadores)

To integrate the sensors, the gyroscope, and the actuators (a servo motor and a DC motor), a custom circuit board was developed. The initial step involved implementing the circuit on a breadboard to validate the combined operation of all components.

Following a testing phase, it was discovered that the gyroscope would not function simultaneously with the sensors. Initially, the malfunction was attributed to the parallel connection of the power and communication lines (GND, VIN, SDA, and SCL)—while keeping the sensors' X-SHUT pins independently connected to the ESP32-S2 Mini's GPIO pins. However, the problem persisted even after testing the gyroscope individually with the microcontroller. Replacing the physical component and performing extensive code debugging failed to yield positive results.

Faced with this limitation, the decision was made to connect the gyroscope directly to a Raspberry Pi 3 Model B+. Finally, the validated portion of the circuit was transferred and soldered onto a perfboard; given the successful performance achieved, this solution was adopted for the project's final development.

Breadboard circuit
<img width="1080" height="1254" alt="5048967179142892676" src="https://github.com/user-attachments/assets/0bb81f95-cd65-4173-8f5b-3d8904faf203" />

Perfboard circuit
<img width="2560" height="2560" alt="5048967179142892677" src="https://github.com/user-attachments/assets/9f4607ee-f12c-4abe-8d11-6de3b640387c" />


