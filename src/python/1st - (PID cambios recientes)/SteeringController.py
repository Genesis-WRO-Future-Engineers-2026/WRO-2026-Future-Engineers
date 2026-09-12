import Config
from PIDController import PIDController


class SteeringController:
    """Control de trayectoria basado en posicion lateral + orientacion aproximada."""

    def __init__(self):
        self.pid = PIDController(
            Config.KP_STEERING,
            Config.KI_STEERING,
            Config.KD_STEERING,
            Config.PID_OUTPUT_LIMIT_DEG,
            Config.PID_INTEGRAL_LIMIT,
            Config.PID_DERIVATIVE_ALPHA,
        )

    @staticmethod
    def _normalized_difference(left, right):
        den = left + right
        if den <= 1:
            return 0.0
        return (left - right) / den

    def compute_error(self, distances, valid, front_distance=None):
        # Posicion lateral: negativo = mas cerca de la pared izquierda.
        if not (valid[Config.LEFT] and valid[Config.RIGHT]):
            return None

        e_y = self._normalized_difference(
            distances[Config.LEFT], distances[Config.RIGHT]
        )

        e_theta = 0.0
        diagonal_ok = valid[Config.LEFT_DIAG] and valid[Config.RIGHT_DIAG]
        if diagonal_ok:
            e_theta = self._normalized_difference(
                distances[Config.LEFT_DIAG], distances[Config.RIGHT_DIAG]
            )

        # Gating: cerca de una esquina no confiamos en las diagonales.
        gate = 1.0
        if front_distance is not None:
            gate = Config.clamp(
                (front_distance - Config.STOP_DISTANCE_MM)
                / Config.DIAGONAL_GATE_DISTANCE_MM,
                0.0,
                1.0,
            )

        return Config.LATERAL_WEIGHT * e_y + Config.ANGLE_WEIGHT * gate * e_theta

    def compute_steering(self, distances, valid):
        front = distances[Config.FRONT] if valid[Config.FRONT] else None
        error = self.compute_error(distances, valid, front)
        if error is None:
            return Config.SERVO_CENTER_DEG
        correction = self.pid.compute(error)
        # PID positivo => servo hacia la derecha (angulo menor).
        angle = Config.SERVO_CENTER_DEG + correction
        return Config.clamp(
            angle,
            Config.SERVO_CENTER_DEG - Config.STRAIGHT_STEERING_LIMIT_DEG,
            Config.SERVO_CENTER_DEG + Config.STRAIGHT_STEERING_LIMIT_DEG,
        )

    def reset(self):
        self.pid.reset()
