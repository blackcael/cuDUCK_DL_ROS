#!/usr/bin/env python3
#!/usr/bin/env python3
import rospy
import math

from duckietown_msgs.msg import WheelEncoderStamped
from odometry.msg import Pose2D


class OdometryCalcRobot:
    BASELINE_WHEEL2WHEEL = 0.1
    RADIUS = 0.0318
    TOTAL_TICKS = 135
    WHEEL_ROTATION_PER_TICK = 2 * math.pi / TOTAL_TICKS

    def __init__(self):
        rospy.init_node("calculate_odometry_robot", anonymous=True)

        # Subscribe to the robot wheel encoder tick topics
        rospy.Subscriber(
            "/yoshi/left_wheel_encoder_node/tick",
            WheelEncoderStamped,
            self.read_left_wheel_ticks,
        )

        rospy.Subscriber(
            "/yoshi/right_wheel_encoder_node/tick",
            WheelEncoderStamped,
            self.read_right_wheel_ticks,
        )

        # Publishes to a topic
        self.pose_publisher = rospy.Publisher("pose", Pose2D, queue_size=10)

        # Keep track of current and previous ticks
        self.current_tick_left = None
        self.current_tick_right = None
        self.last_tick_left = 0
        self.last_tick_right = 0

        # Odometry Calculation
        self.distance_left = 0
        self.distance_right = 0
        self.current_pose = Pose2D(0, 0, 0)

    def read_left_wheel_ticks(self, tick_message: WheelEncoderStamped):
        self.current_tick_left = tick_message.data
        if self.current_tick_right is not None:
            self.publish()

    def read_right_wheel_ticks(self, tick_message: WheelEncoderStamped):
        self.current_tick_right = tick_message.data
        if self.current_tick_left is not None:
            self.publish()

    def publish(self):
        self.calc_pose()
        self.pose_publisher.publish(self.current_pose)

        self.current_tick_left = None
        self.current_tick_right = None

    def calc_pose(self):
        delta_ticks_left = self.current_tick_left - self.last_tick_left
        delta_ticks_right = self.current_tick_right - self.last_tick_right

        delta_wheel_distance_left = (
            OdometryCalcRobot.WHEEL_ROTATION_PER_TICK * delta_ticks_left
        )
        delta_wheel_distance_right = (
            OdometryCalcRobot.WHEEL_ROTATION_PER_TICK * delta_ticks_right
        )

        self.distance_left = OdometryCalcRobot.RADIUS * delta_wheel_distance_left
        self.distance_right = OdometryCalcRobot.RADIUS * delta_wheel_distance_right

        total_dist = (self.distance_right + self.distance_left) / 2
        d_theta = (
            self.distance_right - self.distance_left
        ) / OdometryCalcRobot.BASELINE_WHEEL2WHEEL

        self.current_pose.x += total_dist * math.cos(
            self.current_pose.theta + d_theta / 2
        )
        self.current_pose.y += total_dist * math.sin(
            self.current_pose.theta + d_theta / 2
        )
        self.current_pose.theta += d_theta

        # Save last tick and clear current tick
        self.last_tick_left = self.current_tick_left
        self.last_tick_right = self.current_tick_right
        self.current_tick_left = None
        self.current_tick_right = None


if __name__ == "__main__":
    try:
        OdometryCalcRobot()
        while not rospy.is_shutdown():
            pass
    except rospy.ROSInterruptException:
        pass

# https://prod.liveshare.vsengsaas.visualstudio.com/join?DCEE68F3C2779357381BA7B360C4F1E7336C
