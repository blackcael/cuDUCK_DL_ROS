#!/usr/bin/env python3
#!/usr/bin/env python3
import rospy
import math
import os

from duckietown_msgs.msg import WheelEncoderStamped, Twist2DStamped

# std_msgs/Header header
#   uint32 seq
#   time stamp
#   string frame_id
# float32 v
# float32 omega


ROBOT_NAME = os.environ.get("VEHICLE_NAME")


class LShape:
    VEL = 5
    STRAIGHT_TIME = rospy.Duration(2)
    TURN_TIME = rospy.Duration(1)

    TURN_ANGLE = math.pi / 2

    STRAIGHT = 1
    TURN = 2

    def __init__(self):
        rospy.init_node("LShapeControl", anonymous=True)

        # Publishes to a topic
        self.publisher = rospy.Publisher(
            f"/{ROBOT_NAME}/lane_controller_node/car_cmd", Twist2DStamped, queue_size=10
        )
        # self.rate = rospy.Rate(10)
        self.current_tick = 0
        self.cmd = Twist2DStamped()
        self.start_time = rospy.Time.now()

        self.state = LShape.STRAIGHT
        self.publish()

    def add_header(self):
        self.cmd.header.seq = self.current_tick
        self.cmd.header.stamp = rospy.Time.now()
        self.cmd.header.frame_id = "LShape_cmd"
        self.current_tick += 1

    def change_state(self):
        if self.state == LShape.STRAIGHT:
            rospy.sleep(LShape.STRAIGHT_TIME)
            self.state = LShape.TURN
        elif self.state == LShape.TURN:
            rospy.sleep(LShape.TURN_TIME)
            self.state = LShape.STRAIGHT
        else:
            raise RuntimeError("Invalid LShape State")

    def publish(self):
        while not rospy.is_shutdown():
            self.change_state()
            self.add_header()
            if self.state == LShape.STRAIGHT:
                self.cmd.v = LShape.VEL
                self.cmd.omega = 0
            elif self.state == LShape.TURN:
                self.cmd.v = 0
                self.cmd.omega = LShape.TURN_ANGLE

            self.publisher.publish(self.cmd)


if __name__ == "__main__":
    try:
        LShape()
    except rospy.ROSInterruptException:
        pass

# https://prod.liveshare.vsengsaas.visualstudio.com/join?ECE96F07E35CC1E3C2BB7215805BB6BB8208
