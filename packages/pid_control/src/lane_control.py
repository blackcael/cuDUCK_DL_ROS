#!/usr/bin/env python3
import rospy
import os

from duckietown_msgs.msg import LanePose, Twist2DStamped

from lane_angle_pid import LaneAnglePID
from lane_position_pid import LanePositionPID

# Demo Lane Controller Node Attributes:
#################################################
# Node: /<duckiebot>/lane_controller_node

# Subscribes to:
# /<duckiebot>/lane_filter_node/lane_pose       Type: duckietown_msgs/LanePose

# Publishes to:
# /<duckiebot>/lane_controller_node/car_cmd     Type: duckietown_msgs/Twist2DStamped


# duckietown_msgs/LanePose
#   int32 NORMAL=0
#   int32 ERROR=1
#   std_msgs/Header header
#     uint32 seq
#     time stamp
#     string frame_id
#   float32 d
#   float32 d_ref
#   float32 phi
#   float32 phi_ref
#   float32[4] d_phi_covariance
#   float32 curvature
#   float32 curvature_ref
#   float32 v_ref
#   int32 status
#   bool in_lane

# duckietown_msgs/Twist2DStamped
#   std_msgs/Header header
#     uint32 seq
#     time stamp
#     string frame_id
#   float32 v
#   float32 omega
#################################################

DUCKIEBOT = os.environ.get("VEHICLE_NAME")

# Subscriber topics
LANE_FILTER_NODE = f"/{DUCKIEBOT}/lane_filter_node/lane_pose"

# Publisher topics
INTERSECTION_CONTROL = True  # Set to False to publish to lane control
LANE_CONTROL_TOPIC = f"/{DUCKIEBOT}/lane_controller_node/car_cmd"
INTERSECTION_CONTROL_TOPIC = f"/{DUCKIEBOT}/intersectionFSM_node/car_cmd"


class LaneControl:
    VELOCITY_DEF = 0.25
    UPDATE_THRESHOLD = 10

    def __init__(self):
        assert DUCKIEBOT is not None, "VEHICLE_NAME environment variable not set"
        rospy.init_node("lane_control", anonymous=True)
        rospy.Subscriber(LANE_FILTER_NODE, LanePose, self.lane_pose_cb)

        # Let intersection control node receive car_cmd if enabled
        car_cmd_topic = (
            INTERSECTION_CONTROL_TOPIC if INTERSECTION_CONTROL else LANE_CONTROL_TOPIC
        )
        self.pub_car_cmd = rospy.Publisher(
            car_cmd_topic,
            Twist2DStamped,
            queue_size=10,
        )

        self.velocity = self.VELOCITY_DEF

        # PID Controllers
        self.lane_position_pid = LanePositionPID()
        self.lane_angle_pid = LaneAnglePID()

        # Update Counter
        self.update_counter = 0


    def update_velocity(self):
        temp_velocity = self.velocity
        self.velocity = rospy.get_param(
            f"/{DUCKIEBOT}/lane_control_node/velocity", self.VELOCITY_DEF
        )
        if temp_velocity != self.velocity:
            rospy.logwarn(f"Lane Control Velocity Updated: {self.velocity}")

    def should_update(self):
        if self.update_counter >= self.UPDATE_THRESHOLD:
            self.update_counter = 0
            return True
        else:
            self.update_counter += 1
            return False

    def lane_pose_cb(self, msg):
        if self.should_update():
            # Update PID params
            self.lane_position_pid.update_pid_params()
            self.lane_angle_pid.update_pid_params()
            # Update velocity from param server
            self.update_velocity()

        # Get PID outputs
        pid_v = self.lane_position_pid.add_error(msg.d, msg.header.stamp)
        pid_o = self.lane_angle_pid.add_error(msg.phi, msg.header.stamp)

        

        # Publish car command ROS message
        car_cmd_msg = Twist2DStamped()
        car_cmd_msg.v = self.velocity
        car_cmd_msg.omega = pid_v + pid_o
        # Set timestamp for intersection FSM
        car_cmd_msg.header.stamp = rospy.Time.now()
        self.pub_car_cmd.publish(car_cmd_msg)


if __name__ == "__main__":
    LaneControl()
    rospy.spin()
