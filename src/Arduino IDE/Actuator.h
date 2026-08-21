/*
 * Actuator.h
 *
 * Control PWM para el servo de dirección y el puente H TB6612FNG.
 * Optimizado para ESP32-S2 Mini.
 */

#ifndef ACTUATOR_H
#define ACTUATOR_H

#include <Arduino.h>

// En lugar de #include <Servo.h>, usamos la librería nativa para ESP32
#include <ESP32Servo.h> 

#include "Config.h"

class Actuator {
   private:
    Servo _steeringServo; // El objeto se sigue llamando igual, la librería interna cambia
    uint8_t _currentSpeed; 

   public:
    Actuator();

    // Inicializa el servo y los pines/PWM del puente H
    void begin();

    // Establece el ángulo de dirección en grados
    void setSteering(float angle_degrees);

    // Controla la velocidad del motor puente H (Ciclo de trabajo de 0 a 255)
    void setSpeed(uint8_t speed_pwm);

    // Detiene por completo el motor (Modo standby en TB6612FNG)
    void stop();
};

#endif  // ACTUATOR_H
