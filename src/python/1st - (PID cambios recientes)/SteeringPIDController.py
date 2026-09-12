#SteeringPIDController.py

from PIDController import PIDController
import Config

class SteeringPIDController(PIDController):
    
    mapeo_angular = 1
    KP_SERVO = 0.2
    KI_SERVO = 0.1
    KD_SERVO = 0.8
    FACTOR_INFLUENCIA_LATERAL = 1 #Factor para la influencia de los sensores laterales en un rango de 0 a 1
    
    def __init__(self):
        super().__init__(kp=SteeringPIDController.KP_SERVO, ki=SteeringPIDController.KI_SERVO, kd=SteeringPIDController.KD_SERVO)
    
    
    def compute(self, distancias):
        distancia_izq = min(distancias[0], Config.MAX_DISTANCIA_MURO)
        distancia_der = min( distancias[4], Config.MAX_DISTANCIA_MURO)
        diff_angular = ((SteeringPIDController.FACTOR_INFLUENCIA_LATERAL * distancia_izq + (1 - SteeringPIDController.FACTOR_INFLUENCIA_LATERAL) * distancias[1])
                        - (SteeringPIDController.FACTOR_INFLUENCIA_LATERAL * distancia_der + (1 - SteeringPIDController.FACTOR_INFLUENCIA_LATERAL) * distancias[3])) * self.mapeo_angular
        return max(Config.SERVO_RIGHT_MAX_DEG, min(Config.SERVO_CENTER_DEG - super().compute( 0, diff_angular), Config.SERVO_LEFT_MAX_DEG))