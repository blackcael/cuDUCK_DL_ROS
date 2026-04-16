#!/usr/bin/env python3

# StopLineReading
#
# std_msgs/Header header
#   uint32 seq
#   time stamp
#   string frame_id
# bool stop_line_detected
# bool at_stop_line
# geometry_msgs/Point stop_line_point
#   float64 x
#   float64 y
#   float64 z


import rospy
import os
from enum import Enum

from duckietown_msgs.msg import (
    StopLineReading,
    BoolStamped,
    Twist2DStamped,
    AprilTagsWithInfos,
)
from sensor_msgs.msg import Range

from IntersectionFSM import IntersectionFSM

DUCKIEBOT = os.environ.get("VEHICLE_NAME")


class State(Enum):
    DRIVING = 1
    STOPPED_AT_INT = 2
    NAVIGATING_INT = 3
    STOPPING_BEHIND_BOT = 4


class IntersectionNode:
    def __init__(self):
        assert DUCKIEBOT is not None, "VEHICLE_NAME environment variable not set"

        # Init Node
        rospy.init_node("IntersectionFSM", anonymous=True)
        rospy.Subscriber(
            f"/{DUCKIEBOT}/intersectionFSM_node/car_cmd",
            Twist2DStamped,
            self.car_cmd_cb,
        )
        # Subscriptions
        # Debug subscribe - gets more information about stop line
        rospy.Subscriber(
            f"/{DUCKIEBOT}/stop_line_filter_node/stop_line_reading",
            StopLineReading,
            self.stop_line_cb,
        )
        rospy.Subscriber(
            f"/{DUCKIEBOT}/stop_line_filter_node/at_stop_line",
            BoolStamped,
            self.at_stop_line_cb,
        )
        rospy.Subscriber(
            f"/{DUCKIEBOT}/apriltag_postprocessing_node/apriltags_out",
            AprilTagsWithInfos,
            self.april_tag_cb,
        )
        rospy.Subscriber(
            f"/vehicle_detection/detection",
            BoolStamped,
            self.detection_callback
        )

        # We need another node which handles duckiebot following/collision avoidance
        # This node will subsribe to that node just like stop_line_filter_node

        # Publishers
        self.pub_car_cmd = rospy.Publisher(
            f"/{DUCKIEBOT}/lane_controller_node/car_cmd",
            Twist2DStamped,
            queue_size=10,
        )

        # Compensate for Bad Trim
        if DUCKIEBOT == "turbogoose":
            rospy.set_param(f"/{DUCKIEBOT}/kinematics_node/trim", -0.15)

        self.intersection_fsm = IntersectionFSM()

    # Call Backs
    def detection_callback(self, msg):
        self.intersection_fsm.add_range_reading(msg.data)

    def car_cmd_cb(self, msg):
        # rospy.logwarn(
        #     f"Current State: {self.intersection_fsm.get_current_state().name}"
        # )
        msg.v, msg.omega = self.intersection_fsm.tick_fsm_loop(
            msg.v, msg.omega, msg.header.stamp.to_sec()
        )
        self.pub_car_cmd.publish(msg)

    def stop_line_cb(self, msg):
        debug = rospy.get_param("stopline_debug", False)
        if debug: 
            rospy.logwarn(f"STOPLINE_data: {msg}")

    def at_stop_line_cb(self, msg):
        self.intersection_fsm.add_stop_line_reading(msg.data)
        # rospy.logwarn(f"AT_STOP_LINE: {msg.data}")

    def april_tag_cb(self, msg):
        detection_array = msg.detections
        detected_IDs_list = []
        for detection in detection_array:
            detected_id = detection.tag_id
            if detected_id != None:
                detected_IDs_list.append(detected_id)
        # rospy.logwarn(f"Detected April Tags: {detected_IDs_list}")
        self.intersection_fsm.update_april_tags(detected_IDs_list)


if __name__ == "__main__":
    intersection_node = IntersectionNode()
    rospy.spin()
