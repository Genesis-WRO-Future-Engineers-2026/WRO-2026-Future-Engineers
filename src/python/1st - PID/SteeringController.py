# steering_controller.py
import math
import Config # <--- Importamos la configuración centralizada

class SteeringController:
    def __init__(self):
        # Pure Pursuit no tiene estado interno (stateless); el constructor está vacío.
        pass

    def begin(self):
        # Incluido por simetría con los otros módulos del sistema de Arduino
        pass

    def calculate(self, gap, sensor_data):
        """
        Calcula el ángulo de dirección (grados) usando Pure Pursuit.
        gap: Instancia de GapResult (contiene target_angle)
        sensor_data: Lista de objetos SensorData del SensorReader
        """
        alpha_deg = gap.target_angle

        # Restamos el offset a la distancia del sensor frontal para obtener Ld.
        # Equivalente al operador ternario ( ? : ) de C++
        front_sensor = sensor_data[Config.FRONT_SENSOR_INDEX]
        
        if front_sensor.valid:
            Ld_mm = front_sensor.distance - Config.LOOKAHEAD_OFFSET_MM
        else:
            Ld_mm = 1000.0  # Fallback de seguridad si el sensor frontal no es válido

        # Evitar división por cero o valores geométricos extremos/absurdos
        if Ld_mm < 50.0:
            Ld_mm = 50.0

        alpha_rad = alpha_deg * Config.DEG_TO_RAD

        # Fórmula matemática de Pure Pursuit: delta = atan2(2 * L * sin(alpha), Ld)
        steering_rad = math.atan2(
            2.0 * Config.WHEELBASE_MM * math.sin(alpha_rad), 
            Ld_mm
        )

        steering_deg = steering_rad * Config.RAD_TO_DEG

        # Clamp al límite mecánico del servo usando max() y min() (Equivalente al constrain)
       # 1. Aplicamos el límite (clamp) al desvío relativo usando tus constantes de Config
        steering_deg = max(-Config.MAX_STEERING_ANGLE, min(Config.MAX_STEERING_ANGLE, steering_deg))

        # 2. Convertimos el desvío relativo en un ángulo absoluto sumando tu centro (60)
        angulo_final_servo = Config.SERVO_CENTER_DEG + steering_deg

        # 3. Nos aseguramos de no sobrepasar los límites físicos reales configurados para tu servo
        # (Usa SERVO_MIN_DEG y SERVO_MAX_DEG de tu Config.py para proteger el mecanismo)
        angulo_final_servo = max(Config.SERVO_RIGHT_MAX_DEG, min(Config.SERVO_LEFT_MAX_DEG, angulo_final_servo))

        return angulo_final_servo