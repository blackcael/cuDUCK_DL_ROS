cmake_minimum_required(VERSION 3.0.2)
project(pid_control)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  duckietown_msgs
)

catkin_package(
#  INCLUDE_DIRS include
#  LIBRARIES pid_control
#  CATKIN_DEPENDS rospy std_msgs duckietown_msgs
#  DEPENDS system_lib
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

catkin_install_python(PROGRAMS
  src/lane_control.py
  src/pid_control.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
