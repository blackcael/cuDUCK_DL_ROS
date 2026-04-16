from Direction import Direction

import rospy


class DirectionDecider:
    def __init__(self):
        self.direction_list = [Direction.LEFT, Direction.RIGHT, Direction.STRAIGHT]
        self.current_direction_index = 0

        self.stop_list = [20, 22, 23, 24, 25, 26, 31, 32, 33]
        self.left_right_list = [11, 65]
        self.straight_right_list = [9, 57]
        self.straight_left_list = [10, 61]

    def _choose_next_direction(self):
        rospy.logwarn(f"Current direction index: {self.current_direction_index}")
        direction = self.direction_list[self.current_direction_index]
        self.current_direction_index += 1
        if self.current_direction_index >= len(self.direction_list):
            self.current_direction_index = 0
        return direction

    def _april_tag_to_words(self, april_index):
        ## WE STOP ON THE RED LINE SO WE DONT CARE ABOUT STOP SIGNS
        if april_index in self.stop_list:
            return Direction.STOP
        if april_index in self.left_right_list:
            return (Direction.LEFT, Direction.RIGHT)
        if april_index in self.straight_right_list:
            return (Direction.STRAIGHT, Direction.RIGHT)
        if april_index in self.straight_left_list:
            return (Direction.STRAIGHT, Direction.LEFT)
        return None

    def decide_direction_from_index(self, april_index, ignore_stop=True):
        """
        Given the april tag index, it will return the direction we should go.
        Possible returns are the strings Direction.LEFT, Direction.RIGHT, Direction.STRAIGHT or None
        If the april tag value is "None", the value of a Direction.STOP sign, or an unmapped aruco value, it will return None.
        """
        if april_index == None:
            return None
        possible_directions = self._april_tag_to_words(april_index)
        if possible_directions == None:
            return None
        # Filter Stop Signs
        if possible_directions == Direction.STOP:
            if ignore_stop:
                return None
            else:
                return Direction.STOP

        #### DEBUG ####
        # Debug Turn - Ignore April Tags that don't include the desired turn
        # if Direction.LEFT not in possible_directions:
        #     rospy.logwarn(f"Ignoring april tag {april_index} for debug turn")
        #     return None
        #### DEBUG ####

        # Loop Through Potential Directions
        while True:
            direction = self._choose_next_direction()
            if direction in possible_directions:
                break
        return direction

    # Main direction decider: Loop through directions
    def decide_direction_from_index_list(self, april_index_list):
        """Returns the first valid direction found otherwise None"""
        debug = rospy.get_param("turn_debug", False)
        if debug:
            turn_num = debug = rospy.get_param("turn_type", 1)
            if turn_num < 0 or turn_num > 4: turn_num = 0
            if turn_num == 1:
                return Direction.LEFT
            if turn_num == 2:
                return Direction.RIGHT
            if turn_num == 3: 
                return Direction.STRAIGHT
            return Direction.STOP


        for april_index in april_index_list:
            direction = self.decide_direction_from_index(april_index)
            if direction != None:
                return direction
        # If no valid direction found
        return None
