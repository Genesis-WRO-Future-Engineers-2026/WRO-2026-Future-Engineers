/*
 * main.ino
 *
 * Control de Follow-the-Gap + Pure Pursuit con 5 sensores VL53L0X (XSHUT)
 * Adaptado para ESP32-S2 Mini y Driver de tracción TB6612FNG.
 * * El carro correrá de forma autónoma durante exactamente 1 minuto y luego se detendrá.
 */

#include "Actuator.h"
#include "Config.h"
#include "GapFinder.h"
#include "Logger.h"
#include "SensorReader.h"
#include "SteeringController.h"

// ============================================================================
// Variables Globales
// ============================================================================
SensorReader sensorReader;
GapFinder gapFinder;
SteeringController steeringController;
Actuator actuator;

// Variables para el control de tiempo de la carrera
unsigned long tiempoInicioCarrera = 0;
bool carreraTerminada = false;
const unsigned long DURACION_CARRERA_MS = 60000; // 1 minuto = 60,000 ms

// ============================================================================
// setup
// ============================================================================
void setup() {
    // Inicializar el puerto de diagnóstico serial si el modo actual lo permite
    #if ENABLE_SERIAL
    Serial.begin(115200);
    while (!Serial) { delay(10); } // Esperar conexión en el ESP32-S2 Mini
    #endif

    Logger::println("=== INICIANDO ROBOT (ESP32-S2 Mini) ===");

    // 1. Inicializar actuadores (Servo en pin 18 y TB6612FNG)
    actuator.begin();

    // 2. Inicializar los 5 sensores secuencialmente mediante XSHUT
    if (!sensorReader.begin()) {
        Logger::println("¡ERROR CRÍTICO! Falló la inicialización de sensores. Sistema congelado.");
        actuator.stop();
        while (1) { delay(100); }
    }

    steeringController.begin();

    Logger::println("=== Setup completado con éxito ===");
    Logger::println("Alineando dirección y esperando inicio de carrera...");
    
    actuator.setSteering(0.0);
    actuator.stop();
    
    delay(1000); // Pequeña pausa de seguridad antes de arrancar

    // Guardamos el tiempo exacto en milisegundos en el que arranca la carrera
    tiempoInicioCarrera = millis();
    Logger::println("!!! ¡CARRERA INICIADA! Cronómetro en marcha (1 min) !!!");
}

// ============================================================================
// loop
// ============================================================================
void loop() {
    // Si el minuto ya pasó, forzamos que el coche se quede estático y no haga nada más
    if (carreraTerminada) {
        actuator.setSteering(0.0); // Centrar ruedas
        actuator.stop();           // Apagar motor
        delay(500);
        return; 
    }

    // Comprobar si el tiempo actual ha superado el minuto desde que inició la carrera
    if (millis() - tiempoInicioCarrera >= DURACION_CARRERA_MS) {
        carreraTerminada = true;
        Logger::println("\n==============================================");
        Logger::println("¡TIEMPO AGOTADO! 1 minuto completado. Deteniendo robot.");
        Logger::println("==============================================");
        return;
    }

    // =========================================================================
    // Ejecución del algoritmo de control autónomo (Solo si estamos dentro del minuto)
    // =========================================================================
    unsigned long loopStartUs = micros();

    // Fase 1: Leer los 5 sensores ToF mediante direccionamiento I2C directo
    unsigned long sensStartUs = micros();
    sensorReader.readAll();
    unsigned long sensElapsedUs = micros() - sensStartUs;

    const SensorData* sensorData = sensorReader.getAllData();

    // Fase 2: Comprobar parada de emergencia por proximidad crítica al frente
    // Usamos el nuevo FRONT_SENSOR_INDEX (índice 2) definido en tu Config.h
    bool parada_emergencia = sensorData[FRONT_SENSOR_INDEX].valid &&
                             (sensorData[FRONT_SENSOR_INDEX].distance < CRITICAL_STOP_THRESHOLD);

    // Fase 3: Procesar algoritmo Follow-the-Gap
    GapResult gap = gapFinder.find(sensorData);

    #if ENABLE_SERIAL
    float distancia_frontal = sensorData[FRONT_SENSOR_INDEX].valid
                           ? sensorData[FRONT_SENSOR_INDEX].distance
                           : 0.0f;
    Logger::printGapResult(gap.target_angle, distancia_frontal);
    #endif

    // Fase 4: Calcular ángulo de dirección óptimo usando Pure Pursuit
    float angulo_giro_calculado = steeringController.calculate(gap, sensorData);

    #if ENABLE_SERIAL
    Logger::printSteering(angulo_giro_calculado);
    #endif

    // Fase 5: Enviar comandos a los Actuadores
    if (parada_emergencia) {
        // Si hay un obstáculo insalvable al frente, frena por seguridad antes del minuto
        Logger::println("¡ALERTA! Parada de emergencia por proximidad.");
        actuator.setSteering(0.0);
        actuator.stop();
    } else {
        // Conducción normal: Ajusta el servo e inyecta la velocidad PWM de crucero
        actuator.setSteering(angulo_giro_calculado);
        actuator.setSpeed(CRUISE_SPEED); // Usa el nuevo valor discreto 0-255 de tu Config.h
    }

    // Telemetría de tiempos del ciclo
    #if ENABLE_SERIAL
    unsigned long loopEndUs = micros();
    unsigned long loopElapsedUs = loopEndUs - loopStartUs;
    Logger::printLoopTiming(loopElapsedUs, sensElapsedUs);
    Logger::println("");
    #endif
}
