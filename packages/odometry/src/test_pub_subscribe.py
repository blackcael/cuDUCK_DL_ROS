#!/usr/bin/env python3
#!/usr/bin/env python3
import rospy
import math

# from std_msgs.msg import String
from odometry.msg import WheelTicks
from odometry.msg import Pose2D


class OdometryCalc:
    BASELINE_WHEEL2WHEEL = 0.1
    RADIUS = 0.0318
    TOTAL_TICKS = 135
    WHEEL_ROTATION_PER_TICK = 2 * math.pi / TOTAL_TICKS

    def __init__(self):
        # Creates a node with name 'subscriber_cmd_vel' and make sure it is a
        # unique node (using anonymous=True).
        rospy.init_node("calculate_odometry", anonymous=True)

        # Subscriber which will subscribe to the topic '/turtle1/cmd_vel'.
        self.velocity_subscriber = rospy.Subscriber(
            "dist_wheel", WheelTicks, self.read_wheel_ticks
        )

        # Publishes to a topic
        self.pose_publisher = rospy.Publisher("pose", Pose2D, queue_size=10)

        self.delta_ticks_left = 0
        self.delta_ticks_right = 0
        self.distance_left = 0
        self.distance_right = 0
        self.current_pose = Pose2D(0, 0, 0)

    def read_wheel_ticks(self, tick_message: WheelTicks):
        self.delta_ticks_left = tick_message.wheel_ticks_left
        self.delta_ticks_right = tick_message.wheel_ticks_right
        self.publish()

    def publish(self):
        self.calc_pose()
        self.pose_publisher.publish(self.current_pose)

    def calc_pose(self):
        delta_wheel_distance_left = (
            OdometryCalc.WHEEL_ROTATION_PER_TICK * self.delta_ticks_left
        )
        delta_wheel_distance_right = (
            OdometryCalc.WHEEL_ROTATION_PER_TICK * self.delta_ticks_right
        )

        self.distance_left = OdometryCalc.RADIUS * delta_wheel_distance_left
        self.distance_right = OdometryCalc.RADIUS * delta_wheel_distance_right

        total_dist = (self.distance_right + self.distance_left) / 2
        d_theta = (
            self.distance_right - self.distance_left
        ) / OdometryCalc.BASELINE_WHEEL2WHEEL

        self.current_pose.x += total_dist * math.cos(
            self.current_pose.theta + d_theta / 2
        )
        self.current_pose.y += total_dist * math.sin(
            self.current_pose.theta + d_theta / 2
        )
        self.current_pose.theta += d_theta


if __name__ == "__main__":
    try:
        OdometryCalc()
        while not rospy.is_shutdown():
            pass
    except rospy.ROSInterruptException:
        pass

# https://prod.liveshare.vsengsaas.visualstudio.com/join?DCEE68F3C2779357381BA7B360C4F1E7336C
