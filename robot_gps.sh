#!/bin/bash

# Robot GPS Status Monitor using PX4 sensor_gps
# Usage: ./gps_monitor.sh r0 r5 r12 r29

# Check if any arguments were provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <robot_names...>"
    echo "Example: $0 r0 r5 r12 r29"
    exit 1
fi

# Create temp directory for results
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR; kill 0" EXIT

# Declare associative arrays for storing results
declare -A GPS_DATA
declare -a ROBOTS

# Initialize robots
for robot_name in "$@"; do
    ROBOTS+=("$robot_name")
    GPS_DATA["$robot_name"]="---|---|---|---|---|---|---|---|---|Waiting..."
done

# Function to draw the table
draw_table() {
    clear
    echo "╔═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                          Robot GPS Status Monitor (Live)                                                    ║"
    echo "╠════════╦════════╦══════════╦══════╦═════════════╦══════════════╦════════╦═════════╦══════════╦══════════╦═══════════════════╣"
    echo "║ Robot  ║ Age(s) ║ Fix Type ║ Sats ║ Latitude    ║ Longitude    ║ Alt(m) ║ Vel(m/s)║ HDOP     ║ VDOP     ║ Status            ║"
    echo "╠════════╬════════╬══════════╬══════╬═════════════╬══════════════╬════════╬═════════╬══════════╬══════════╬═══════════════════╣"
    
    for robot_name in "${ROBOTS[@]}"; do
        IFS='|' read -r age fix sats lat lon alt vel hdop vdop status <<< "${GPS_DATA[$robot_name]}"
        
        printf "║ %-6s ║ %6s ║ %-8s ║ %4s ║ %11s ║ %12s ║ %6s ║ %7s ║ %8s ║ %8s ║ %-17s ║\n" \
            "$robot_name" "$age" "$fix" "$sats" "$lat" "$lon" "$alt" "$vel" "$hdop" "$vdop" "$status"
    done
    
    echo "╚════════╩════════╩══════════╩══════╩═════════════╩══════════════╩════════╩═════════╩══════════╩══════════╩═══════════════════╝"
    echo ""
    echo "Press Ctrl+C to exit"
}

# Function to parse fix type
get_fix_type() {
    case $1 in
        0) echo "No Fix" ;;
        1) echo "Dead Rck" ;;
        2) echo "2D Fix" ;;
        3) echo "3D Fix" ;;
        4) echo "DGPS" ;;
        5) echo "RTK Flt" ;;
        6) echo "RTK Fix" ;;
        *) echo "Unknown" ;;
    esac
}

# Function to get GPS status for a robot
get_gps_status() {
    local robot_name=$1
    local result_file="$TEMP_DIR/$robot_name"
    
    # SSH into robot and run px4-listener sensor_gps -n 1
    gps_output=$(ssh "$robot_name" "px4-listener sensor_gps -n 1" 2>&1)
    
    # Parse the output
    if [ -n "$gps_output" ]; then
        # Extract relevant fields
        age=$(echo "$gps_output" | grep "timestamp:" | grep -oP '\(\K[0-9.]+(?= seconds ago)')
        fix_num=$(echo "$gps_output" | grep "fix_type:" | awk '{print $NF}')
        sats=$(echo "$gps_output" | grep "satellites_used:" | awk '{print $NF}')
        lat_raw=$(echo "$gps_output" | grep "^    lat:" | awk '{print $NF}')
        lon_raw=$(echo "$gps_output" | grep "^    lon:" | awk '{print $NF}')
        alt_raw=$(echo "$gps_output" | grep "^    alt:" | awk '{print $NF}')
        vel=$(echo "$gps_output" | grep "vel_m_s:" | awk '{print $NF}')
        hdop=$(echo "$gps_output" | grep "hdop:" | awk '{print $NF}')
        vdop=$(echo "$gps_output" | grep "vdop:" | awk '{print $NF}')
        
        # Convert lat/lon from 1e7 format to degrees
        if [ -n "$lat_raw" ] && [ "$lat_raw" != "0" ]; then
            lat=$(echo "scale=7; $lat_raw / 10000000" | bc)
        else
            lat="0.0"
        fi
        
        if [ -n "$lon_raw" ] && [ "$lon_raw" != "0" ]; then
            lon=$(echo "scale=7; $lon_raw / 10000000" | bc)
        else
            lon="0.0"
        fi
        
        # Convert altitude from mm to m
        if [ -n "$alt_raw" ]; then
            alt=$(echo "scale=1; $alt_raw / 1000" | bc)
        else
            alt="0.0"
        fi
        
        # Get fix type string
        fix=$(get_fix_type "$fix_num")
        
        # Format age
        if [ -n "$age" ]; then
            age=$(printf "%.2f" "$age")
        else
            age="---"
        fi
        
        # Format velocity
        if [ -n "$vel" ]; then
            vel=$(printf "%.2f" "$vel")
        else
            vel="0.00"
        fi
        
        # Determine status
        if [ "$fix_num" -eq 0 ]; then
            status="No GPS"
        elif [ "$fix_num" -eq 6 ]; then
            status="RTK Fixed"
        elif [ "$fix_num" -eq 5 ]; then
            status="RTK Float"
        elif [ "$fix_num" -ge 3 ]; then
            status="Fix OK"
        else
            status="Poor Fix"
        fi
        
        # Default empty values
        sats="${sats:-0}"
        hdop="${hdop:-99.99}"
        vdop="${vdop:-99.99}"
        
        echo "$age|$fix|$sats|$lat|$lon|$alt|$vel|$hdop|$vdop|$status" > "$result_file"
    else
        echo "---|---|---|---|---|---|---|---|---|Error" > "$result_file"
    fi
}

# Main loop
echo "Starting GPS status monitor..."
sleep 1

while true; do
    # Get GPS status for all robots in parallel
    for robot_name in "${ROBOTS[@]}"; do
        get_gps_status "$robot_name" &
    done
    
    # Wait for all background jobs to complete
    wait
    
    # Read results from temp files
    for robot_name in "${ROBOTS[@]}"; do
        result_file="$TEMP_DIR/$robot_name"
        if [ -f "$result_file" ]; then
            GPS_DATA["$robot_name"]=$(cat "$result_file")
        fi
    done
    
    # Draw the updated table
    draw_table
    
    # Wait before next update
    sleep 2
done
