/*
 * Config.h
 *
 * Centralized configuration values.
 * All constants are named here to avoid magic numbers.
 */

#ifndef CONFIG_H
#define CONFIG_H

// ============================================================================
// Run mode
// ============================================================================
// Mode definitions:
//   0: MODE_DEBUG      - debug only (no PWM, serial enabled)
//   1: MODE_PRODUCTION - race run (PWM enabled, serial disabled)
//   2: MODE_DEBUG_RUN  - debug run (PWM enabled, serial enabled)
#define MODE_DEBUG 0
#define MODE_PRODUCTION 1
#define MODE_DEBUG_RUN 2

#define RUN_MODE MODE_PRODUCTION // select run mode here

// Feature toggles derived from RUN_MODE
#define ENABLE_SERIAL (RUN_MODE == MODE_DEBUG || RUN_MODE == MODE_DEBUG_RUN)
#define ENABLE_PWM (RUN_MODE == MODE_PRODUCTION || RUN_MODE == MODE_DEBUG_RUN)

// ============================================================================
// Hardware & Sensores ToF VL53L0X (Secuencia XSHUT)
// ============================================================================
// Ya no usamos el multiplexor TCA9548A_ADDR ni SENSOR_CHANNELS.
// Pines físicos conectados a los XSHUT de cada sensor en el ESP32-S2 Mini
const uint8_t XSHUT_PINS[5] = {1, 2, 3, 4, 5}; 

// Direcciones I2C dinámicas asignadas consecutivamente durante el inicio
const uint8_t SENSOR_ADDRESSES[5] = {0x30, 0x32, 0x34, 0x36, 0x38};

// Nueva distribución de 5 sensores
const uint8_t NUM_SENSORS = 5;

// Ángulos físicos de orientación: [Izquierda 90°, Izquierda 45°, Centro 0°, Derecha 45°, Derecha 90°]
const float SENSOR_ANGLES[NUM_SENSORS] = {-90.0f, -45.0f, 0.0f, 45.0f, 90.0f};

// El sensor central (0.0 grados) ahora pasa a estar en el índice 2
const uint8_t FRONT_SENSOR_INDEX = 2;  

// ============================================================================
// Sensor Thresholds & Parameters
// ============================================================================
const uint16_t RELIABLE_RANGE = 2300;       // Max trusted distance (mm)
const uint16_t MIN_VALID_DISTANCE = 40;     // Min trusted distance (mm)
const uint16_t CRITICAL_STOP_THRESHOLD = 300; // Front emergency-stop threshold (mm)

// Auto-stop timeout (debug aid).
// 0 disables it; otherwise the car stops after this many seconds.
const unsigned long AUTO_STOP_SECONDS = 20;

// ============================================================================
// Actuadores: Servo de Dirección (Calibración en Grados)
// ============================================================================
const uint8_t SERVO_PIN = 40;        // Pin de señal del servo (probado en sweep)

// --- AJUSTA ESTOS VALORES EN GRADOS SEGÚN TU COCHE ---
const int SERVO_CENTER_DEG = 60;     // Ángulo central para que el carro vaya recto
const int SERVO_RIGHT_MAX_DEG = 0;   // Ángulo físico máximo a la DERECHA
const int SERVO_LEFT_MAX_DEG = 120;   // Ángulo físico máximo a la IZQUIERDA (puedes probar 80, 90, etc.)

const float MAX_STEERING_ANGLE = 30.0f; // Máximo ángulo de giro que el software (Pure Pursuit) puede calcular

// ============================================================================
// Actuadores: Motor de Tracción (TB6612FNG + Periférico LEDC)
// ============================================================================
const uint8_t MOTOR_IN1_PIN = 34;
const uint8_t MOTOR_IN2_PIN = 21;
const uint8_t MOTOR_PWMA_PIN = 17;

// Configuración de señal PWM por hardware nativo para ESP32-S2
const uint32_t PWM_FREQ = 20000;     // Frecuencia de 20kHz (Inaudible, evita silbidos del motor)
const uint8_t PWM_RESOLUTION = 8;    // Resolución de 8 bits (Valores de ciclo de trabajo de 0 a 255)

// Velocidad base de crucero para el circuito (Mapeado de 0 a 255)
const uint8_t CRUISE_SPEED = 150;    

// ============================================================================
// Pure Pursuit Parameters
// ============================================================================
const float WHEELBASE_MM = 92.0f;        // L: distance from front to rear axle
const float LOOKAHEAD_OFFSET_MM = 400.0f; // subtracted from front distance to get Ld

// ============================================================================
// Gap Finder Parameters
// ============================================================================
const float FARTHEST_HYSTERESIS = 150.0f; // candidate must be this much farther to switch (mm)

// ============================================================================
// Math constants & Trigonometry
// ============================================================================
#ifndef DEG_TO_RAD
#define DEG_TO_RAD 0.01745329251f
#endif

#ifndef RAD_TO_DEG
#define RAD_TO_DEG 57.295779513f
#endif

// Factor trigonométrico fijo sin(45°) usado en GapFinder.cpp para la interpolación de áreas
const float SIN_45_DEG = 0.7071067811f; 

#endif  // CONFIG_H
