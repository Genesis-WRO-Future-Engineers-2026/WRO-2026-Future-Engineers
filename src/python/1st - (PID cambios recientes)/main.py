import Config
from Carro import Carro
import time
from Pista import Pista

def _fmt(value):
    return "{:7.1f}".format(value)

carro = Carro()
carro.begin()
pista = Pista()

# ============================================================================
# BUCLE DE CONTROL PRINCIPAL
# ============================================================================
#  
# carro.resolver_pista(pista)
# carro.cruce(pista)
# carro.actuadores.set_angle_dg(90)

# ============================================================================
# PRUEBA SENSORES
# ============================================================================
while True:
   sensor_frame = carro.sensores.read_all()
# #    carro.recta_PID(sensor_frame)
   distances = sensor_frame.distances
   print(
             "L {} | LD {} | F {} | RD {} | R {}".format(
                    distances[0],
                    distances[1], 
                    distances[2], 
                    distances[3], 
                    distances[4], 
            )
        )

# ============================================================================
# PRUEBA ANGULO DE SERVO
# ============================================================================

#    valid = sensor_frame.valid
#    front = distances[Config.FRONT]
#    print(carro.controlador_volante.compute_error(distances, valid))

