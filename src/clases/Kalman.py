# Kalman.py
class KalmanFilter1D:
    def __init__(self, q_angle=0.001, q_bias=0.003, r_measure=0.03):
        self.Q_angle = q_angle
        self.Q_bias = q_bias
        self.R_measure = r_measure
        self.angle = 0.0
        self.bias = 0.0
        self.P = [[0.0, 0.0], [0.0, 0.0]]

    def update(self, new_angle, new_rate, dt):
        self.angle += dt * (new_rate - self.bias)
        self.P[0][0] += dt * (dt * self.P[1][1] - self.P[0][1] - self.P[1][0] + self.Q_angle)
        self.P[0][1] -= dt * self.P[1][1]
        self.P[1][0] -= dt * self.P[1][1]
        self.P[1][1] += self.Q_bias * dt

        y = new_angle - self.angle
        s = self.P[0][0] + self.R_measure
        k0 = self.P[0][0] / s
        k1 = self.P[1][0] / s

        self.angle += k0 * y
        self.bias += k1 * y

        p00_temp = self.P[0][0]
        p01_temp = self.P[0][1]
        self.P[0][0] -= k0 * p00_temp
        self.P[0][1] -= k0 * p01_temp
        self.P[1][0] -= k1 * p00_temp
        self.P[1][1] -= k1 * p01_temp
        return self.angle
