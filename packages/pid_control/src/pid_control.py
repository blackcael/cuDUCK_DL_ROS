#!/usr/bin/env python3
import rospy

from collections import deque

from std_msgs.msg import Float32


class PIDControl:
    Kp = 0.22
    Ki = 0.08
    Kd = 0.95

    # Keep only last N seconds for integral
    WINDOWED_INTEGRAL_TIME = 5

    def __init__(self):
        rospy.init_node("pid_control", anonymous=True)
        rospy.Subscriber("error", Float32, self.error_cb)

        self.pub = rospy.Publisher("control_input", Float32, queue_size=10)

        # Values for PID controller
        self.last_error = 0
        self.last_time = None

        self.current_error = 0
        self.current_time = None

        self.running_integral = 0
        self.error_history = deque()  # Store (error_contribution, timestamp) tuples

    def calc_proportional_resp(self):
        return self.Kp * self.current_error

    def calc_integral_resp(self):
        # Windowed integral: only integrate over recent time window
        if self.last_time is None:
            return 0
        dt = self.current_time - self.last_time

        # Add new error contribution using trapezoidal rule with timestamp
        error_contribution = 0.5 * (self.current_error + self.last_error) * dt
        self.error_history.append((error_contribution, self.current_time))

        # Remove contributions older than the time window
        cutoff_time = self.current_time - self.WINDOWED_INTEGRAL_TIME
        while self.error_history and self.error_history[0][1] < cutoff_time:
            self.error_history.popleft()

        # Recalculate integral from windowed history
        self.running_integral = sum(
            contribution for contribution, _ in self.error_history
        )

        return self.Ki * self.running_integral

    def calc_derivative_resp(self):
        # Does not accumulate, current rate of change
        if self.last_time is None:
            return 0
        dt = self.current_time - self.last_time
        derivative = 0
        if dt > 0:
            derivative = (self.current_error - self.last_error) / dt
        return self.Kd * derivative

    def error_cb(self, msg):
        self.current_error = msg.data
        self.current_time = rospy.get_time()

        # PID calculations
        P = self.calc_proportional_resp()
        I = self.calc_integral_resp()
        D = self.calc_derivative_resp()
        rospy.logwarn(f"P: {P}, I: {I}, D: {D}")

        control_msg = Float32()
        control_msg.data = P + I + D

        self.last_error = self.current_error
        self.last_time = self.current_time

        self.pub.publish(control_msg)


if __name__ == "__main__":
    PIDControl()
    rospy.spin()
