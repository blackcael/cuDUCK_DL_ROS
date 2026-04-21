import rospy
import cv2
import numpy as np
import math
import os
import torch

from sensor_msgs.msg import Image, CompressedImage
from duckietown_msgs.msg import Twist2DStamped


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

        # Subscribers
        rospy.Subscriber(
            CompressedImage,
            self.dl_callback,
            queue_size=1,
            buff_size=2**24,
        )

        # Publishers
        self.pub_car_cmd = rospy.Publisher(
            WHEELS_TOPIC,
            Twist2DStamped,
            queue_size=10,
        )

        # Load Model


        # Compensate for Bad Trim
        # if DUCKIEBOT == "turbogoose":
        #     rospy.set_param(f"/{DUCKIEBOT}/kinematics_node/trim", -0.15)

    # Call Backs
    def dl_callback(self, compressed_img_msg){
        img = self.bridge.compressed_imgmsg_to_cv2(compressed_img_msg, "bgr8")
        new_image = cv2.resize(img, self.image_size , interpolation=cv2.INTER_NEAREST)
        wheels_cmd = self.get_wheels_commands_from_image(compressed_img_msg)
        self.pub(wheels_cmd)
    }

    def angle_from_logits(self, logits):
        pass

    def msg_from_angle(self, angle):
        pass


    def get_wheels_commands_from_image(self, img)
        # 1) Pass image through the model (returns logits)
        logits = self.model(img)
        # 2) Convert Logits into Directions
        v_l, v_r = self.angle_from_logits(logits)
        # 3) Convert Angle into Message
        wheels_cmd_msg = self.msg_from_angle(v_l, v_r)
        return wheels_cmd_msg


if __name__ == "__main__":
    dl_drive_node = DL_Drive_Node()
    rospy.spin()
