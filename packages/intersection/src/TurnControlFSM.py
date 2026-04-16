#!/usr/bin/env python3
import os
import rospy
from geometry_msgs.msg import Pose2D
import numpy as np
from collections import deque
from enum import Enum

from dataclasses import dataclass
from Direction import Direction
from BlinkerControl import BlinkerControl

DUCKIEBOT = os.environ.get("VEHICLE_NAME")
PARAM_NAME_SPACE = f"/{DUCKIEBOT}/turn_params"


class Direction(Enum):
    LEFT = 1
    RIGHT = 2
    STRAIGHT = 3
    STOP = 4


@dataclass
class Velocity2D:
    """Velocity and Omega object"""

    v: float
    o: float


class TurnControlFSM:
    # Param Defaults
    SPEED_DEF = 0.2
    ANG_VEL_DEF = 3.3
    LEFT_TURN_LENGTH_DEF = 1.0
    RIGHT_TURN_LENGTH_DEF = 1.2
    STRAIGHT_LENGTH_DEF = 0.16
    LEFT_SPEED_DEF = 0.3
    RIGHT_SPEED_DEF = 0.1
    LOAD_PARAMS_UPDATE_THRESHOLD = 50

    def __init__(self):
        # rospy.init_node("turnControlFSM", anonymous=True) # Constructor called inside IntersectionNode
        rospy.Subscriber("pose", Pose2D, self.pose_cb)

        self.pose = Pose2D()
        self.pose.x = 0
        self.pose.y = 0
        self.pose.theta = 0
        self.start_pos = self.pose

        self.left_turn_length = self.LEFT_TURN_LENGTH_DEF
        self.right_turn_length = self.RIGHT_TURN_LENGTH_DEF
        self.straight_length = self.STRAIGHT_LENGTH_DEF
        self.move_forward_vel = Velocity2D(v=self.SPEED_DEF, o=0.0)
        self.stop_vel = Velocity2D(v=0.0, o=0.0)
        self.turn_left_vel = Velocity2D(v=self.LEFT_SPEED_DEF, o=self.ANG_VEL_DEF)
        self.turn_right_vel = Velocity2D(v=self.RIGHT_SPEED_DEF, o=-self.ANG_VEL_DEF)
        self.state_velocity = Velocity2D(v=0.0, o=0.0)
        self.move_segments = deque()

        # `current_state` changes based on segments of the turn
        # Turning left is separated into LEFT and STRAIGHT segments
        # Turning right is separated into RIGHT and STRAIGHT segments
        # Turning straight is just STRAIGHT segments
        # STOP state is used to indicate end of turn
        self.current_state = Direction.STOP
        self.current_direction = Direction.STOP
        self.movement_flag = False

        # Cael Update Counter
        self.update_counter = 0

    def load_params(self):
        # Fetch new parameter values from ROS
        speed = rospy.get_param(PARAM_NAME_SPACE + "/speed", self.SPEED_DEF)
        left_speed = rospy.get_param(
            PARAM_NAME_SPACE + "/left_speed", self.LEFT_SPEED_DEF
        )
        right_speed = rospy.get_param(
            PARAM_NAME_SPACE + "/right_speed", self.RIGHT_SPEED_DEF
        )
        ang_vel = rospy.get_param(PARAM_NAME_SPACE + "/ang_vel", self.ANG_VEL_DEF)
        left_turn_length = rospy.get_param(
            PARAM_NAME_SPACE + "/left_turn_length", self.LEFT_TURN_LENGTH_DEF
        )
        right_turn_length = rospy.get_param(
            PARAM_NAME_SPACE + "/right_turn_length", self.RIGHT_TURN_LENGTH_DEF
        )
        straight_length = rospy.get_param(
            PARAM_NAME_SPACE + "/straight_length", self.STRAIGHT_LENGTH_DEF
        )

        # Compare fetched values with current values
        temps = (
            self.move_forward_vel.v,
            self.move_forward_vel.o,
            self.turn_left_vel.v,
            self.turn_left_vel.o,
            self.turn_right_vel.v,
            self.turn_right_vel.o,
            self.left_turn_length,
            self.right_turn_length,
            self.straight_length,
        )

        updated = (
            speed,
            0.0,
            left_speed,
            ang_vel,
            right_speed,
            -ang_vel,
            left_turn_length,
            right_turn_length,
            straight_length,
        )

        if temps != updated:
            # rospy.logwarn(f"TurnControlFSM params updated: {updated}")
            self.move_forward_vel = Velocity2D(v=speed, o=0.0)
            self.turn_left_vel = Velocity2D(v=left_speed, o=ang_vel)
            self.turn_right_vel = Velocity2D(v=right_speed, o=-ang_vel)
            self.left_turn_length = left_turn_length
            self.right_turn_length = right_turn_length
            self.straight_length = straight_length

    def pose_cb(self, msg):
        self.pose = msg

    def dist(self, p1, p2):
        return np.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)

    def is_moving(self):
        return self.movement_flag

    def set_direction(self, direction):
        self.load_params()
        self.current_direction = direction
        self.build_move_segments()

        # Initialize FSM with first segment
        self.current_state = self.move_segments.popleft()
        self.start_pos = self.pose
        self.movement_flag = True

    def build_move_segments(self):
        self.move_segments.clear()
        if self.current_direction == Direction.STRAIGHT:
            # Straight segment length is shared with turns
            # Each should be about half the intersection length
            # so about 2 straight segments for straight movement
            self.move_segments.append(Direction.STRAIGHT)
            self.move_segments.append(Direction.STRAIGHT)
            self.move_segments.append(Direction.STOP)
        else:
            # Left or Right turn
            self.move_segments.append(Direction.STRAIGHT)
            self.move_segments.append(self.current_direction)
            self.move_segments.append(Direction.STRAIGHT)
            self.move_segments.append(Direction.STOP)

    def get_travelled_dist(self):
        return self.dist(self.start_pos, self.pose)

    def get_angle_turned(self):
        return np.abs(self.pose.theta - self.start_pos.theta)

    def should_update(self):
        if self.update_counter >= self.LOAD_PARAMS_UPDATE_THRESHOLD:
            self.update_counter = 0
            return True
        else:
            self.update_counter += 1
            return False

    def turn_control_tick(self):
        if self.should_update(): 
            self.load_params()
        self.turn_control_actions()
        self.turn_control_transitions()
        # rospy.logwarn(
        #     f"M: {self.movement_flag}, D: {self.current_direction}, S: {self.current_state}, V: {self.state_velocity.v}, O: {self.state_velocity.o} "
        #     f"D: {self.get_travelled_dist()}, A: {self.get_angle_turned()}"
        # )
        return self.state_velocity.v, self.state_velocity.o

    def turn_control_actions(self):
        # rospy.logwarn(f"Turn control action for state: {self.current_state}")
        if self.current_state == Direction.STOP:
            raise Exception("Should not be in STOP state during turn control")
        elif self.current_state == Direction.STRAIGHT:
            self.state_velocity = self.move_forward_vel
        elif self.current_state == Direction.LEFT:
            self.state_velocity = self.turn_left_vel
        elif self.current_state == Direction.RIGHT:
            self.state_velocity = self.turn_right_vel

        # Tick Blinkers
        self.blinkerControl.update_blinkers(self.current_state)

    def turn_control_transitions(self):
        next_state = self.current_state
        if self.current_state == Direction.STOP:
            raise Exception("Should not be in STOP state during turn control")
        elif not self.move_segments:
            # Should never happen
            rospy.logwarn("No more move segments, stopping")
            next_state = Direction.STOP
        elif (
            self.current_state == Direction.STRAIGHT
            and self.get_travelled_dist() >= self.straight_length
        ):
            # If straight segment has reached required length (should probably be half intersection length)
            self.start_pos = self.pose
            next_state = self.move_segments.popleft()
        elif (
            self.current_state == Direction.LEFT
            and self.get_angle_turned() >= self.left_turn_length
        ):
            # If left turn has reached 90 degrees
            self.start_pos = self.pose
            next_state = self.move_segments.popleft()
        elif (
            self.current_state == Direction.RIGHT
            and self.get_angle_turned() >= self.right_turn_length
        ):
            # If right turn has reached 90 degrees
            self.start_pos = self.pose
            next_state = self.move_segments.popleft()

        # The last segment should always be STOP, this should notify FSM caller
        # to stop ticking turn control
        if next_state == Direction.STOP:
            self.movement_flag = False
        self.current_state = next_state


if __name__ == "__main__":
    # Standalone testing mode - not used when called from IntersectionNode
    rospy.init_node("turnControlFSM", anonymous=True)
    oc = TurnControlFSM()
    rospy.spin()
