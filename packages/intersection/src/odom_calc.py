#!/usr/bin/env python3
import os
import rospy
from geometry_msgs.msg import Pose2D
from duckietown_msgs.msg import WheelEncoderStamped
import numpy as np


DUCKIEBOT = os.environ.get("VEHICLE_NAME")

N = 135 # A constant number
R = 0.0318 # Wheen radius
b_w2w = 0.1 # Meters
alpha = 2 * np.pi / N


class OdomCalc:
    # Initialize left and right turns and ticks
    def __init__(self):
        rospy.init_node('odom_calc', anonymous=True)
        rospy.Subscriber(f"/{DUCKIEBOT}/left_wheel_encoder_node/tick", WheelEncoderStamped, self.put_left)
        rospy.Subscriber(f"/{DUCKIEBOT}/right_wheel_encoder_node/tick", WheelEncoderStamped, self.put_right)
        self.left_measures = []
        self.right_measures = []
        self.pub = rospy.Publisher("pose", Pose2D, queue_size=10)
        self.last_ltick = 0
        self.last_rtick = 0
        
        
        self.x = 0
        self.y = 0
        self.theta = 0
        rate = rospy.Rate(10)
        
        while not rospy.is_shutdown():
            if self.left_measures and self.right_measures:
                lticks = self.left_measures.pop()
                rticks = self.right_measures.pop()
                self.do_calculations(lticks, rticks)
            rate.sleep()
        
    def put_left(self, msg):
        self.left_measures.append(msg.data)
        
    def put_right(self, msg):
        self.right_measures.append(msg.data)

    # Calculate ticks and lengths for open loop turns
    def do_calculations(self, cticksl, cticksr):
        lticks = cticksl - self.last_ltick
        rticks = cticksr - self.last_rtick
        
        l_dist = lticks*alpha*R
        r_dist = rticks*alpha*R
        dist = (l_dist + r_dist) / 2.0
        dtheta = (r_dist - l_dist) / b_w2w
        dx = dist * np.cos(self.theta + dtheta/2.0)
        dy = dist * np.sin(self.theta + dtheta/2.0)
        self.x += dx
        self.y += dy
        self.theta += dtheta
        
        newpos = Pose2D()
        newpos.x = self.x
        newpos.y = self.y
        newpos.theta = self.theta
        self.pub.publish(newpos)
        
        self.last_ltick = cticksl
        self.last_rtick = cticksr
        
        
if __name__ == '__main__':
    oc = OdomCalc()