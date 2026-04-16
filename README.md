# Final Project -- QuackOps

Intersection Handling

Overall Goals:
- Add onto existing lane following functionality to handle intersections in Duckietown
- Detect red lines and use PID controller to stop before line and look for AprilTag IDs
- Based on intersection type, choose valid direction and turn using open-loop control
- Using FSM, switch back to lane following mode after turn
- Add functionality for LED blinkers while turning and non-collision filters for the bot in front

Nodes and Topics Added:
- IntersectionFSM Node:
   1. Update stop line, vehicle detection, current april tags, and pose on callbacks
   2. Call FSM tick for every lane following car cmd message received
      a. FSM States: DRIVING, STOPPED_AT_INT, NAVIGATING_INT, STOPPED_BEHIND_BOT
      b. Transitions determined by stop line certainty, vehicle detection certainty, and april tags
      c. Updates LEDs on transition
      d. While NAVIGATING_INT, use another FSM to turn desired angle or drive straight using odometry

- Odometry Node:
    - Calculate and publish pose using wheel encoder ticks as done in previous labs
- Ground Projection Node:
    - Crop image, filter WHITE, YELLOW, and RED. Find edges and publish lines as before.
- Lane Following Node:
    - PID response control from Lane Filter Node (enabled in launch file)
- April Tag Detection Demo Node:
    - Enable in launch file. Subscribe to this to get tag IDs.
- Vehicle Detection Node:
    - Enable in launch file. Subscribe to this to get vehicle detected status.
- Stop Line Filter Node:
    - Enable in launch file. Get lines from ground projection. Publishes stop line detected state. 


## How to run:


Git clone project
```bash
dts devel build -H <duckiebot_name> -f
dts devel run -R <duckiebot_name> --device /dev/input/js0:/dev/input/js0 --cmd bash
```

```bash
roslaunch intersection pid_robot.launch
```

Launch gui tools and keyboard control in separate terminals with:
```bash
dts start_gui_tools <duckiebot_name>
```
```bash
dts duckiebot keyboard_control <duckiebot_name>
```

Click 'a' on keyboard control to begin lane_following software
