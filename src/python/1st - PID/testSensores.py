# test_sensores.py
from SensorReader import SensorReader
import time

lector = SensorReader()
print("Iniciando lectura de sensores...")
lector.begin()

while True:
    try:
        lector.read_all()
        # Obtenemos los datos filtrados (el promedio de las últimas lecturas)
        datos_filtrados = lector.get_filtered_data()
        # Obtenemos los datos crudos para ver si son válidos
        datos_crudos = lector.get_all_data()
        
        print("--- Lecturas actuales ---")
        for i in range(5):
            print(f"Sensor {i}: Distancia = {datos_filtrados[i]} mm | Válido = {datos_crudos[i].valid}")
            
        print("-------------------------")
        time.sleep_ms(500)
        
    except KeyboardInterrupt:
        print("Prueba finalizada.")
        break