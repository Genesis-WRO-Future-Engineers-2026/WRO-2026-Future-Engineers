#SteeringPIDController.py

from PIDController import PIDController
import Config
from Carro import Carro

class SteeringPIDController(PIDController):
    
    mapeo_angular = 1
    KP_SERVO = 0.2
    KI_SERVO = 0
    KD_SERVO = 0
    
    def __init__(self):
        super().__init__(self, KP_SERVO, KI_SERVO, KD_SERVO)
    
    
    def compute(self, c):
        distancias = c.sensores.get_filtered_data()
        diff_angular = (distancias[0] - distancias[4]) * self.mapeo_angular
        return 60 - super().compute( 0, diff_angular)
    
    def correccion_servo(self, c):
        c.actuadores.set_angle_dg(self.compute(c))