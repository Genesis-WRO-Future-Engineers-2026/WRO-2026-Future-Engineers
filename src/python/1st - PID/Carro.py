#Carro.py
from Actuator import Actuator
from SensorReader import SensorReader
from Pista import Pista
import Config
from Logger import Logger
import time #Chequear envio del tiempo
from SteeringPIDController import SteeringPIDController

class Carro():
    def __init__(self):
        self.actuadores = Actuator()
        self.sensores = SensorReader()
        self.controlador_volante = SteeringPIDController()
        self.__x_coordinate = -1
        self.__y_coordinate = -1
        if (Config.ENABLE_SERIAL):
            self.logger = Logger()
            self.logger.begin()
        
        
    def begin(self):
        self.actuadores.begin()
        self.sensores.begin()
        
    def get_x_coordinate(self):
        return self.__x_coordinate
    
    def set_x_coordinate(self, x):
        self.__x_coordinate = x
        
    def get_y_coordinate(self):
        return self.__y_coordinate
    
    def set_y_coordinate(self, y):
        self.__y_coordinate = y
        
    def recta_PID(self):
        
        self.sensores.read_all()
        distancias = [self.sensores.get_all_data()[sensor].distance for sensor in range(Config.NUM_SENSORS)]
        angulo_objetivo = self.controlador_volante.compute(distancias)
        self.actuadores.set_angle_dg(angulo_objetivo)
        if(Config.ENABLE_SERIAL):
            self.logger.send_data(emergency=False, pwm=200,sensors=distancias, steering=0, x=0, y=0, sentido=0)
        
        
        
    def resolver_pista(self, pista):
        while not pista.esta_resuelta():
            self.sensores.read_all()
            datos_sensores = self.sensores.get_filtered_data()
            
            self.recta_PID()
            
            dist_derecha = datos_sensores[4]
            dist_izquierda = datos_sensores[0]
        
            dist_frontal = datos_sensores[Config.FRONT_SENSOR_INDEX] 
            
            parada = dist_frontal < Config.CRITICAL_STOP_THRESHOLD        
        
            
            if parada:

                self.actuadores.stop()
                pista.set_sentido(pista.SENTIDO_HORARIO if dist_derecha > dist_izquierda else pista.SENTIDO_ANTIHORARIO)
                pista.resuelta()
                self.set_y_coordinate(dist_izquierda)

            else:

                self.actuadores.set_speed(Config.CRUISE_SPEED)
      
            self.set_x_coordinate(dist_frontal)
        
        
            
            # ============================================================================
            # MODO 2: TELEMETRÍA EN LA NUBE (Envío a Firebase)
            # ============================================================================
            
            if(Config.ENABLE_SERIAL):
                self.logger.send_data(emergency=parada, pwm=Config.CRUISE_SPEED,sensors=[datos_sensores[sensor] for sensor in range(Config.NUM_SENSORS)], steering=0, x=self.get_x_coordinate(), y=self.get_y_coordinate(), sentido=pista.get_sentido())
            
            # Pequeña pausa de estabilidad (50ms)
            time.sleep_ms(50)