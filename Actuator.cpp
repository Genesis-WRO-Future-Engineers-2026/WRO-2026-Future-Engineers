#include "Actuator.h"
#include "Logger.h"

Actuator::Actuator() : _currentSpeed(0) {}

void Actuator::begin() {
#if ENABLE_PWM
    // 1. Asignación de Timers e inicialización del Servo de Dirección
    // Esto asegura que use los mismos recursos de hardware que funcionaron en el sweep
    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    
    _steeringServo.setPeriodHertz(50); // Frecuencia estándar para servos (50Hz)
    
    // IMPORTANTE: Enlazamos el pin asignándole su rango de pulso mínimo y máximo (1000us a 2000us)
    // Esto permite que el método map(grados, 0, 180, 1000, 2000) sea totalmente preciso
    _steeringServo.attach(SERVO_PIN, 1000, 2000); 
    
    // Colocamos el servo en la posición central calibrada en grados (ej: 45°) nada más arrancar
    // Convertimos esos grados iniciales a microsegundos para mantener la coherencia del driver
    int pulse_center_us = map(SERVO_CENTER_DEG, 0, 180, 1000, 2000);
    _steeringServo.writeMicroseconds(pulse_center_us);

    // 2. Inicialización del Puente H del Motor (TB6612FNG)
    pinMode(MOTOR_IN1_PIN, OUTPUT);
    pinMode(MOTOR_IN2_PIN, OUTPUT);
    
    // Configuramos el motor en el Canal 4 (PWM a 20kHz, 8 bits) para no interferir con el servo
    ledcSetup(4, 20000, 8); 
    ledcAttachPin(MOTOR_PWMA_PIN, 4); 

    // Estado inicial seguro: Coche completamente detenido
    stop();

    Logger::println("Actuadores Inicializados con Calibración en Grados:");
    Logger::print("  Servo Pin: "); Logger::print(SERVO_PIN);
    Logger::print(" | Centro: "); Logger::print(SERVO_CENTER_DEG); Logger::println("°");
    Logger::print("  Motor Pines: IN1="); Logger::print(MOTOR_IN1_PIN);
    Logger::print(", IN2="); Logger::print(MOTOR_IN2_PIN);
    Logger::print(", PWM(Ch4)="); Logger::println(MOTOR_PWMA_PIN);
#else
    Logger::println("DEBUG MODE: Actuadores desactivados (Sin salidas físicas PWM)");
#endif
}

void Actuator::setSteering(float angle_degrees) {
    // 1. Traducir el ángulo teórico del software (Pure Pursuit) a grados reales del servo.
    // El software calcula: Negativo = Izquierda, Positivo = Derecha.
    // Tu servo físico hace: Grados altos (90) = Izquierda, Grados bajos (0) = Derecha.
    int target_servo_deg = map((int)(angle_degrees * 10),
                               (int)(-MAX_STEERING_ANGLE * 10),
                               (int)(MAX_STEERING_ANGLE * 10),
                               SERVO_LEFT_MAX_DEG * 10,   // Izquierda teórica -> Grados altos (ej: 900)
                               SERVO_RIGHT_MAX_DEG * 10); // Derecha teórica   -> Grados bajos (ej: 0)

    // Dividimos entre 10 para regresar a la escala normal de grados enteros
    int final_deg = target_servo_deg / 10;

    // 2. Filtro de seguridad (Clamp) para que el servo nunca intente ir más allá de tus límites configurados
    // Aseguramos el rango numérico estándar entre el mínimo y máximo en grados
    int min_allowed = (SERVO_RIGHT_MAX_DEG < SERVO_LEFT_MAX_DEG) ? SERVO_RIGHT_MAX_DEG : SERVO_LEFT_MAX_DEG;
    int max_allowed = (SERVO_RIGHT_MAX_DEG > SERVO_LEFT_MAX_DEG) ? SERVO_RIGHT_MAX_DEG : SERVO_LEFT_MAX_DEG;
    
    if (final_deg < min_allowed) final_deg = min_allowed;
    if (final_deg > max_allowed) final_deg = max_allowed;

#if ENABLE_PWM
    // 3. Convertir los grados finales a microsegundos precisos (0° -> 1000us, 180° -> 2000us)
    // Esto replica exactamente lo que hace el método .write() por dentro, garantizando compatibilidad
    int pulse_us = map(final_deg, 0, 180, 1000, 2000);
    
    _steeringServo.writeMicroseconds(pulse_us);
#endif

    Logger::printActuator("Servo Grados Reales", final_deg);
}

void Actuator::setSpeed(uint8_t speed_pwm) {
    _currentSpeed = speed_pwm;
#if ENABLE_PWM
    if (_currentSpeed == 0) {
        stop();
        return;
    }
    digitalWrite(MOTOR_IN1_PIN, HIGH);
    digitalWrite(MOTOR_IN2_PIN, LOW);
    ledcWrite(4, _currentSpeed); // Canal 4
#endif
}

void Actuator::stop() {
    _currentSpeed = 0;
#if ENABLE_PWM
    digitalWrite(MOTOR_IN1_PIN, LOW);
    digitalWrite(MOTOR_IN2_PIN, LOW);
    ledcWrite(4, 0); // Canal 4
#endif
}
