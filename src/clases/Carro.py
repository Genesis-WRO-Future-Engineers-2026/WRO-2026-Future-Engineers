#Carro.py
from Actuator import Actuator
from SteeringController import SteeringController
from SensorReader import SensorReader
from Mpu6050 import accel  # <--- Importante para la IMU
from Navegacion import NavegadorPista
from machine import I2C, Pin
import Config
from Logger import Logger
import time 

class Carro():
    def __init__(self):
        self.actuadores = Actuator()
        self.volante = SteeringController()
        self.sensores = SensorReader()
        self.__x_coordinate = -1
        self.__y_coordinate = -1
        
        # Inicialización de I2C compartido para MPU6050
        self.i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100000)
        self.mpu = accel(self.i2c)
        self.navegador = NavegadorPista(self, self.mpu)
        
        if (Config.ENABLE_SERIAL):
            self.logger = Logger()
            self.logger.begin()

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

    def resolver_pista(self, pista):
        print("Iniciando recorrido libre WRO...")
        
        while not pista.get_resuelto():
            # Ejecuta la lógica de control, giros e integración IMU
            self.navegador.ejecutar_paso(pista)
            
            # Telemetría remota
            if Config.ENABLE_SERIAL:
                datos = self.sensores.get_filtered_data()
                self.logger.send_data(
                    emergency=(self.navegador.estado == NavegadorPista.ESTADO_COMPLETADO),
                    pwm=self.actuadores._current_speed,
                    sensors=datos,
                    steering=self.navegador.yaw_acumulado, # Telemetría del ángulo real
                    x=datos[Config.FRONT_SENSOR_INDEX],
                    y=datos[0],
                    sentido=pista.get_sentido()
                )
            
            time.sleep_ms(30) # Ciclo de control constante a ~33Hz

        self.actuadores.stop()
        print("¡3 Vueltas completadas con éxito!")
