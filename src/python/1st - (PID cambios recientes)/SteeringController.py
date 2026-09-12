import Config
from PIDController import PIDController
from CornerDetector import CornerDetector


class SteeringController:

    def __init__(self):

        self.pid = PIDController(
            Config.KP_STEERING,
            Config.KI_STEERING,
            Config.KD_STEERING,
            Config.PID_OUTPUT_LIMIT_DEG,
            Config.PID_INTEGRAL_LIMIT,
            Config.PID_DERIVATIVE_ALPHA,
        )

        # ---------------------------------------------------------
        # Memoria del último error válido
        # ---------------------------------------------------------
        self.last_error = 0.0

        # Indica si alguna vez hemos tenido un error válido.
        self.has_previous_error = False

        # Último ángulo de dirección calculado.
        self.last_steering_angle = Config.SERVO_CENTER_DEG
        
        self.corner_detector = CornerDetector()

    # =============================================================
    # ERROR NORMALIZADO
    # =============================================================

    @staticmethod
    def _normalized_difference(left, right):

        den = left + right

        if den <= 1:
            return None

        return (left - right) / den

    # =============================================================
    # CÁLCULO DEL ERROR
    # =============================================================

    def compute_error(
        self,
        distances,
        valid,
        front_distance=None
    ):

        # ---------------------------------------------------------
        # Comprobamos sensores laterales.
        # ---------------------------------------------------------

        left_ok = (
            valid[Config.LEFT]
            and distances[Config.LEFT] is not None
        )

        right_ok = (
            valid[Config.RIGHT]
            and distances[Config.RIGHT] is not None
        )

        # ---------------------------------------------------------
        # Si uno de los sensores laterales no está disponible,
        # NO inventamos un error.
        #
        # El controlador superior decidirá utilizar el último error.
        # ---------------------------------------------------------

        if not (left_ok and right_ok):
            return None

        # ---------------------------------------------------------
        # Error lateral.
        # ---------------------------------------------------------

        e_y = self._normalized_difference(
            distances[Config.LEFT],
            distances[Config.RIGHT]
        )

        if e_y is None:
            return None

        # ---------------------------------------------------------
        # Error de orientación mediante diagonales.
        # ---------------------------------------------------------

        e_theta = 0.0

        diagonal_ok = (
            valid[Config.LEFT_DIAG]
            and valid[Config.RIGHT_DIAG]
            and distances[Config.LEFT_DIAG] is not None
            and distances[Config.RIGHT_DIAG] is not None
        )

        if diagonal_ok:

            diagonal_error = self._normalized_difference(
                distances[Config.LEFT_DIAG],
                distances[Config.RIGHT_DIAG]
            )

            if diagonal_error is not None:
                e_theta = diagonal_error

        # ---------------------------------------------------------
        # Gate de diagonales.
        #
        # Las diagonales tienen mayor importancia cerca de la
        # pared frontal / esquina.
        # ---------------------------------------------------------

        gate = 1.0

        if front_distance is not None:

            gate = Config.clamp(
                (
                    front_distance
                    - Config.CORNER_FRONT_DISTANCE_MM
                )
                / Config.DIAGONAL_GATE_DISTANCE_MM,
                0.0,
                1.0
            )

        # ---------------------------------------------------------
        # Error combinado.
        # ---------------------------------------------------------

        error = (
            Config.LATERAL_WEIGHT * e_y
            + Config.ANGLE_WEIGHT * gate * e_theta
        )

        return error

    # =============================================================
    # CONTROL DE DIRECCIÓN
    # =============================================================

    def compute_steering(self, distances, valid):

        # ---------------------------------------------------------
        # Sensor frontal
        # ---------------------------------------------------------

        front = None

        if (
            valid[Config.FRONT]
            and distances[Config.FRONT] is not None
        ):
            front = distances[Config.FRONT]

        # ---------------------------------------------------------
        # Intentamos calcular un nuevo error.
        # ---------------------------------------------------------

        error = self.compute_error(
            distances,
            valid,
            front
        )

        # =========================================================
        # CASO 1:
        # Tenemos un nuevo error válido.
        # =========================================================

        if error is not None:

            self.last_error = error
            self.has_previous_error = True

        # =========================================================
        # CASO 2:
        # No tenemos error nuevo.
        #
        # UTILIZAMOS EL ERROR ANTERIOR.
        # =========================================================

        else:

            if self.has_previous_error:

                error = self.last_error

            else:

                # Todavía no tenemos ninguna referencia.
                # En el arranque sí tiene sentido comenzar centrado.
                error = 0.0

        # ---------------------------------------------------------
        # Ejecutamos PID.
        # ---------------------------------------------------------

        correction = self.pid.compute(error)

        # ---------------------------------------------------------
        # IMPORTANTE:
        #
        # Convención del servo:
        #
        #   0°   = derecha
        #   75°  = centro
        #   150° = izquierda
        #
        # Por lo tanto, si correction > 0 significa "girar
        # a la derecha", debemos RESTAR la corrección.
        # ---------------------------------------------------------

        angle = (
            Config.SERVO_CENTER_DEG
            + correction
        )

        # ---------------------------------------------------------
        # Limitar dirección.
        # ---------------------------------------------------------

        angle = Config.clamp(
            angle,
            Config.SERVO_CENTER_DEG
            - Config.STRAIGHT_STEERING_LIMIT_DEG,

            Config.SERVO_CENTER_DEG
            + Config.STRAIGHT_STEERING_LIMIT_DEG
        )

        # ---------------------------------------------------------
        # Guardar último ángulo.
        # ---------------------------------------------------------

        self.last_steering_angle = angle

        return angle

    # =============================================================
    # RESET
    # =============================================================

    def reset(self):

        self.pid.reset()

        self.last_error = 0.0
        self.has_previous_error = False

        self.last_steering_angle = (
            Config.SERVO_CENTER_DEG
        )
        
    def detect_corner(self, distances, valid):

        return self.corner_detector.update(
            distances,
            valid
        )
