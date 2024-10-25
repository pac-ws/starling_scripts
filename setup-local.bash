#!/bin/bash

LOG_FILE="/tmp/setup.log"

log_status() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a "$LOG_FILE"
}

help() {
    echo "Usage: $0 [-h|--help] [--ssid <ssid>] [--pass <password>] [--ros <namespace>] [--offboard] [--docker] [--disable-cams] [--params]"
    exit 0
}

params="$(getopt -o 'h' -l ssid:,pass:,ros:,offboard,docker,disable-cams,params,help --name "$(basename "$0")" -- "$@")"
echo "Debug: $params"

eval set -- "$params"
unset params

SSID_SET=false
SSID=""
PASS_SET=false
PASS=""
ROS_NAMESPACE=""
DISABLE_CAMS=false
OFFBOARD=false
DOCKER=false
PARAMS=false

while true; do
    echo "Debug: $1"
    case ${1} in
        --ssid) 
            SSID_SET=true
            SSID="${2}"
            if [[ -z "$SSID" ]]; then
                echo "Error: --ssid requires an ssid."
                exit 1
            fi
            shift 2
            ;;
        --pass) 
            PASS_SET=true
            PASS="${2}"
            if [[ -z "$PASS" ]]; then
                echo "Error: --pass requires a password."
                exit 1
            fi
            shift 2
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
        --disable-cams) 
            DISABLE_CAMS=true
            shift
            ;;
        --params) 
            PARAMS=true
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

echo "SSID: ${SSID}"
echo "PASS: ${PASS}"
echo "OFFBOARD: ${OFFBOARD}"
echo "DOCKER: ${DOCKER}"

# Connect to wifi 
WiFi(){
    log_status "Connecting to WiFi"
    voxl-wifi station '${SSID}' '${PASS}'
    return 0
}

# Set up ROS2
ROS(){
    log_status "Setting up ROS2"
    apt update
    apt install voxl-ros2-foxy voxl-mpa-to-ros2 -y
    voxl-configure-mpa-to-ros2
    sed -i "/param load/a param set XRCE_DDS_DOM_ID 10" /usr/bin/voxl-px4-start
    sed -i "s/microdds_client start -t udp -h 127.0.0.1 -p 8888 */microdds_client start -t udp -h 127.0.0.1 -p 8888 -n '${ROS_NAMESPACE}'/" /usr/bin/voxl-px4-start
    echo "export ROS_DOMAIN_ID=10" >> /home/root/.bashrc
    return 0
}

# Disable Figure Eight
# Works
Offboard(){
    log_status "Disabling Figure Eight mode"
    sed -i '/\"offboard_mode\":[[:space:]]*\"figure_eight\"/s/\"figure_eight\"/\"off\"/' /etc/modalai/voxl-vision-hub.conf
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
    apt install -y ca-certificates curl gnupg
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io
    docker pull agarwalsaurav/pac:arm64
    return 0
}

DisableCams(){
    log_status "Disabling cameras"
    systemctl stop voxl-camera-server
    systemctl disable voxl-camera-server
    return 0
}

Params(){
    log_status "Setting up PX4 params (Outdoor GPS Baro)"
    voxl-configure-px4-params -f /usr/share/modalai/px4_params/v1.14/EKF2_helpers/outdoor_gps_baro.params -n
    return 0
}

push_log() {
    log_status "Pushing log file to the drone"
    cp $LOG_FILE /data/setup.log
}

if [[ "$SSID_SET" = true && "$PASS_SET" = true ]]; then
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

if [ "$DISABLE_CAMS" = true ]; then
    DisableCams
fi

if [ "$PARAMS" = true ]; then
    Params
fi


# Store log file on drone with date
push_log

rm $LOG_FILE
