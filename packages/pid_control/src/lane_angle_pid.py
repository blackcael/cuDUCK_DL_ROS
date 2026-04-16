import rospy
from PID import PID, get_param


class LaneAnglePID(PID):
    def __init__(self):
        super().__init__()

    def update_pid_params(self):
        # Update params from yaml file
        Kp_old = self.Kp
        Ki_old = self.Ki
        Kd_old = self.Kd
        Kp = get_param("Kp_angle", 0)
        Ki = get_param("Ki_angle", 0)
        Kd = get_param("Kd_angle", 0)
        if Kp != Kp_old or Ki != Ki_old or Kd != Kd_old:
            rospy.logwarn(f"Updated lane angle params: Kp={Kp}, Ki={Ki}, Kd={Kd}")
        self.update_params(Kp, Ki, Kd)
