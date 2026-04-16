#!/usr/bin/env python3

import rospy
import cv2
import numpy as np
import math
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class MaskNode:
    def __init__(self):
        rospy.init_node("hough_lines", anonymous=True)

        # Make sure the / namespace is correct in "/image"
        rospy.Subscriber("/image_cropped", Image, self.cb_img_cropped)

        rospy.Subscriber("/image_white", Image, self.cb_img_white)
        rospy.Subscriber("/image_yellow", Image, self.cb_img_yellow)
        self.pub_canny = rospy.Publisher("/image_edges", Image, queue_size=10)
        self.pub_white = rospy.Publisher("/image_lines_white", Image, queue_size=10)
        self.pub_yellow = rospy.Publisher("/image_lines_yellow", Image, queue_size=10)

        # Instantiate the converter class once by using a class members
        self.image_cropped = None
        self.bridge = CvBridge()
        self.canny_edge_img = None

    @staticmethod
    def bgr_to_hsv(image):
        return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    def ros_msg_to_openCV(self, msg, type: str):
        return self.bridge.imgmsg_to_cv2(msg, type)

    def openCV_to_ros_msg(self, image, type: str):
        return self.bridge.cv2_to_imgmsg(image, type)

    def cb_img_cropped(self, msg):
        self.image_cropped = self.ros_msg_to_openCV(msg, "bgr8")
        self.canny_edge_img = self.canny_edge(self.image_cropped)
        msg = self.openCV_to_ros_msg(self.canny_edge_img, "8UC1")
        self.pub_canny.publish(msg)

    # Call back to get white regions of image
    def cb_img_white(self, msg):
        image = self.ros_msg_to_openCV(msg, "8UC1")
        combined = self.combine_canny(image)
        lines = cv2.HoughLinesP(combined, rho=1, theta=math.pi / 180, threshold=15)

        lined_image = self.output_lines(self.image_cropped, lines)

        msg = self.openCV_to_ros_msg(lined_image, "bgr8")
        self.pub_white.publish(msg)

    # Call back to get yellow regions of image
    def cb_img_yellow(self, msg):
        image = self.ros_msg_to_openCV(msg, "8UC1")
        combined = self.combine_canny(image)
        lines = cv2.HoughLinesP(combined, rho=1, theta=math.pi / 180, threshold=5)

        lined_image = self.output_lines(self.image_cropped, lines)

        msg = self.openCV_to_ros_msg(lined_image, "bgr8")
        self.pub_yellow.publish(msg)

    def combine_canny(self, image):
        canny_edge = self.canny_edge(image)
        return cv2.bitwise_and(canny_edge, image)

    # Output lines to final image
    def output_lines(self, original_image, lines):
        output = np.copy(original_image)
        if lines is not None:
            for i in range(len(lines)):
                l = lines[i][0]
                cv2.line(
                    output, (l[0], l[1]), (l[2], l[3]), (255, 0, 0), 2, cv2.LINE_AA
                )
                cv2.circle(output, (l[0], l[1]), 2, (0, 255, 0))
                cv2.circle(output, (l[2], l[3]), 2, (0, 0, 255))

        return output

    def canny_edge(self, image):
        image_edge = cv2.Canny(image, 200, 300)
        return image_edge


if __name__ == "__main__":
    # initialize our node and create a publisher as normal
    img_flip = MaskNode()
    rospy.spin()
