#!/bin/bash

LOG_FILE="/tmp/setup.log"

log_status() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a "$LOG_FILE"
}

help() {
    echo "Usage: $0 [-h|--help] [--wifi <ssid> <password>] [--ros <namespace>] [--offboard] [--docker]"
    echo "Options:"
    echo "  -h  Display this help message."
    exit 0
}

params="$(getopt -o '' -l wifi:,ros:,offboard,docker --name "$(basename "$0")" -- "$@")"
echo "Debug: $params"

if [ $? -ne 0 ]; then
    echo "Error: Failed to parse options."
    help
    exit 1
fi

eval set -- "$params"
unset params

SSID="blank"
PASS_WD=""
ROS_NAMESPACE=""
OFFBOARD=false
DOCKER=false

while true; do
    echo "Debug: $1"
    case ${1} in
        --wifi) 
            WIFI=true
            SSID="${2}"
            PASS_WD="${3}"
            if [[ -z "$SSID" || -z "$PASS_WD" ]]; then
                echo "Error: --wifi requires both SSID and password."
                exit 1
            fi
            shift 3
            ;;
        --ros) 
            ROS=true
            ROS_NAMESPACE="${2}"
            if [[ -z "$ROS_NAMESPACE" ]]; then
                echo "Error: --ros requires a namespace."
                exit 1
            fi
            echo "Debug: ROS_NAMESPACE: ${ROS_NAMESPACE}"
            shift 2
            ;;
        --offboard) 
            OFFBOARD=true
            shift
            ;;
        --docker) 
            DOCKER=true
            shift
            ;;
        -h|--help) 
            help 
            exit 0
            ;;
        --) 
            shift
            break
            ;;
        *) 
            help
            exit 1
            ;;
    esac
done

echo "OFFBOARD: ${OFFBOARD}"
echo "DOCKER: ${DOCKER}"

# Connect to wifi 
WiFi(){
    log_status "Connecting to WiFi"

    adb shell "voxl-wifi station '${2}' ${3}'"

    echo "Waiting for Starling to ping google.com..."
    while true; do
        if adb shell 'ping -c 1 -W 1 google.com &> /dev/null'; then
            echo "Connected"
            break
        else
            echo "."
            sleep 2
        fi
    done
    return 0
}

# Set up ROS2
ROS(){
    log_status "Setting up ROS2"
    adb shell 'apt update'
    adb shell 'apt install voxl-ros2-foxy voxl-mpa-to-ros2 -y'
    adb shell 'voxl-configure-mpa-to-ros2'
    adb shell 'sed -i "/param load/a param set XRCE_DDS_DOM_ID 10" /usr/bin/voxl-px4-start' 
    adb shell "sed -i 's/microdds_client start -t udp -h 127.0.0.1 -p 8888 */microdds_client start -t udp -h 127.0.0.1 -p 8888 -n ${1}/' /usr/bin/voxl-px4-start"
    adb shell 'echo "export ROS_DOMAIN_ID=10" >> /home/root/.bashrc'
    return 0
}

# Disable Figure Eight
# Works
Offboard(){
    log_status "Disabling Figure Eight mode"

    adb shell "sed -i '/\"offboard_mode\":[[:space:]]*\"figure_eight\"/s/\"figure_eight\"/\"off\"/' /etc/modalai/voxl-vision-hub.conf"

    if [ $? -eq 0 ]; then
        log_status "Successfully disabled Figure Eight mode"
    else
        log_status "Failed to disable Figure Eight mode"
    fi
    return 0
}

# Install docker
# Works
Docker(){
    log_status "Installing Docker"
    adb shell 'apt install -y ca-certificates curl gnupg'
    adb shell 'curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg'
    adb shell 'echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null'
    adb shell 'apt update'
    adb shell 'sudo apt install -y docker-ce docker-ce-cli containerd.io'
    return 0
}

push_log() {
    log_status "Pushing log file to the drone"
    adb push "$LOG_FILE" /data/
}

if [ "$WIFI" = true ]; then
    WiFi
fi

if [ "$ROS" = true ]; then
    ROS 
fi

if [ "$OFFBOARD" = true ]; then
    Offboard
fi

if [ "$DOCKER" = true ]; then
    Docker
fi

# Store log file on drone with date
push_log
rm $LOG_FILE


