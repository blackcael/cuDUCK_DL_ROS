#!/usr/bin/env python3

import rospy
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge
import numpy as np
import cv2
import matplotlib.pyplot as plt

class TimedImageInspector:
    def __init__(self):
        rospy.init_node("image_inspector", anonymous=True)

        self.bridge = CvBridge()
        self.latest_image = None

        self.sample_images = False
        if self.sample_images:
            msg_type = Image
        else:
            msg_type = CompressedImage

        # Subscribe to camera topic
        self.sub = rospy.Subscriber("camera_node/image/compressed", msg_type, self.image_callback)

        # Create a timer to call self.timer_callback every 10 seconds
        self.timer = rospy.Timer(rospy.Duration(10.0), self.timer_callback)
        rospy.loginfo("Timed Image Inspector started. Will display an image every 10 seconds.")

    def image_callback(self, msg):
        if self.sample_images:
            # Convert ROS Image to OpenCV BGR format
            self.latest_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        else:
            try:
                np_arr = np.frombuffer(msg.data, np.uint8)
                self.latest_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                rospy.loginfo("Received and decoded compressed image.")
            except Exception as e:
                rospy.logerr(f"Failed to decode image: {e}")

    def timer_callback(self, event):
        if self.latest_image is None:
            rospy.logwarn("No image received yet, skipping this cycle.")
            return

        bgr = self.latest_image
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        # Show both original and HSV images
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].imshow(rgb)
        axes[0].set_title("Original (RGB)")
        axes[0].axis("off")

        axes[1].imshow(hsv)
        axes[1].set_title("HSV plotted as RGB")
        axes[1].axis("off")

        plt.tight_layout()
        plt.show(block=False)  # Don't block execution
        plt.pause(9)           # Keep open for 9 seconds
        plt.close(fig)         # Close figure to prevent memory buildup

if __name__ == "__main__":
    try:
        inspector = TimedImageInspector()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
