#!/bin/bash

help() {
    echo "Usage: $0 [-h] [-i interface] [-n last_octet] [-f frequency] [-e essid]"
    echo "Options:"
    echo "  -h  Display this help message."
    echo "  -i  Specify the interface to use. Default is wlan0"
    echo "  -n  Specify last octet of IP address. Default is 50"
    echo "  -f  Specify the frequency to use. Default is 2412 (MHz)"
    echo "  -e  Specify the ESSID of the network. Default is swarm_adhoc"
    exit 0
}

# Default values
IFACE=wlan0
OCTET=50
FREQ=2412
ESSID=swarm_adhoc

while getopts ":hi:n:f:" option; do
    case $option in
        h) help exit;;
        i) IFACE=$OPTARG;;
        n) OCTET=$OPTARG;;
        f) FREQ=$OPTARG;;
        \?) echo "Invalid option: $OPTARG"; exit 1;;
    esac
done

echo "Configuring ad-hoc network named ${ESSID} on interface ${IFACE} with IP 10.42.0.${OCTET}/24 and frequency ${FREQ} MHz"

# Configure the interface
ip link set ${IFACE} down
iw dev ${IFACE} set type ibss
ip link set ${IFACE} up
iw dev ${IFACE} ibss join ${ESSID} ${FREQ}
ip addr add 10.42.0.${OCTET}/24 dev ${IFACE}
iw dev ${IFACE} info



