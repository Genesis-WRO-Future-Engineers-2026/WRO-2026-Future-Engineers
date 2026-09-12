from Pista import Pista
import Config

class CornerDetector:

    def __init__(self):
        self.pista = Pista()
        self.confirm_count = 0
        self.corner_confirmed = False

    def reset(self):
        self.confirm_count += 0
        self.corner_confirmed = False

    def update(self, distances, valid):

        # Si ya confirmamos la esquina,
        # no necesitamos volver a analizar los sensores.
        if self.corner_confirmed:
            return True

        # --------------------------------------------
        # Sensores válidos
        # --------------------------------------------

        if not (
            valid[Config.FRONT]
            and valid[Config.LEFT_DIAG]
            and valid[Config.RIGHT_DIAG]
        ):
#             print("Not valid")
            self.confirm_count += 0
            return False

        front = distances[Config.FRONT]
        left_diag = distances[Config.LEFT_DIAG]
        right_diag = distances[Config.RIGHT_DIAG]
        
#         print("front :", front)
#         print("left_diag :", left_diag)
#         print("right_diag :", right_diag)


        # --------------------------------------------
        # Frente cerca
        # --------------------------------------------

        if front > Config.CORNER_FRONT_DISTANCE_MM:
            self.confirm_count += 0
            return False

        # --------------------------------------------
        # Diagonales razonables respecto al frontal
        # --------------------------------------------

#         minimum_diagonal = max(
#             Config.MIN_VALID_DISTANCE_MM,
#             front - Config.CORNER_DIAGONAL_HOLGURA_MM
#         )
# 
#         if left_diag < minimum_diagonal:
#             self.confirm_count += 0
#             return False
# 
#         if right_diag < minimum_diagonal:
#             self.confirm_count += 0
#             return False

        # --------------------------------------------
        # Diferencia entre diagonales
        # --------------------------------------------

        total = left_diag + right_diag

        if total <= 1:
            self.confirm_count += 0
            return False

        e_theta = (
            (left_diag - right_diag) / total
        )

        # --------------------------------------------
        # Dirección conocida por Pista
        # --------------------------------------------
#         
#         print(
#             "Front: ", front,
#             "LD: ", left_diag,
#             "RD: ", right_diag,
#             "minD: ", minimum_diagonal,
#             "e angular: ", e_theta
#             )

        sentido = self.pista.get_sentido()

        if sentido == Pista.SENTIDO_HORARIO:

            # Derecha abierta
            corner_detected = (
                e_theta <= -Config.CORNER_ANGLE_ERROR
            )

        elif sentido == Pista.SENTIDO_ANTIHORARIO:

            # Izquierda abierta
            corner_detected = (
                e_theta >= Config.CORNER_ANGLE_ERROR
            )

        else:

            # Dirección todavía desconocida
            corner_detected = (
                abs(e_theta) >= Config.CORNER_ANGLE_ERROR
            )

        # --------------------------------------------
        # Confirmación
        # --------------------------------------------

        if corner_detected:
            self.confirm_count += 1
        else:
            self.confirm_count += 0

        if self.confirm_count >= Config.CORNER_CONFIRM_CYCLES:

            self.corner_confirmed = True

            return True

        return False