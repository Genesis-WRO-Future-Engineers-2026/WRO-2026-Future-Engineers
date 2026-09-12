import time
import Config


class PIDController:
    """PID con dt en segundos, anti-windup y derivada filtrada."""

    def __init__(self, kp, ki, kd, output_limit, integral_limit, derivative_alpha=0.25):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limit = abs(output_limit)
        self.integral_limit = abs(integral_limit)
        self.derivative_alpha = Config.clamp(derivative_alpha, 0.0, 1.0)
        self.reset()

    def reset(self):
        self.integral = 0.0
        self.previous_error = 0.0
        self.derivative_filtered = 0.0
        self.last_time = None

    def compute(self, error):
        now = time.ticks_ms()
        if self.last_time is None:
            self.last_time = now
            self.previous_error = error
            return Config.clamp(self.kp * error, -self.output_limit, self.output_limit)

        dt_ms = time.ticks_diff(now, self.last_time)
        self.last_time = now
        if dt_ms <= 0:
            dt_ms = 1
        dt = dt_ms / 1000.0
        dt = Config.clamp(dt, 0.001, 0.100)

        derivative = (error - self.previous_error) / dt
        self.derivative_filtered = (
            self.derivative_alpha * derivative
            + (1.0 - self.derivative_alpha) * self.derivative_filtered
        )

        # Integracion con limite. Evita que el integral crezca sin control.
        candidate_integral = self.integral + error * dt
        candidate_integral = Config.clamp(
            candidate_integral, -self.integral_limit, self.integral_limit
        )

        p = self.kp * error
        d = self.kd * self.derivative_filtered
        unsaturated = p + self.ki * candidate_integral + d
        output = Config.clamp(unsaturated, -self.output_limit, self.output_limit)

        # Anti-windup simple: aceptar el integral si no empuja mas hacia saturacion.
        saturated_high = unsaturated > self.output_limit and error > 0
        saturated_low = unsaturated < -self.output_limit and error < 0
        if not saturated_high and not saturated_low:
            self.integral = candidate_integral

        self.previous_error = error
        return output
