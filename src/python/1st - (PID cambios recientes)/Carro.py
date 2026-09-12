#Carro.py
from Actuator import Actuator
from SensorReader import SensorReader
from Pista import Pista
import Config
from Logger import Logger
import time #Chequear envio del tiempo
from SteeringController import SteeringController

class Carro():
    
    DRIVE = 0
    CONFIRM_STOP = 1
    TURN = 2
    DONE = 3
    
    def __init__(self):
        self.actuadores = Actuator()
        self.sensores = SensorReader()
        self.controlador_volante = SteeringController()
        self.stop_count = 0
        self.state = self.DRIVE
        self.start_ms = time.ticks_ms()
        if (Config.ENABLE_SERIAL):
            self.logger = Logger()
            self.logger.begin()
        
        
    def begin(self):
        self.actuadores.begin()
        self.sensores.begin()
        
        
    def _fresh(self, frame, index):
        return frame.valid[index] and frame.distances[index] is not None
    
    def _choose_turn(self, frame):
        left = frame.distances[Config.LEFT]
        right = frame.distances[Config.RIGHT]
        if self._fresh(frame, Config.LEFT) and self._fresh(frame, Config.RIGHT):
            if right > left:
                return Pista.SENTIDO_HORARIO
            return Pista.SENTIDO_ANTIHORARIO

    def _front_stop_candidate(self, frame):
        if not self._fresh(frame, Config.FRONT):
            return False
        return frame.distances[Config.FRONT] <= Config.STOP_DISTANCE_MM 
     
    def recta_PID(self, sensor_frame):
        angulo_objetivo = self.controlador_volante.compute_steering(sensor_frame.distances, sensor_frame.valid)
        self.actuadores.set_angle_dg(angulo_objetivo)
     
    def cruce(self, pista):
        angulo_cruce = pista.get_sentido() * Config.SERVO_LEFT_MAX_DEG
        
        self.actuadores.set_angle_dg(angulo_cruce)
        
        tiempo_inicio = time.ticks_ms()
        duracion = 1500
        
        while time.ticks_diff(time.ticks_ms(), tiempo_inicio) < duracion:
            self.actuadores.set_speed(Config.CRUISE_SPEED)
        
        self.actuadores.stop()
        
        
    def resolver_pista(self, pista):
        self.actuadores.set_speed(Config.CRUISE_SPEED)
        while not pista.esta_resuelta():
            sensor_frame = self.sensores.read_all()
            distancias = sensor_frame.distances
            
            self.recta_PID(sensor_frame)
            
            # No detectar pared durante el arranque para evitar falsos positivos.
            startup_done = time.ticks_diff(time.ticks_ms(), self.start_ms) >= Config.STARTUP_INHIBIT_MS
            if startup_done:
                corner = self.controlador_volante.detect_corner(
                    sensor_frame.distances,
                    sensor_frame.valid
                )

                if corner:
                    self.actuadores.stop()
                    self.state = self.CONFIRM_STOP

            if self.state == self.CONFIRM_STOP:
                pista.set_sentido(self._choose_turn(sensor_frame))
                pista.resuelta()
        
            # ============================================================================
            # MODO 2: TELEMETRÍA EN LA NUBE (Envío a Firebase)
            # ============================================================================
            if(Config.ENABLE_SERIAL):
            
                self.logger.send_data(emergency=parada, pwm=Config.CRUISE_SPEED,sensors=[distancias[sensor] for sensor in range(Config.NUM_SENSORS)], steering=0, sentido=pista.get_sentido())