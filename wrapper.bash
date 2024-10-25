#!bin/bash
# Usage: ./wrapper.bash <ros_namespace>
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash ${SCRIPT_DIR}/drone-setup.bash --ssid mrsl_perch --pass mrsl_12345
sleep 30
bash ${SCRIPT_DIR}/drone-setup.bash --ros $1 --offboard --docker --disable-cams --params
