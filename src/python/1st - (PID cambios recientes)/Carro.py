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
        
    def recuperacion_cruce(self, frame):
        inicio = time.ticks_ms()
        self.actuadores.set_speed(Config.MIN_SPEED)
        while (time.ticks_ms() - inicio < Config.TIEMPO_RECUPERACION_CRUCE):
            self.recta_PID(frame)
        self.actuadores.stop()   

    def _front_stop_candidate(self, frame):
        if not self._fresh(frame, Config.FRONT):
            return False
        return frame.distances[Config.FRONT] <= Config.STOP_DISTANCE_MM 
     
    def recta_PID(self, sensor_frame):
        # 1. Vigilar diagonales ANTES de avanzar
        if self.emergencia_diagonales(sensor_frame):
            return # Si hizo el empujoncito, cortamos aquí para no acelerar de frente

        # 2. Lógica normal de recta (solo si no hubo emergencia)
        if sensor_frame.distances[Config.FRONT] <= Config.DISTANCIA_REDUCCION_VELOCIDAD:
            self.actuadores.set_speed(Config.MIN_SPEED)
        else:
            self.actuadores.set_speed(Config.CRUISE_SPEED)
        
        angulo_objetivo = self.controlador_volante.compute_steering(sensor_frame.distances, sensor_frame.valid)
        self.actuadores.set_angle_dg(angulo_objetivo)
        
        corner = self.controlador_volante.detect_corner(
            sensor_frame.distances,
            sensor_frame.valid
        )

        if corner:
            self.state = self.TURN

     
    def cruce(self, pista, sensor_frame):
        pista.marcar_esquina()
        self.actuadores.set_speed(Config.MIN_SPEED)
        angulo_cruce = pista.get_sentido() * Config.SERVO_LEFT_MAX_DEG
        tiempo_inicio = time.ticks_ms()
        
        while time.ticks_diff(time.ticks_ms(), tiempo_inicio) < Config.DURACION_CRUCE:
            
            if sensor_frame.distances[Config.FRONT] <= Config.DISTANCIA_MINIMA_CRUCE_MM:
                self.enderezar(sensor_frame, angulo_cruce)
                sensor_frame = self.sensores.read_all()
            else:
                self.actuadores.set_angle_dg(angulo_cruce)
                self.actuadores.set_speed(Config.CRUISE_SPEED)
            
        self.recuperacion_cruce(sensor_frame)
        self.controlador_volante.corner_detector.reset()
        self.state = self.DRIVE
        self.actuadores.stop()
         
    def enderezar(self, sensor_frame, angulo_cruce):

        distancia_actual = sensor_frame.distances[Config.FRONT]
        diferencia = Config.clamp(distancia_actual - Config.DISTANCIA_MINIMA_CRUCE_MM, 300, 1500)
        
        duracion_ms = int(abs(diferencia) * Config.FACTOR_EMPUJONCITO_MS)
        if duracion_ms <= 0:
            return

        tiempo_inicio = time.ticks_ms()
        angulo_retroceso = Config.SERVO_LEFT_MAX_DEG if  angulo_cruce == Config.SERVO_RIGHT_MAX_DEG else Config.SERVO_RIGHT_MAX_DEG
        self.actuadores.set_angle_dg(angulo_retroceso)   
        while time.ticks_diff(time.ticks_ms(), tiempo_inicio) < duracion_ms:
            self.actuadores.backward(Config.CRUISE_SPEED)
                
        self.actuadores.stop()
                 
        
    def resolver_pista(self, pista):
        self.actuadores.set_speed(Config.CRUISE_SPEED)
        while not pista.esta_resuelta():
            sensor_frame = self.sensores.read_all()
            distancias = sensor_frame.distances
            
            # No detectar pared durante el arranque para evitar falsos positivos.
            startup_done = time.ticks_diff(time.ticks_ms(), self.start_ms) >= Config.STARTUP_INHIBIT_MS
            if startup_done:
                corner = self.controlador_volante.detect_corner(
                    sensor_frame.distances,
                    sensor_frame.valid
                )

                if corner:
                    self.state = self.CONFIRM_STOP

            if self.state == self.CONFIRM_STOP:
                self.actuadores.stop()
                pista.set_sentido(self._choose_turn(sensor_frame))
                pista.resuelta()
            else:
                if distancias[Config.FRONT] < Config.MAX_VALID_DISTANCE_MM and self.actuadores.get_speed() >= Config.CRUISE_SPEED:
                    self.actuadores.set_speed(Config.MIN_SPEED)
                self.recta_PID(sensor_frame)
            # ============================================================================
            # MODO 2: TELEMETRÍA EN LA NUBE (Envío a Firebase)
            # ============================================================================
            if(Config.ENABLE_SERIAL):
                parada = (self.state == self.CONFIRM_STOP) # Variable corregida
                self.logger.send_data(emergency=parada, pwm=Config.CRUISE_SPEED,sensors=[distancias[sensor] for sensor in range(Config.NUM_SENSORS)], steering=0, sentido=pista.get_sentido())
        self.state = self.TURN   
        self.actuadores.stop()
        
        
    def revisar_apertura_y_girar(self, sensor_frame, pista):
        """
        Monitorea los sensores laterales. Si detecta una apertura (supera el umbral 
        de distancia al muro), ejecuta un giro forzado durante un tiempo determinado 
        y luego retorna al modo de conducción normal.
        """
        distances = sensor_frame.distances
        valid = sensor_frame.valid

        # Validar que los sensores laterales estén disponibles y sean válidos
        if not (valid[Config.LEFT] and valid[Config.RIGHT]):
            return False

        dist_izq = distances[Config.LEFT]
        dist_der = distances[Config.RIGHT]

        # Determinar el sentido de la pista
        sentido = pista.get_sentido()

        # Umbral para considerar que hay una esquina/apertura (ej. 500 mm o ajustable en Config)
        umbral_apertura = getattr(Config, 'MAX_DISTANCIA_MURO', 500)

        apertura_detectada = False
        angulo_objetivo = Config.SERVO_CENTER_DEG

        # Lógica de WRO Futuros Ingenieros según el sentido de la pista
        if sentido == pista.SENTIDO_HORARIO and dist_der > umbral_apertura:
            apertura_detectada = True
            angulo_objetivo = Config.SERVO_RIGHT_MAX_DEG  # Giro hacia la derecha
        elif sentido == pista.SENTIDO_ANTIHORARIO and dist_izq > umbral_apertura:
            apertura_detectada = True
            angulo_objetivo = Config.SERVO_LEFT_MAX_DEG   # Giro hacia la izquierda

        if apertura_detectada:
            if Config.ENABLE_SERIAL:
                print("¡Apertura lateral detectada! Ejecutando giro por tiempo...")
            
            tiempo_inicio = time.ticks_ms()
            duracion_giro_ms = 600  # Ajusta este tiempo según las dimensiones de la pista y velocidad

            # Bucle de giro por tiempo con tracción activa
            while time.ticks_diff(time.ticks_ms(), tiempo_inicio) < duracion_giro_ms:
                self.actuadores.set_angle_dg(angulo_objetivo)
                
                if Config.ENABLE_PWM:
                    self.actuadores.set_speed(Config.CRUISE_SPEED)
                
                # Breve pausa para refrescar el bucle interno
                time.sleep_ms(10)

            # Reiniciar el controlador PID para evitar saltos bruscos al volver a la recta
            self.controlador_volante.reset()
            return True

        return False
    
    #===================================================================
    #  Correcion de emergencia con sensores diagonales  
    #=============================================
    def emergencia_diagonales(self, sensor_frame, umbral_ld=30, umbral_der=100):
        distances = sensor_frame.distances
        valid = sensor_frame.valid

        # Revisar diagonal izquierda con su propio umbral (ej: 30 mm)
        if valid[Config.LEFT_DIAG] and distances[Config.LEFT_DIAG] < umbral_ld:
            if Config.ENABLE_SERIAL: print("¡EMERGENCIA IZQ!")
            self.actuadores.stop()
            time.sleep_ms(500)
            self.actuadores.set_angle_dg(Config.SERVO_LEFT_MAX_DEG)
            self.actuadores.backward(255)
            time.sleep_ms(300)
            self.actuadores.stop()
            self.actuadores.set_angle_dg(Config.SERVO_CENTER_DEG)
            self.controlador_volante.reset()
            return True

        # Revisar diagonal derecha con su propio umbral (ej: 110 mm)
        if valid[Config.RIGHT_DIAG] and distances[Config.RIGHT_DIAG] < umbral_der:
            if Config.ENABLE_SERIAL: print("¡EMERGENCIA DER!")
            self.actuadores.stop()
            time.sleep_ms(500)
            self.actuadores.set_angle_dg(Config.SERVO_RIGHT_MAX_DEG)
            self.actuadores.backward(255)
            time.sleep_ms(300)
            self.actuadores.stop()
            self.actuadores.set_angle_dg(Config.SERVO_CENTER_DEG)
            self.controlador_volante.reset()
            return True

        return False