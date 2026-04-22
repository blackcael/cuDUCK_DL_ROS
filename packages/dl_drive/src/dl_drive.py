#!/usr/bin/env python3

import rospy
import os
import sys
import time
import torch

from sensor_msgs.msg import CompressedImage
from duckietown_msgs.msg import WheelsCmdStamped
from cv_bridge import CvBridge

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from helper_functions import steering_bin_to_wheel_cmd
from model_loader import load_model_from_ros_params, preprocess_bgr_image

DUCKIEBOT = os.environ.get("VEHICLE_NAME")

CAMERA_TOPIC = f"/{DUCKIEBOT}/camera_node/image/compressed"
WHEELS_TOPIC = f"/{DUCKIEBOT}/wheels_driver_node/wheels_cmd"


class DL_Drive_Node:
    def __init__(self):
        assert DUCKIEBOT is not None, "VEHICLE_NAME environment variable not set"

        # Init Node
        rospy.init_node("dl_drive", anonymous=True)

        # Class Variables
        self.bridge = CvBridge()
        self.image_size = (32,32)
        loaded = load_model_from_ros_params()
        self.model = loaded.model
        self.device = loaded.device
        self.image_size = loaded.image_size
        self.model_input_channels = loaded.model_input_channels

        # Subscribers
        rospy.Subscriber(
            CAMERA_TOPIC,
            CompressedImage,
            self.dl_callback,
            queue_size=1,
            buff_size=2**24,
        )

        # Publishers
        self.pub_car_cmd = rospy.Publisher(
            WHEELS_TOPIC,
            WheelsCmdStamped,
            queue_size=10,
        )

        # Compensate for Bad Trim
        # if DUCKIEBOT == "turbogoose":
        #     rospy.set_param(f"/{DUCKIEBOT}/kinematics_node/trim", -0.15)

    # Call Backs
    def dl_callback(self, compressed_img_msg):
        img = self.bridge.compressed_imgmsg_to_cv2(compressed_img_msg, "bgr8")
        wheels_cmd = self.get_wheels_commands_from_image(img)
        self.pub_car_cmd.publish(wheels_cmd)

    def angle_from_logits(self, logits):
        return steering_bin_to_wheel_cmd(logits)

    def msg_from_angle(self, v_l, v_r):
        wheels_cmd = WheelsCmdStamped()
        wheels_cmd.header.stamp = rospy.Time.now()
        wheels_cmd.vel_left = float(v_l.item() if torch.is_tensor(v_l) else v_l)
        wheels_cmd.vel_right = float(v_r.item() if torch.is_tensor(v_r) else v_r)
        return wheels_cmd


    def get_wheels_commands_from_image(self, img):
        # 1) Preprocess image and run the model
        model_input = preprocess_bgr_image(
            img,
            self.image_size,
            self.model_input_channels,
            self.device,
        )
        with torch.no_grad():
            inference_start = time.perf_counter()
            logits = self.model(model_input)
            inference_ms = (time.perf_counter() - inference_start) * 1000.0
        rospy.logwarn("REALTIME: dl_drive model inference time: %.3f ms", inference_ms)
        # 2) Convert Logits into Directions
        v_l, v_r = steering_bin_to_wheel_cmd(logits)
        # 3) Convert Angle into Message
        wheels_cmd_msg = self.msg_from_angle(v_l, v_r)
        return wheels_cmd_msg


if __name__ == "__main__":
    dl_drive_node = DL_Drive_Node()
    rospy.spin()
