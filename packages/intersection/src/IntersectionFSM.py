#!/usr/bin/env python3
import rospy
from enum import Enum

from BlinkerControl import TurnSignals
from DirectionDecider import DirectionDecider
from RobustStopBuffer import RobustStopBuffer
from TurnControlFSM import TurnControlFSM, Direction, Velocity2D

STOP_DURATION = 3
MIN_STOP_CERTAINTY = 0.6
MIN_STOP_BUFFER_SIZE = 10
MIN_DET_CERTAINTY = 0.1
BEHIND_CAR_DURATION = 2

RANGE_THRESHOLD = 0.2

LOAD_PARAMS_UPDATE_THRESHOLD = 50



class State(Enum):
    DRIVING = 1
    STOPPED_AT_INT = 2
    NAVIGATING_INT = 3
    STOPPING_BEHIND_BOT = 4


class IntersectionFSM:
    """ROS Free FSM"""
    
    def __init__(self):
        # Intersection Stop Control
        self.behind_car_start = -1
        self.inter_stop_start = -1
        self.stop_buffer = RobustStopBuffer()

        # Range Control
        self.dbuffer = RobustStopBuffer()

        # Direction Decider
        self.direction_decider = DirectionDecider()
        self.new_direction = None

        # Turn Control
        self.turn_control = TurnControlFSM()
        self.turn_signals = TurnSignals()
        self.turn_signals.update_blinkers(Direction.STRAIGHT)


        # Blinker Control (We are just using turn Controls object)
        self.blinkerControl = self.turn_control.blinkerControl

        # April Tags
        self.detected_IDs_list = []

        # State Machine Management
        self.current_state = State.DRIVING
        self.vel2D = Velocity2D(v=0.0, o=0.0)
        

        # Update counter
        self.update_counter = 0
        self.min_stop_certainty = 0.6
        self.min_stop_buffer_size = 10


    def add_stop_line_reading(self, at_stop_line: bool):
        self.stop_buffer.append(at_stop_line)

    def add_range_reading(self, detection: bool):
        self.dbuffer.append(detection)

    def update_april_tags(self, april_tags_list: list):
        self.detected_IDs_list = april_tags_list

    def get_current_state(self):
        return self.current_state

    # Tick with FSM loop
    def tick_fsm_loop(self, velocity: float, omega: float, time_stamp: float):
        self.vel2D.v, self.vel2D.o = velocity, omega
        self.time_stamp = time_stamp
        self.fsm_actions()
        self.fsm_transitions()
        if self.vel2D.v == velocity and self.vel2D.o == omega and self.current_state != State.DRIVING:
            rospy.logwarn(f"ERROR NOT CORRECTLY CHANGING VEL: {self.vel2D.v}, {self.vel2D.o}")
        return self.vel2D.v, self.vel2D.o

    def should_update_params(self):
        if self.update_counter >= LOAD_PARAMS_UPDATE_THRESHOLD:
            self.update_counter = 0
            return True
        else:
            self.update_counter += 1
            return False

    def update_params(self):
        self.min_stop_certainty = rospy.get_param(
            "min_stop_certainty", self.min_stop_certainty
        )
        new_buffer_size = rospy.get_param(
            "min_stop_buf_size", self.min_stop_buffer_size
        )
        if new_buffer_size != self.min_stop_buffer_size:
            self.min_stop_buffer_size = new_buffer_size
            self.stop_buffer.set_buffer_size(new_buffer_size)



    def fsm_actions(self):
        # CAEL TEMP DEBUG
        rospy.logwarn(f"CURRENT_STATE = {self.current_state}, NEW_DIRECTION = {self.new_direction}")
        if self.current_state == State.DRIVING:
            #update blinkers
            self.blinkerControl.update_blinkers(Direction.STRAIGHT)
            # Don't do anything pass through velocity and omega
            pass

        elif self.current_state == State.STOPPED_AT_INT:
            #update blinkers
            self.blinkerControl.update_blinkers(Direction.STOP)
            # set wheel velocites to zero, ignore omega
            self.vel2D.v = 0.0

            # Look for direction
            self.new_direction = (
                self.direction_decider.decide_direction_from_index_list(
                    self.detected_IDs_list
                )
            )

        elif self.current_state == State.NAVIGATING_INT:
            # using what direction should be next, turn that direction (call to Turn Control)
            self.vel2D.v, self.vel2D.o = self.turn_control.turn_control_tick()

        elif self.current_state == State.STOPPING_BEHIND_BOT:
            # disable standard lane following
            # set wheel velocites to zero
            self.vel2D.v, self.vel2D.o = 0, 0

    def fsm_transitions(self):
        next_state = self.current_state

        if self.current_state == State.DRIVING:
            # If we robustly see red lines go to stopped at int
            if self.stop_buffer.get_certainty() >= self.min_stop_certainty:
                # Save the time we stopped at intersection
                next_state = State.STOPPED_AT_INT
                self.stop_buffer.clear()
                self.inter_stop_start = self.time_stamp
                self.turn_signals.update_blinkers(Direction.STOP)
                self.new_direction = None  # Set none so april tag direction is required
            # TODO: If we see another car in front of us (distance sensor?) go to STOPPING_BEHIND_BOT
            if self.dbuffer.get_certainty() >= MIN_DET_CERTAINTY:
                next_state = State.STOPPING_BEHIND_BOT
                self.turn_signals.update_blinkers(Direction.STOP)
                self.dbuffer.clear()
                self.behind_car_start = self.time_stamp

        elif self.current_state == State.STOPPED_AT_INT:
            # Navigate Intersection
            time_at_stop = self.time_stamp - self.inter_stop_start
            if time_at_stop >= STOP_DURATION and self.new_direction != None:
                next_state = State.NAVIGATING_INT
                self.turn_control.set_direction(self.new_direction)
                self.turn_signals.update_blinkers(self.new_direction)

        elif self.current_state == State.NAVIGATING_INT:
            # Once we get "navigating complete flag (complete turn / straight) go back to driving"
            if not self.turn_control.is_moving():
                next_state = State.DRIVING
                self.stop_buffer.clear()
                self.turn_signals.update_blinkers(Direction.STRAIGHT)

        elif self.current_state == State.STOPPING_BEHIND_BOT:
            # Once we no longer see car in front of us, return to driving
            duration = self.time_stamp - self.behind_car_start
            if (
                duration >= BEHIND_CAR_DURATION
                and self.dbuffer.get_certainty() < MIN_DET_CERTAINTY
            ):
                next_state = State.DRIVING
                self.turn_signals.update_blinkers(Direction.STRAIGHT)

        if next_state != self.current_state:
            rospy.logwarn(f"Switching to {next_state.name}")
        self.current_state = next_state
