import rospy
from PID import PID, get_param


class LanePositionPID(PID):
    def __init__(self):
        super().__init__()

    # Update PID params from yaml file
    def update_pid_params(self):
        Kp_old = self.Kp
        Ki_old = self.Ki
        Kd_old = self.Kd
        Kp = get_param("Kp_pos", 0)
        Ki = get_param("Ki_pos", 0)
        Kd = get_param("Kd_pos", 0)
        if Kp != Kp_old or Ki != Ki_old or Kd != Kd_old:
            rospy.logwarn(f"Updated lane position params: Kp={Kp}, Ki={Ki}, Kd={Kd}")
        self.update_params(Kp, Ki, Kd)
