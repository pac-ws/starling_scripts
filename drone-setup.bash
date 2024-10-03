#!/bin/bash

# Connect to wifi (add mac address first)
adb shell voxl-wifi station $1 $2

# Set up ROS2
adb shell apt update
adb install voxl-ros2-foxy voxl-mpa-to-ros2 -y
adb shell voxl-configure-mpa-to-ros2

# Disable Figure Eight
adb shell vim -c "237s/figure_eight/off/g" -c "wq" "/etc/modalai/voxl-vision-hub.conf"

# Add the workspace
# TODO

# Build ROS packages
#adb shell cd /fred/starling_tests_ws/ && colcon build
