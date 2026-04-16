import rospy


def get_param(name, default=None):
    if rospy.has_param(name):
        return rospy.get_param(name)
    else:
        return default


class PID:
    def __init__(self):
        self.Kp = 0
        self.Ki = 0
        self.Kd = 0

        self.current_error = 0
        self.current_time = None

        self.last_error = 0
        self.last_time = None

        self.running_integral = 0

    def update_params(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd

    def calc_proportional_resp(self):
        return -1 * self.Kp * self.current_error

    def calc_integral_resp(self):
        # Windowed integral: only integrate over recent time window
        if self.last_time is None:
            return 0
        dt = self.current_time - self.last_time

        # Add new error contribution using trapezoidal rule with timestamp
        self.running_integral += 0.5 * (self.current_error + self.last_error) * dt
        return -1 * self.Ki * self.running_integral

    def calc_derivative_resp(self):
        # Does not accumulate, current rate of change
        if self.last_time is None:
            return 0
        dt = self.current_time - self.last_time
        derivative = 0
        if dt > 0:
            derivative = (self.current_error - self.last_error) / dt
        return -1 * self.Kd * derivative

    def add_error(self, error, timestamp):
        self.current_error = error
        self.current_time = timestamp.to_sec()

        P = self.calc_proportional_resp()
        I = self.calc_integral_resp()
        D = self.calc_derivative_resp()

        self.last_error = self.current_error
        self.last_time = self.current_time

        return P + I + D
