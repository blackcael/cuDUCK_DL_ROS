#!/usr/bin/env python3

import rospy
import cv2
import numpy as np
import math
import os

from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge
from std_srvs.srv import SetBool, SetBoolResponse
from duckietown_msgs.msg import SegmentList, Segment, Vector2D

ROBOT_NAME = os.environ.get("VEHICLE_NAME")
PARAM_NAME_SPACE = f"/{ROBOT_NAME}/masks_params"
COLOR_FILTER_NS = f"/{ROBOT_NAME}/color_filter_params"


class GroundProjection:
    DEBUG_DEF = False
    WMINH_DEF = 0
    WMINS_DEF = 0
    WMINV_DEF = 120
    WMAXH_DEF = 180
    WMAXS_DEF = 80
    WMAXV_DEF = 255
    WHL_THRESHOLD_DEF = 2
    WHL_MLL_DEF = 8
    WHL_MLG_DEF = 8

    YMINH_DEF = 12
    YMINS_DEF = 50
    YMINV_DEF = 140
    YMAXH_DEF = 28
    YMAXS_DEF = 180
    YMAXV_DEF = 255
    YHL_THRESHOLD_DEF = 2
    YHL_MLL_DEF = 8
    YHL_MLG_DEF = 8

    def __init__(self):
        rospy.init_node("ground_projection", anonymous=True)

        # Class variables
        self.bridge = CvBridge()

        # Subscribers and Publishers
        rospy.Subscriber(
            f"/{ROBOT_NAME}/camera_node/image/compressed",
            CompressedImage,
            self.callback,
            queue_size=1,
            buff_size=2**24,
        )
        self.pub = rospy.Publisher(
            f"/{ROBOT_NAME}/line_detector_node/segment_list", SegmentList, queue_size=1
        )
        self.red_rho = 1
        self.red_threshold = 15
        self.red_minLineLength = 5
        self.red_maxLineGap = 15

        # White default params
        self.debug = GroundProjection.DEBUG_DEF
        self.wminh = GroundProjection.WMINH_DEF
        self.wmins = GroundProjection.WMINS_DEF
        self.wminv = GroundProjection.WMINV_DEF
        self.wmaxh = GroundProjection.WMAXH_DEF
        self.wmaxs = GroundProjection.WMAXS_DEF
        self.wmaxv = GroundProjection.WMAXV_DEF
        self.wHL_threshold = GroundProjection.WHL_THRESHOLD_DEF
        self.wHL_mll = GroundProjection.WHL_MLL_DEF
        self.wHL_mlg = GroundProjection.WHL_MLG_DEF

        # Yellow default params
        self.yminh = GroundProjection.YMINH_DEF
        self.ymins = GroundProjection.YMINS_DEF
        self.yminv = GroundProjection.YMINV_DEF
        self.ymaxh = GroundProjection.YMAXH_DEF
        self.ymaxs = GroundProjection.YMAXS_DEF
        self.ymaxv = GroundProjection.YMAXV_DEF
        self.yHL_threshold = GroundProjection.YHL_THRESHOLD_DEF
        self.yHL_mll = GroundProjection.YHL_MLL_DEF
        self.yHL_mlg = GroundProjection.YHL_MLG_DEF
        self.load_color_params()

        ############## DEBUG PUBLISHERS ##############
        self.debug_pub_white = rospy.Publisher(
            f"/{ROBOT_NAME}/debug_white", Image, queue_size=1
        )
        self.debug_pub_yellow = rospy.Publisher(
            f"/{ROBOT_NAME}/debug_yellow", Image, queue_size=1
        )
        self.debug_pub_bit_white = rospy.Publisher(
            f"/{ROBOT_NAME}/debug_bit_white", Image, queue_size=1
        )
        self.debug_pub_bit_yellow = rospy.Publisher(
            f"/{ROBOT_NAME}/debug_bit_yellow", Image, queue_size=1
        )
        # self.debug_pub_gray = rospy.Publisher(
        #     f"/{ROBOT_NAME}/debug_gray", Image, queue_size=1
        # )
        self.debug_pub_edges = rospy.Publisher(
            f"/{ROBOT_NAME}/debug_edges", Image, queue_size=1
        )
        ##############################################

        rospy.Service("line_detector_node/switch", SetBool, self.ld_switch)
        rospy.Service("lane_filter_node/switch", SetBool, self.lf_switch)

    def decompress_image(self, compressed_img_msg):
        return self.bridge.compressed_imgmsg_to_cv2(compressed_img_msg, "bgr8")

    def update_params(self):
        self.red_rho = rospy.get_param(f"{PARAM_NAME_SPACE}/red_rho", self.red_rho)
        self.red_threshold = rospy.get_param(
            f"{PARAM_NAME_SPACE}/red_thresh", self.red_rho
        )
        self.red_minLineLength = rospy.get_param(
            f"{PARAM_NAME_SPACE}/red_minLineLength", self.red_rho
        )
        self.red_maxLineGap = rospy.get_param(
            f"{PARAM_NAME_SPACE}/red_maxLineGap", self.red_rho
        )

    def lf_switch(self, msg):
        return True, ""

    def ld_switch(self, msg):
        return True, ""

    def check_debug_param(self):
        debug_t = self.debug
        self.debug = rospy.get_param(COLOR_FILTER_NS + "/debug_color", False)
        if debug_t != self.debug:
            rospy.logwarn(f"Ground Projection Debug Mode: {self.debug}")

    # Parameters for HSV values for color filtering
    def load_color_params(self):
        (
            wminh_t,
            wmins_t,
            wminv_t,
            wmaxh_t,
            wmaxs_t,
            wmaxv_t,
            wHL_threshold_t,
            wHL_mll_t,
            wHL_mlg_t,
            yminh_t,
            ymins_t,
            yminv_t,
            ymaxh_t,
            ymaxs_t,
            ymaxv_t,
            yHL_threshold_t,
            yHL_mll_t,
            yHL_mlg_t
        ) = (
            self.wminh,
            self.wmins,
            self.wminv,
            self.wmaxh,
            self.wmaxs,
            self.wmaxv,
            self.wHL_threshold,
            self.wHL_mll,
            self.wHL_mlg,
            self.yminh,
            self.ymins,
            self.yminv,
            self.ymaxh,
            self.ymaxs,
            self.ymaxv,
            self.yHL_threshold,
            self.yHL_mll,
            self.yHL_mlg,
        )

        # Get White params
        self.wminh = rospy.get_param(
            COLOR_FILTER_NS + "/wminh", GroundProjection.WMINH_DEF
        )
        self.wmins = rospy.get_param(
            COLOR_FILTER_NS + "/wmins", GroundProjection.WMINS_DEF
        )
        self.wminv = rospy.get_param(
            COLOR_FILTER_NS + "/wminv", GroundProjection.WMINV_DEF
        )
        self.wmaxh = rospy.get_param(
            COLOR_FILTER_NS + "/wmaxh", GroundProjection.WMAXH_DEF
        )
        self.wmaxs = rospy.get_param(
            COLOR_FILTER_NS + "/wmaxs", GroundProjection.WMAXS_DEF
        )
        self.wmaxv = rospy.get_param(
            COLOR_FILTER_NS + "/wmaxv", GroundProjection.WMAXV_DEF
        )
        self.wHL_threshold = rospy.get_param(
            COLOR_FILTER_NS + "/wHL_threshold", GroundProjection.WHL_THRESHOLD_DEF
        )
        self.wHL_mll = rospy.get_param(
            COLOR_FILTER_NS + "/wHL_mll", GroundProjection.WHL_MLL_DEF
        )
        self.wHL_mlg = rospy.get_param(
            COLOR_FILTER_NS + "/wHL_mlg", GroundProjection.WHL_MLG_DEF
        )

        # Get Yellow params
        self.yminh = rospy.get_param(
            COLOR_FILTER_NS + "/yminh", GroundProjection.YMINH_DEF
        )
        self.ymins = rospy.get_param(
            COLOR_FILTER_NS + "/ymins", GroundProjection.YMINS_DEF
        )
        self.yminv = rospy.get_param(
            COLOR_FILTER_NS + "/yminv", GroundProjection.YMINV_DEF
        )
        self.ymaxh = rospy.get_param(
            COLOR_FILTER_NS + "/ymaxh", GroundProjection.YMAXH_DEF
        )
        self.ymaxs = rospy.get_param(
            COLOR_FILTER_NS + "/ymaxs", GroundProjection.YMAXS_DEF
        )
        self.ymaxv = rospy.get_param(
            COLOR_FILTER_NS + "/ymaxv", GroundProjection.YMAXV_DEF
        )
        self.yHL_threshold = rospy.get_param(
            COLOR_FILTER_NS + "/yHL_threshold", GroundProjection.YHL_THRESHOLD_DEF
        )
        self.yHL_mll = rospy.get_param(
            COLOR_FILTER_NS + "/yHL_mll", GroundProjection.YHL_MLL_DEF
        )
        self.yHL_mlg = rospy.get_param(
            COLOR_FILTER_NS + "/yHL_mlg", GroundProjection.YHL_MLG_DEF
        )

        if (
            wminh_t != self.wminh
            or wmins_t != self.wmins
            or wminv_t != self.wminv
            or wmaxh_t != self.wmaxh
            or wmaxs_t != self.wmaxs
            or wmaxv_t != self.wmaxv
            or wHL_threshold_t != self.wHL_threshold
            or wHL_mll_t != self.wHL_mll
            or wHL_mlg_t != self.wHL_mlg
            or yminh_t != self.yminh
            or ymins_t != self.ymins
            or yminv_t != self.yminv
            or ymaxh_t != self.ymaxh
            or ymaxs_t != self.ymaxs
            or ymaxv_t != self.ymaxv
            or yHL_threshold_t != self.yHL_threshold
            or yHL_mll_t != self.yHL_mll
            or yHL_mlg_t != self.yHL_mlg

        ):
            rospy.logwarn(
                f"GP Yellow Filter Params: "
                f"yminh: {self.yminh}, ymins: {self.ymins}, yminv: {self.yminv}, "
                f"ymaxh: {self.ymaxh}, ymaxs: {self.ymaxs}, ymaxv: {self.ymaxv}, "
                f"yHL_thresh: {self.yHL_threshold}, yHL_mll: {self.yHL_mll}, yHL_mlg: {self.yHL_mlg}"
            )
            rospy.logwarn(
                f"GP White Filter Params: "
                f"wminh: {self.wminh}, wmins: {self.wmins}, wminv: {self.wminv}, "
                f"wmaxh: {self.wmaxh}, wmaxs: {self.wmaxs}, wmaxv: {self.wmaxv}"
                f"wHL_thresh: {self.wHL_threshold}, wHL_mll: {self.wHL_mll}, wHL_mlg: {self.wHL_mlg}"
            )

    def hough_transform(self, image, cropped_image_bgr):
        self.check_debug_param()
        if self.debug:
            self.load_color_params()

        # Filter for white and yellow
        # image_yellow = cv2.inRange(image, (12, 50, 140), (28, 180, 255)) # yoshi
        image_yellow = cv2.inRange(
            image,
            (self.yminh, self.ymins, self.yminv),
            (self.ymaxh, self.ymaxs, self.ymaxv),
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        image_yellow = cv2.dilate(image_yellow, kernel)

        image_white = cv2.inRange(
            image,
            (self.wminh, self.wmins, self.wminv),
            (self.wmaxh, self.wmaxs, self.wmaxv),
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        image_white = cv2.erode(image_white, kernel)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        image_white = cv2.dilate(image_white, kernel)
        image_white = cv2.dilate(image_white, kernel)  # Extra dilation

        # Filter out yellow pixels from white mask
        image_white = cv2.bitwise_and(image_white, cv2.bitwise_not(image_yellow))

        image_red_lower = cv2.inRange(image, (0, 70, 50), (15, 255, 255))
        image_red_upper = cv2.inRange(image, (165, 70, 80), (185, 255, 255))
        image_red = cv2.bitwise_or(image_red_lower, image_red_upper)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        image_red = cv2.dilate(image_red, kernel)

        ###### DEBUG PUBLISHERS ######
        img_mes = self.bridge.cv2_to_imgmsg(image_white, "8UC1")
        self.debug_pub_white.publish(img_mes)
        img_mes = self.bridge.cv2_to_imgmsg(image_yellow, "8UC1")
        self.debug_pub_yellow.publish(img_mes)
        ##############################

        # Find edges using Canny on filtered images
        # canny_edge_yellow = cv2.Canny(image_yellow, 170, 300)
        # canny_edge_white = cv2.Canny(image_white, 170, 300)

        gray_image = cv2.cvtColor(cropped_image_bgr, cv2.COLOR_BGR2GRAY)
        gray_image = cv2.GaussianBlur(gray_image, (5, 5), 0)

        ###### DEBUG PUBLISHERS ######
        # img_mes = self.bridge.cv2_to_imgmsg(gray_image, "8UC1")
        # self.debug_pub_gray.publish(img_mes)
        ##############################

        edges = cv2.Canny(gray_image, 10, 60)

        ###### DEBUG PUBLISHERS ######
        edges_msg = self.bridge.cv2_to_imgmsg(edges, "8UC1")
        self.debug_pub_edges.publish(edges_msg)
        ##############################

        ## Pass in the cropped image, blur the image, and find edges using Canny
        ## this gives all edges independent of color, bitwise AND with color filtered images later

        # Bitwise AND the each set of edges with the cropped image
        # bitwise_yellow = cv2.bitwise_and(canny_edge_yellow, image_yellow)
        # bitwise_white = cv2.bitwise_and(canny_edge_white, image_white)
        bitwise_yellow = cv2.bitwise_and(edges, image_yellow)
        bitwise_white = cv2.bitwise_and(edges, image_white)
        bitwise_red = cv2.bitwise_and(edges, image_red)

        # ###### DEBUG PUBLISHERS ######
        img_mes = self.bridge.cv2_to_imgmsg(bitwise_white, "8UC1")
        self.debug_pub_bit_white.publish(img_mes)
        img_mes = self.bridge.cv2_to_imgmsg(bitwise_yellow, "8UC1")
        self.debug_pub_bit_yellow.publish(img_mes)
        ##############################

        # Perform Hough Transform to find lines for each
        # rho=1, theta=math.pi/180, threshold = 15
        lines_white = cv2.HoughLinesP(
            bitwise_white,
            rho=1,
            theta=math.pi / 180,
            threshold=self.wHL_threshold,
            minLineLength=self.wHL_mll,
            maxLineGap=self.wHL_mlg,
        )
        lines_yellow = cv2.HoughLinesP(
            bitwise_yellow,
            rho=1,
            theta=math.pi / 180,
            threshold=self.yHL_threshold,
            minLineLength=self.yHL_mll,
            maxLineGap=self.yHL_mlg,
        )
        lines_red = cv2.HoughLinesP(
            bitwise_red,
            rho=self.red_rho,
            theta=math.pi / 180,
            threshold=self.red_threshold,
            minLineLength=self.red_minLineLength,
            maxLineGap=self.red_maxLineGap,
        )

        return lines_white, lines_yellow, lines_red

    def segments_from_lines(self, lines, color):
        # format lines for ground projection... into a segment type
        #    # Each has:
        #    #  color
        #    #  Vector2D(x, y) coordiantes normalized between 0 and 1
        # make a list of all segments
        # Reformat line segment from the Hough Transform
        # segments

        image_size = (160, 120)
        offset = 40

        # Normalize the pixel values to [0, 1]
        arr_cutoff = np.array([0, offset, 0, offset])
        arr_ratio = np.array(
            [
                1.0 / image_size[0],
                1.0 / image_size[1],
                1.0 / image_size[0],
                1.0 / image_size[1],
            ]
        )

        segments = []
        if lines is not None:
            for line in lines:
                normalized_line = (line[0] + arr_cutoff) * arr_ratio
                seg = Segment()
                seg.color = color
                seg.pixels_normalized[0] = Vector2D(
                    x=normalized_line[0], y=normalized_line[1]
                )
                seg.pixels_normalized[1] = Vector2D(
                    x=normalized_line[2], y=normalized_line[3]
                )
                segments.append(seg)

        return segments

    def callback(self, msg):
        image = self.decompress_image(msg)

        # Crop the image
        # cropped_img = self.crop_image(image)
        image_size = (160, 120)
        offset = 40  # you can choose what this crop offset is
        new_image = cv2.resize(image, image_size, interpolation=cv2.INTER_NEAREST)
        cropped_image = new_image[offset:, :]
        cropped_hsv = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2HSV)

        # Take Hough Transform to find lines in the image
        lines_white, lines_yellow, lines_red = self.hough_transform(
            cropped_hsv, cropped_image
        )

        # Find normalized segments
        segments_white = self.segments_from_lines(lines_white, color=Segment.WHITE)
        segments_yellow = self.segments_from_lines(lines_yellow, color=Segment.YELLOW)
        segments_red = self.segments_from_lines(lines_red, color=Segment.RED)

        seglist = SegmentList()
        seglist.segments.extend(segments_white)
        seglist.segments.extend(segments_yellow)
        seglist.segments.extend(segments_red)
        self.pub.publish(seglist)


if __name__ == "__main__":
    GroundProjection()
    rospy.spin()

# https://prod.liveshare.vsengsaas.visualstudio.com/join?6CAE990062784EC6A1C40AC94DCAF8F286B6
