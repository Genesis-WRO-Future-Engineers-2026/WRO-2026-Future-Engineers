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

# Distribución y orientación física real de tus 5 sensores (Izquierda a Derecha)
SENSOR_ANGLES = [-90.0, -45.0, 0.0, 45.0, 90.0]
SENSOR_OFFSETS = [197, 220, 0, 350, 178]
FRONT_SENSOR_INDEX = 2                        # El sensor central (0.0°) está en el índice 2

# Thresholds de los sensores
RELIABLE_RANGE = 1000         # Max trusted distance (mm)
MIN_VALID_DISTANCE = 40       # Min trusted distance (mm)
CRITICAL_STOP_THRESHOLD = 150 # Front emergency-stop threshold (mm)
AUTO_STOP_SECONDS = 20       # Tiempo de parada automática en segundos

# ============================================================================
# ACTUADORES (Pines y Calibración en Grados)
# ============================================================================
# --- Servo de Dirección ---
SERVO_PIN = 40
SERVO_CENTER_DEG = 24         # Ángulo para ir totalmente recto
SERVO_RIGHT_MAX_DEG = 0       # Ángulo máximo físico a la derecha
SERVO_LEFT_MAX_DEG = 48      # Ángulo máximo físico a la izquierda
MAX_STEERING_ANGLE = 20    # Límite de cálculo por software (Pure Pursuit)

# --- Motor de Tracción (TB6612FNG) ---
MOTOR_IN1_PIN = 34
MOTOR_IN2_PIN = 21
MOTOR_PWMA_PIN = 17

PWM_FREQ = 20000              # 20kHz inaudible para el motor
CRUISE_SPEED = 145            # Velocidad base de crucero (0-255)

# ============================================================================
# PARÁMETROS DE LOS ALGORITMOS
# ============================================================================
# --- Pure Pursuit ---
WHEELBASE_MM = 92.0           # L: distancia entre ejes
LOOKAHEAD_OFFSET_MM = 400.0   # Restado a la distancia frontal para Ld

# --- Gap Finder ---
FARTHEST_HYSTERESIS = 150.0   # Histéresis en mm para evitar vibraciones del servo

# ============================================================================
# CONSTANTES MATEMÁTICAS
# ============================================================================
DEG_TO_RAD = math.pi / 180.0
RAD_TO_DEG = 180.0 / math.pi
SIN_45_DEG = 0.7071067811     # Factor trigonométrico fijo para áreas

# --- Parámetros de Pure Pursuit por Coordenadas ---
LOOKAHEAD_PURE_PURSUIT = 150.0  # Ld en mm


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