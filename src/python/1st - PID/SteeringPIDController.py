#SteeringPIDController.py

from PIDController import PIDController
import Config

class SteeringPIDController(PIDController):
    
    mapeo_angular = 1
    KP_SERVO = 0.4
    KI_SERVO = 0.3
    KD_SERVO = 3
    FACTOR_INFLUENCIA_LATERAL = 0.7 #Factor para la influencia de los sensores laterales en un rango de 0 a 1
    
    def __init__(self):
        super().__init__(kp=SteeringPIDController.KP_SERVO, ki=SteeringPIDController.KI_SERVO, kd=SteeringPIDController.KD_SERVO)
    
    
    def compute(self, distancias):
        diff_angular = ((SteeringPIDController.FACTOR_INFLUENCIA_LATERAL * distancias[0] + (1 - SteeringPIDController.FACTOR_INFLUENCIA_LATERAL) * distancias[1])
                        - (SteeringPIDController.FACTOR_INFLUENCIA_LATERAL * distancias[3] + (1 - SteeringPIDController.FACTOR_INFLUENCIA_LATERAL) * distancias[4])) * self.mapeo_angular
        return max(0, min(60 - super().compute( 0, diff_angular), 120))