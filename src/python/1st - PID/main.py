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
 
carro.resolver_pista(pista)
carro.cruce(pista)
# carro.actuadores.set_angle_dg(145)
 
# while True:
#     carro.sensores.read_all()
#     print(carro.sensores.get_filtered_data())

