import Config
from Carro import Carro
import time
from Pista import Pista

def main():
    print("=== INICIANDO CARRO - WRO FUTUROS INGENIEROS ===")
    
    carro = Carro()
    carro.begin()
    
    pista = Pista()
    pista.set_sentido(Pista.SENTIDO_HORARIO)
    pista.resuelta()

    print("Entrando al bucle principal de carrera...")

    try:
        while True:
            # 1. Leer sensores
            sensor_frame = carro.sensores.read_all()

            # 2. Verificar emergencia diagonal con umbrales independientes
            emergencia_activa = carro.emergencia_diagonales(sensor_frame)

            # Si el carro hizo el rescate, saltamos el resto del ciclo
            if emergencia_activa:
                continue

            # 3. Lógica normal de dirección (PID)
            angulo_steering = carro.controlador_volante.compute_steering(
                sensor_frame.distances, 
                sensor_frame.valid
            )
            
            carro.actuadores.set_angle_dg(angulo_steering)

            if Config.ENABLE_PWM:
                carro.actuadores.set_speed(Config.CRUISE_SPEED)

            time.sleep_ms(5)

    except KeyboardInterrupt:
        print("\nPrueba detenida manualmente. Apagando motores...")
        carro.actuadores.stop()

if __name__ == "__main__":
    main()