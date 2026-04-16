import os
import rospy

from duckietown_msgs.msg import LEDPattern
from std_msgs.msg import ColorRGBA

from TurnControlFSM import Direction


DUCKIEBOT = os.environ.get("VEHICLE_NAME")

'''
CAEL MAPPED LEDs (At least on Turbogoose)
self.straight_msg.rgb_vals = [
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 0: FRONT LEFT
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 1: REAR RIGHT
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 2: ???
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 3: REAR LEFT
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 4: FRONT RIGHT
        ]
'''


class BlinkerControl:
    def __init__(self):
        self.pub_string = f"/{DUCKIEBOT}/led_emitter_node/led_pattern"
        self.publisher = rospy.Publisher(
            self.pub_string,
            LEDPattern,
            queue_size=10,
        )

        self.straight_msg = LEDPattern()
        self.straight_msg.rgb_vals = [
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 0: FRONT LEFT
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 1: REAR RIGHT
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 2: ???
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 3: REAR LEFT
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 4: FRONT RIGHT
        ]
        self.straight_msg.frequency = 0.0  # Solid, no blinking

        self.blink_left_msg = LEDPattern()
        self.blink_left_msg.rgb_vals = [
            ColorRGBA(1.0, 0.0, 0.0, 1.0),  # 0: FRONT LEFT
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 1: REAR RIGHT
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 2: ???
            ColorRGBA(1.0, 0.0, 0.0, 1.0),  # 3: REAR LEFT
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 4: FRONT RIGHT
        ]
        self.blink_left_msg.frequency = 2.0  # Flashing at 2Hz

        self.blink_right_msg = LEDPattern()
        self.blink_right_msg.rgb_vals = [
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 0: FRONT LEFT
            ColorRGBA(1.0, 0.0, 0.0, 1.0),  # 1: REAR RIGHT
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 2: ???
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 3: REAR LEFT
            ColorRGBA(1.0, 0.0, 0.0, 1.0),  # 4: FRONT RIGHT
        ]
        self.blink_right_msg.frequency = 2.0  # Flashing at 2Hz

        self.stop_msg = LEDPattern()
        self.stop_msg.rgb_vals = [
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 0: FRONT LEFT
            ColorRGBA(1.0, 0.0, 0.0, 1.0),  # 1: REAR RIGHT
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 2: ???
            ColorRGBA(1.0, 0.0, 0.0, 1.0),  # 3: REAR LEFT
            ColorRGBA(0.0, 0.0, 0.0, 1.0),  # 4: FRONT RIGHT
        ]
        self.stop_msg.frequency = 0.0

    def get_ledPattern_from_direction(self, direction):
        if direction == Direction.LEFT:
            return self.blink_left_msg
        if direction == Direction.RIGHT:
            return self.blink_right_msg
        if direction == Direction.STOP:
            return self.stop_msg
        if direction == Direction.STRAIGHT:
            return self.straight_msg

    def update_blinkers(self, direction):
        debug = rospy.get_param("blink_debug", False)
        if debug:
            msg = self.make_test_msg(rospy.get_param("blink_led_num", 0), rospy.get_param("blink_freq", 0.0))
        else:
            msg = self.get_ledPattern_from_direction(direction)
        self.publisher.publish(msg)

    def make_test_msg(self, led_num, freq):
        input_array = [0,0,0,0,0]
        input_array[led_num] = 1
        if led_num > 5 or led_num < 0: led_num = 0 
        test_msg = LEDPattern()
        test_msg.rgb_vals = [
            ColorRGBA(input_array[0], 0.0, 0.0, 1.0),  # 0: off
            ColorRGBA(input_array[1], 0.0, 0.0, 1.0),  # 3 (Left Tail Light): RED
            ColorRGBA(input_array[2], 0.0, 0.0, 1.0),  # 1: off
            ColorRGBA(input_array[3], 0.0, 0.0, 1.0),  # 2: off
            ColorRGBA(input_array[4], 0.0, 0.0, 1.0),  # 4 (Right Tail Light): RED
        ]
        test_msg.frequency = freq
        return test_msg
