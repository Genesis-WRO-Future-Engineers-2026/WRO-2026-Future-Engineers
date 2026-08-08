#Navegacion.py
import time
import math
import Config

class PIDController:
    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.prev_error = 0.0
        self.integral = 0.0

    def compute(self, setpoint, measured_value, dt):
        error = setpoint - measured_value
        self.integral += error * dt
        # Anti-windup para el término integral
        self.integral = max(-100.0, min(100.0, self.integral))
        
        derivative = (error - self.prev_error) / dt if dt > 0 else 0.0
        self.prev_error = error
        
        return (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)

    def reset(self):
        self.prev_error = 0.0
        self.integral = 0.0


class NavegadorPista:
    # Estados de Navegación
    ESTADO_BUSCAR_SENTIDO = 0
    ESTADO_SEGUIR_CARRIL = 1
    ESTADO_GIRO_ESQUINA = 2
    ESTADO_COMPLETADO = 3

    def __init__(self, carro, mpu):
        self.carro = carro
        self.mpu = mpu
        self.pid = PIDController(kp=0.15, ki=0.001, kd=0.05)
        
        self.estado = self.ESTADO_BUSCAR_SENTIDO
        self.yaw_acumulado = 0.0
        self.last_time = time.ticks_ms()
        self.vueltas = 0
        self.target_yaw_esquina = 0.0
        
        # Umbrales geométricos (en mm)
        self.UMBRAL_CARRIL_ABIERTO = 1200.0  # Si lee más de esto, la pared "desapareció"
        self.DIST_GIRO_FRONTAL = 450.0      # Distancia frontal para iniciar el giro de 90°

    def actualizar_imu(self):
        """Lee el giroscopio GyZ de la MPU y actualiza el Yaw acumulado"""
        now = time.ticks_ms()
        dt = time.ticks_diff(now, self.last_time) / 1000.0
        self.last_time = now
        
        if dt <= 0 or dt > 0.5:
            return

        values = self.mpu.get_values()
        # MPU6050 típica a +-250 deg/s mapea 131 LSB / (deg/s)
        gyz_deg_sec = values["GyZ"] / 131.0 
        
        # Filtro de zona muerta (noise gate) para lecturas estáticas
        if abs(gyz_deg_sec) > 1.5:
            self.yaw_acumulado += gyz_deg_sec * dt

    def ejecutar_paso(self, pista):
        self.actualizar_imu()
        self.carro.sensores.read_all()
        sensores = self.carro.sensores.get_filtered_data()
        
        s_izq_90   = sensores[0]
        s_izq_45   = sensores[1]
        s_front_0  = sensores[Config.FRONT_SENSOR_INDEX]
        s_der_45   = sensores[3]
        s_der_90   = sensores[4]

        # ====================================================================
        # ESTADO 0: DETERMINAR SENTIDO EN EL PRIMER CRUCE
        # ====================================================================
        if self.estado == self.ESTADO_BUSCAR_SENTIDO:
            self.carro.actuadores.set_speed(Config.CRUISE_SPEED)
            self.carro.actuadores.set_steering(0) # Recto
            
            if s_front_0 < self.DIST_GIRO_FRONTAL or s_izq_90 > self.UMBRAL_CARRIL_ABIERTO or s_der_90 > self.UMBRAL_CARRIL_ABIERTO:
                if s_der_90 > s_izq_90:
                    pista.set_sentido(pista.SENTIDO_HORARIO)
                else:
                    pista.set_sentido(pista.SENTIDO_ANTIHORARIO)
                
                self.pid.reset()
                self.estado = self.ESTADO_SEGUIR_CARRIL

        # ====================================================================
        # ESTADO 1: SEGUIMIENTO DE CARRIL CON PID
        # ====================================================================
        elif self.estado == self.ESTADO_SEGUIR_CARRIL:
            self.carro.actuadores.set_speed(Config.CRUISE_SPEED)
            
            # Verificación de giro imminentemente en la pared frontal
            if s_front_0 <= self.DIST_GIRO_FRONTAL or s_izq_45 < 300 or s_der_45 < 300:
                self.estado = self.ESTADO_GIRO_ESQUINA
                # Target: Girar +90° o -90° respecto al Angulo actual
                giro = -90.0 if pista.get_sentido() == pista.SENTIDO_HORARIO else 90.0
                self.target_yaw_esquina = self.yaw_acumulado + giro
                return

            # PID Centrado:
            # Caso A: Ambos lados cerrados (Centrado Doble Pared)
            if s_izq_90 < self.UMBRAL_CARRIL_ABIERTO and s_der_90 < self.UMBRAL_CARRIL_ABIERTO:
                error = s_izq_90 - s_der_90
            # Caso B: Salida a cruce por la derecha (Mantenerse pegado a pared Izquierda)
            elif s_izq_90 < self.UMBRAL_CARRIL_ABIERTO:
                error = (s_izq_90 - 350.0)
            # Caso C: Salida a cruce por la izquierda (Mantenerse pegado a pared Derecha)
            elif s_der_90 < self.UMBRAL_CARRIL_ABIERTO:
                error = (350.0 - s_der_90)
            else:
                error = 0.0

            steering_angle = self.pid.compute(setpoint=0.0, measured_value=error, dt=0.05)
            self.carro.actuadores.set_steering(steering_angle)

        # ====================================================================
        # ESTADO 2: GIRO DE ESQUINA (GUIADO POR MPU6050)
        # ====================================================================
        elif self.estado == self.ESTADO_GIRO_ESQUINA:
            angulo_max_servo = Config.MAX_STEERING_ANGLE if pista.get_sentido() == pista.SENTIDO_HORARIO else -Config.MAX_STEERING_ANGLE
            self.carro.actuadores.set_steering(angulo_max_servo)
            self.carro.actuadores.set_speed(Config.CRUISE_SPEED - 30) # Reducir velocidad al girar
            
            # Verificar si ya rotó los 90° requeridos en la esquina
            if abs(self.yaw_acumulado - self.target_yaw_esquina) < 15.0 or \
               (pista.get_sentido() == pista.SENTIDO_HORARIO and self.yaw_acumulado <= self.target_yaw_esquina) or \
               (pista.get_sentido() == pista.SENTIDO_ANTIHORARIO and self.yaw_acumulado >= self.target_yaw_esquina):
                
                self.pid.reset()
                self.estado = self.ESTADO_SEGUIR_CARRIL

        # Verificar si completó las 3 Vueltas (360° * 3 = 1080°)
        self.vueltas = abs(self.yaw_acumulado) / 360.0
        if self.vueltas >= 3.0:
            self.estado = self.ESTADO_COMPLETADO
            self.carro.actuadores.stop()
            pista.set_resuelto(True)
