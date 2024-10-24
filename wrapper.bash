#!bin/bash
# Usage: ./wrapper.bash <ros_namespace>
drone_setup.bash --ssid mrsl_perch -pass mrsl_12345
sleep 30
drone_setup.bash --ros $1 --offboard --docker --disable-cams --params
