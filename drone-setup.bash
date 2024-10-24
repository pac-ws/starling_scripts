#!/bin/bash

help() {
    echo "Usage: $0 [-h|--help] [--wifi <ssid> <password>] [--ros <namespace>] [--offboard] [--docker]"
    echo "Options:"
    echo "  -h  Display this help message."
    exit 0
}

params="$(getopt -l wifi:,ros:,offboard,docker --name "$(basename "$0")" -- "$@")"

eval set -- "$params"
unset params

SSID = "blank"
while true; do
    case ${1} in
        --wifi) WIFI=true; SSID="${2}"; PASS_WD="${3}"; shift 3;;
        --ros) ROS=true; ROS_NAMESPACE="${2}"; shift 2;;
        --offboard) OFFBOARD=true; shift;;
        --docker) DOCKER=true; shift;;
        -h|--help) help; exit 0;;

# Connect to wifi (add mac address first)
WiFi(){
    echo "Connecting to WiFi ${SSID}"

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
}

# Set up ROS2
ROS(){
    adb shell 'apt update'
    adb shell 'apt install voxl-ros2-foxy voxl-mpa-to-ros2 -y'
    adb shell 'voxl-configure-mpa-to-ros2'
    adb shell 'sed -i "/param load/a param set XRCE_DDS_DOM_ID 10" /usr/bin/voxl-px4-start' 
    adb shell "sed -i 's/microdds_client start -t udp -h 127.0.0.1 -p 8888 */microdds_client start -t udp -h 127.0.0.1 -p 8888 -n ${1}/' /usr/bin/voxl-px4-start"
    adb shell 'echo "export ROS_DOMAIN_ID=10" >> /home/root/.bashrc'
}

# Disable Figure Eight
Offboard(){
    adb shell "sed -i '/\"offboard_mode\": \"figure_eight\"/s/\"figure_eight\"/\"off\"/' /etc/modalai/voxl-vision-hub.conf"
}

# Install docker
Docker(){
    adb shell 'apt install -y ca-certificates curl gnupg'
    adb shell 'curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg'
    adb shell 'echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null'
    adb shell 'apt update'
    adb shell 'sudo apt install -y docker-ce docker-ce-cli containerd.io'
}

if [-n "$WIFI" ]; then
    WiFi
fi

if [-n "$ROS" ]; then
    ROS 
fi

if [-n "$OFFBOARD" ]; then
    Offboard
fi

if [-n "$DOCKER" ]; then
    Docker
fi

