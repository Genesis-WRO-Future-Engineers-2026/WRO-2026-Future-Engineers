import time

class PIDController:
    def __init__(self, kp=0.2, ki=0, kd=0, default_dt=0.01):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.default_dt = default_dt
        self.prev_error = 0.0
        self.integral = 0.0
        self.last_time = None  

    def compute(self, setpoint, measured_value):
        current_time = time.ticks_ms()

        
        if self.last_time is None:
            dt = self.default_dt
        else:
            dt = time.ticks_diff(current_time, self.last_time)

        
        if dt <= 0.0:
            dt = 1e-6

        error = setpoint - measured_value
        
       
        self.integral += error * dt
        self.integral = max(-100.0, min(100.0, self.integral)) # Anti-windup
        
        
        derivative = (error - self.prev_error) / dt if self.last_time is not None else 0.0
        
        
        self.prev_error = error
        self.last_time = current_time
        
        
        return (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)

    def reset(self):
        self.prev_error = 0.0
        self.integral = 0.0
        self.last_time = None  