"""Modo de calibracion y diagnostico.

IMPORTANTE: el modo SENSORS/CONTROL/IMU no mueve motores.
El modo SERVO mueve el servo: levantar el robot y mantener las ruedas libres.
"""
import time
import Config
from SensorReader import SensorReader

try:
    from mpu6050 import MPU6050
except Exception:
    MPU6050 = None


def _fmt(value):
    if value is None:
        return "---"
    return "{:7.1f}".format(value)


def sensor_mode():
    sensors = SensorReader()
    available = sensors.begin()
    print("\n=== CALIBRACION DE SENSORES ===")
    print("Disponibles:", available)
    print("Orden: L, LD, F, RD, R")
    print("Valores en mm. Ctrl+C para salir.\n")

    while True:
        frame = sensors.read_all()
        d = frame.distances
        v = frame.valid
        print(
            "L {} {} | LD {} {} | F {} {} | RD {} {} | R {} {}".format(
                _fmt(d[0]), "OK" if v[0] else "--",
                _fmt(d[1]), "OK" if v[1] else "--",
                _fmt(d[2]), "OK" if v[2] else "--",
                _fmt(d[3]), "OK" if v[3] else "--",
                _fmt(d[4]), "OK" if v[4] else "--",
            )
        )
        time.sleep_ms(Config.CALIBRATION_PRINT_MS)


def servo_mode():
    from Actuator import Actuator
    actuator = Actuator()
    print("\n=== CALIBRACION DEL SERVO ===")
    print("LEVANTA EL ROBOT. Se movera el servo.")
    print("Centro={}, derecha={}, izquierda={}".format(
        Config.SERVO_CENTER_DEG, Config.SERVO_RIGHT_DEG, Config.SERVO_LEFT_DEG
    ))
    print("Ajusta SERVO_CENTER_DEG hasta que las ruedas queden rectas.")

    positions = [
        Config.SERVO_CENTER_DEG,
        Config.SERVO_RIGHT_DEG,
        Config.SERVO_CENTER_DEG,
        Config.SERVO_LEFT_DEG,
        Config.SERVO_CENTER_DEG,
    ]
    for angle in positions:
        print("Servo -> {} deg".format(angle))
        actuator.set_steering(angle)
        time.sleep_ms(Config.CALIBRATION_SERVO_HOLD_MS)
    actuator.stop()
    actuator.set_steering(Config.SERVO_CENTER_DEG)


def control_mode():
    from SteeringController import SteeringController
    sensors = SensorReader()
    available = sensors.begin()
    controller = SteeringController()
    print("\n=== DIAGNOSTICO DEL CONTROLADOR ===")
    print("No se mueven motores ni servo.")
    print("Columnas: sensores | e_y | e_theta | error | PID | servo")
    print("Si el signo de PID no coincide con la correccion fisica, invierte la convencion antes de ajustar Kp/Kd.\n")

    while True:
        frame = sensors.read_all()
        front = frame.distances[Config.FRONT] if frame.valid[Config.FRONT] else None
        error = controller.compute_error(frame.distances, frame.valid, front)
        if error is None:
            print("Sensores laterales no validos")
        else:
            # compute_steering actualiza el PID; calculamos una sola vez por ciclo.
            angle = controller.compute_steering(frame.distances, frame.valid)
            correction = Config.SERVO_CENTER_DEG - angle
            print(
                "L={} LD={} F={} RD={} R={} | e={} | corr={} deg | servo={} deg".format(
                    _fmt(frame.distances[0]), _fmt(frame.distances[1]),
                    _fmt(frame.distances[2]), _fmt(frame.distances[3]),
                    _fmt(frame.distances[4]), _fmt(error),
                    _fmt(correction), _fmt(angle)
                )
            )
        time.sleep_ms(Config.CALIBRATION_PRINT_MS)


def imu_mode():
    if MPU6050 is None:
        print("MPU6050 no disponible.")
        return
    imu = MPU6050()
    print("\n=== CALIBRACION MPU6050 ===")
    print("Mantener robot QUIETO durante la calibracion.")
    imu.calibrate_gyro()
    print("Bias gyro: X={} Y={} Z={}".format(
        imu.gyro_bias[0], imu.gyro_bias[1], imu.gyro_bias[2]
    ))
    print("roll | pitch | inclinacion eje Z")
    while True:
        data = imu.update()
        print("{:7.2f} | {:7.2f} | {:7.2f}".format(
            data[0], data[1], imu.z_axis_tilt()
        ))
        time.sleep_ms(Config.CALIBRATION_PRINT_MS)


def run():
    mode = Config.CALIBRATION_SECTION.upper()
    if mode == "SENSORS":
        sensor_mode()
    elif mode == "SERVO":
        servo_mode()
    elif mode == "CONTROL":
        control_mode()
    elif mode == "IMU":
        imu_mode()
    else:
        print("CALIBRATION_SECTION invalido:", mode)
        print("Usa SENSORS, SERVO, CONTROL o IMU")
