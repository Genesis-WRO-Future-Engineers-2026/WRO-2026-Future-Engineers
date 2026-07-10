#Carro.py
from Actuator import Actuator
from SteeringController import SteeringController
from SensorReader import SensorReader

class Carro():
    def __init__(self):
        self.actuadores = Actuator()
        self.volante = SteeringController()
        self.sensores = SensorReader()
        self.__x_coordinate = -1
        self.__y_coordinate = -1
        
        
    def begin(self):
        self.actuadores.begin()
        self.volante.begin()
        self.sensores.begin()
        
    def get_x_coordinate(self):
        return self.__x_coordinate
    
    def set_x_coordinate(self, x):
        self.__x_coordinate = x
        
    def get_y_coordinate(self):
        return self.__y_coordinate
    
    def set_y_coordinate(self, y):
        self.__y_coordinate = y