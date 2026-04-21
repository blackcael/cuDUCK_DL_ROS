# Final Project -- QuackOps

rosbag record -O try6.bag  /turbogoose/camera_node/image/compressed /turbogoose/wheels_driver_node/wheels_cmd  --split --size=64

docker cp dts-run-cuduck_dl_ros:/code/catkin_ws/try5_0.bag .