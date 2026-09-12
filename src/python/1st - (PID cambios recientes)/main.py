import Config
from Carro import Carro
import time
from Pista import Pista

carro = Carro()
carro.begin()
pista = Pista()

# ============================================================================
# BUCLE DE CONTROL PRINCIPAL
# ============================================================================
#  
carro.resolver_pista(pista)
# carro.cruce(pista)
# carro.actuadores.set_angle_dg(145)
 
# while True:
#    sensor_frame = carro.sensores.read_all()
#    distances = sensor_frame.distances
#    valid = sensor_frame.valid
#    front = distances[Config.FRONT]
#    print(carro.controlador_volante.compute_error(distances, valid, front))

