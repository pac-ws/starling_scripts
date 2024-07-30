#!/bin/bash

# Default value
IFACE=wlan0

while getopts ":hi:" option; do
    case $option in
        h)
            echo "Usage: $0 [-i interface]"
            exit 0
            ;;
        i)
            IFACE=$OPTARG;;
        \?)
            echo "Invalid option: -$OPTARG"
            exit 1
            ;;
    esac
done

echo "Setting $IFACE to managed mode"
ip link set $IFACE down
iw dev $IFACE set type managed
ip link set $IFACE up
iw dev $IFACE info


