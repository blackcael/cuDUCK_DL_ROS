#!/usr/bin/env python3

import rospy
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class MaskNode:
    def __init__(self):
        rospy.init_node("mask", anonymous=True)

        # Make sure the / namespace is correct in "/image"
        rospy.Subscriber("/image", Image, self.cb_manager)
        self.pub_cropped = rospy.Publisher("/image_cropped", Image, queue_size=10)
        self.pub_white = rospy.Publisher("/image_white", Image, queue_size=10)
        self.pub_yellow = rospy.Publisher("/image_yellow", Image, queue_size=10)

        # Instantiate the converter class once by using a class member
        self.bridge = CvBridge()
        self.cropped_image_hsv = None

    @staticmethod
    def convert_hsv(image):
        return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    def ros_msg_to_openCV(self, msg, type: str):
        return self.bridge.imgmsg_to_cv2(msg, type)

    def openCV_to_ros_msg(self, image, type: str):
        return self.bridge.cv2_to_imgmsg(image, type)

    def cb_manager(self, msg):
        self.crop_cb(msg)
        self.filter_yellow()
        self.filter_white()

    def crop_cb(self, msg):
        # convert to a OpenCV image using the bridge
        cv_img = self.ros_msg_to_openCV(msg, "bgr8")

        # Crop half of the pixels in y dimension
        # Numpy operations because cv_img is really a numpy array
        half_y_idx = cv_img.shape[0] // 2
        cv_cropped = cv_img[half_y_idx:, :]

        # convert new image to ROS to send
        cropped_img_msg = self.openCV_to_ros_msg(cv_cropped, "bgr8")

        # publish cropped image
        self.pub_cropped.publish(cropped_img_msg)

        # convert cropped image to hsv
        self.cropped_image_hsv = self.convert_hsv(cv_cropped)

    def filter_yellow(self):
        # TODO: Use erode or dilate
        image_yellow = cv2.inRange(
            self.cropped_image_hsv, (12, 50, 140), (28, 180, 255)
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        image_yellow = cv2.dilate(image_yellow, kernel)
        msg = self.openCV_to_ros_msg(image_yellow, "8UC1")
        self.pub_yellow.publish(msg)

    def filter_white(self):
        # TODO: Use erode or dilate
        image = cv2.inRange(self.cropped_image_hsv, (65, 0, 145), (150, 100, 255))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        image = cv2.erode(image, kernel)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        image = cv2.dilate(image, kernel)
        msg = self.openCV_to_ros_msg(image, "8UC1")
        self.pub_white.publish(msg)


if __name__ == "__main__":
    # initialize our node and create a publisher as normal
    img_flip = MaskNode()
    rospy.spin()

# https://prod.liveshare.vsengsaas.visualstudio.com/join?7E5CFE8D706D01C7EFA7552431552196D1EB
