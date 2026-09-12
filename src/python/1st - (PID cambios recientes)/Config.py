# Config.py
import math
from Pista import Pista

# ============================================================================
# --- CONFIGURACIÓN DE RED Y FIREBASE ---
# ============================================================================
WIFI_SSID = "Fundacite_Robotica"                                       
WIFI_PASSWORD = "Fundacite.1234"                                       
FIREBASE_URL = "https://wro-fe-default-rtdb.firebaseio.com/.json"  

# ============================================================================
# RUN MODE (Modos de ejecución como en tu Arduino)
# ============================================================================
MODE_DEBUG = 0       # debug only (no PWM, serial enabled)
MODE_PRODUCTION = 1  # race run (PWM enabled, serial disabled)
MODE_DEBUG_RUN = 2   # debug run (PWM enabled, serial enabled)

RUN_MODE = MODE_PRODUCTION # <-- Selecciona el modo aquí

# Feature toggles automáticos derivados de RUN_MODE
ENABLE_SERIAL = (RUN_MODE == MODE_DEBUG or RUN_MODE == MODE_DEBUG_RUN)
ENABLE_PWM = (RUN_MODE == MODE_PRODUCTION or RUN_MODE == MODE_DEBUG_RUN)

# ============================================================================
# HARDWARE & SENSORES ToF VL53L0X
# ============================================================================
NUM_SENSORS = 5
XSHUT_PINS = [1, 2, 3, 4, 5]                  # Pines físicos conectados a los XSHUT
SENSOR_ADDRESSES = [0x30, 0x32, 0x34, 0x36, 0x38] # Direcciones consecutivas reales


LEFT = 0
LEFT_DIAG = 1
FRONT = 2
RIGHT_DIAG = 3
RIGHT = 4

# Distribución y orientación física real de tus 5 sensores (Izquierda a Derecha)
SENSOR_ANGLES = [-90.0, -45.0, 0.0, 45.0, 90.0]
SENSOR_OFFSETS = [0, 0, 30, 60, 0]
FRONT_SENSOR_INDEX = 2                        # El sensor central (0.0°) está en el índice 2

# Thresholds de los sensores
RELIABLE_RANGE = 1500         # Max trusted distance (mm)
MIN_VALID_DISTANCE = 40       # Min trusted distance (mm)
STOP_DISTANCE_MM = 900 # Front emergency-stop threshold (mm)
STOP_CONFIRM_COUNT = 4
DISTANCIA_FRENADO = 600
STARTUP_INHIBIT_MS = 700   # Tiempo de inicio
MAX_DISTANCIA_MURO = 500
DURACION_INICIO = 1500

MIN_VALID_DISTANCE_MM = 40
MAX_VALID_DISTANCE_MM = 1800
MAX_WALL_DISTANCE_MM = 1200


# ---------------- Filtrado ----------------
FILTER_ALPHA = 0.45       # EMA: 0..1; mayor = mas rapido, menor = mas suave
STALE_TIMEOUT_MS = 150


# ============================================================================
# ACTUADORES (Pines y Calibración en Grados)
# ============================================================================
# --- Servo de Dirección ---
SERVO_PIN = 40
SERVO_CENTER_DEG = 75         # Ángulo para ir totalmente recto
SERVO_RIGHT_MAX_DEG = 0       # Ángulo máximo físico a la derecha
SERVO_LEFT_MAX_DEG = 150      # Ángulo máximo físico a la izquierda
STRAIGHT_STEERING_LIMIT_DEG = 20
TURN_STEERING_DEG = 75

# --- Motor de Tracción (TB6612FNG) ---
MOTOR_IN1_PIN = 34
MOTOR_IN2_PIN = 21
MOTOR_PWMA_PIN = 17

PWM_FREQ = 20000              # 20kHz inaudible para el motor
CRUISE_SPEED = 160            # Velocidad base de crucero (0-255)
MIN_SPEED = 70

# ============================================================================
# CONSTANTES MATEMÁTICAS
# ============================================================================
DEG_TO_RAD = math.pi / 180.0
RAD_TO_DEG = 180.0 / math.pi
SIN_45_DEG = 0.7071067811     # Factor trigonométrico fijo para áreas

# ---------------- Control PID ----------------
# El error es adimensional y normalmente esta entre -1 y +1.
# La salida esta en grados de servo respecto al centro.
KP_STEERING = 28.0
KI_STEERING = 0.0
KD_STEERING = 1.2
PID_OUTPUT_LIMIT_DEG = STRAIGHT_STEERING_LIMIT_DEG
PID_INTEGRAL_LIMIT = 0.35
PID_DERIVATIVE_ALPHA = 0.25

# Pesos del error matematico:
# e_y = (d_left - d_right)/(d_left + d_right)
# e_theta = (d_left_diag - d_right_diag)/(d_left_diag + d_right_diag)
LATERAL_WEIGHT = 1.0
ANGLE_WEIGHT = 0.80

# Las diagonales pierden influencia al acercarse a una esquina.
DIAGONAL_GATE_DISTANCE_MM = 1100


# --- Trayectoria Predefinida en Boxes (Waypoints en mm) ---
TRAYECTORIA = [
    {'x': 600, 'y': 200},
    {'x': 200, 'y': 600},
    {'x': 200, 'y': 2600},
    {'x': 600, 'y': 3000},
    {'x': 2600, 'y': 3000},
    {'x': 3000, 'y': 2600},
    {'x': 3000, 'y': 600},
    {'x': 2600, 'y': 200},
    {'x': 600, 'y': 200}
    ]

def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value