import Config
from Logger import Logger
from Carro import Carro
import time
from Pista import Pista


carro = Carro()
carro.begin()
pista = Pista()

if (Config.ENABLE_SERIAL):
    logger = Logger()
    logger.begin()

# ============================================================================
# BUCLE DE CONTROL PRINCIPAL
# ============================================================================
print("\n--- INICIANDO NAVEGACIÓN Y TELEMETRÍA ---")

while True:
    # Registramos el tiempo en microsegundos en el que inicia el ciclo
    t_ciclo_inicio = time.ticks_us()
    
    # 1. CAPA DE HARDWARE: Leer los sensores ToF
    t_sensor_inicio = time.ticks_us()
    carro.sensores.read_all()
    datos_sensores = carro.sensores.get_all_data()
    t_sensor_total = time.ticks_diff(time.ticks_us(), t_sensor_inicio)
    
    # 3. CAPA DE ACTUADORES: Aplicar movimiento físico al coche
    carro.actuadores.set_steering(Config.SERVO_CENTER_DEG)
    
    
    if carro.sensores.get_all_data()[Config.FRONT_SENSOR_INDEX].distance < Config.CRITICAL_STOP_THRESHOLD:
        carro.actuadores.stop()
        pista.set_sentido(pista.SENTIDO_HORARIO if carro.sensores.get_all_data()[4].distance > carro.sensores.get_all_data()[0].distance else pista.SENTIDO_ANTIHORARIO)
        carro.set_y_coordinate(carro.sensores.get_all_data()[4].distance if pista.get_sentido() == pista.SENTIDO_HORARIO else pista.ANCHO - carro.sensores.get_all_data()[4].distance)
    else:
        carro.actuadores.set_speed(Config.CRUISE_SPEED)
  
    carro.set_x_coordinate(carro.sensores.get_all_data()[Config.FRONT_SENSOR_INDEX])
    
    # Calcula cuánto tardó todo el bucle en procesar la información
    t_ciclo_total = time.ticks_diff(time.ticks_us(), t_ciclo_inicio)
    
    
    # ============================================================================
    # MODO 2: TELEMETRÍA EN LA NUBE (Envío a Firebase)
    # ============================================================================
    parada_emergencia = carro.sensores.get_all_data()[Config.FRONT_SENSOR_INDEX].distance < Config.CRITICAL_STOP_THRESHOLD
    
    if(Config.ENABLE_SERIAL):
        logger.send_data(emergency=parada_emergencia, pwm=Config.CRUISE_SPEED,sensors=[carro.sensores.get_all_data()[sensor].distance for sensor in range(Config.NUM_SENSORS)], steering=0, x=carro.get_x_coordinate(), y=carro.get_y_coordinate(), sentido=pista.get_sentido())
    
    # Pequeña pausa de estabilidad (50ms)
    time.sleep_ms(50)

