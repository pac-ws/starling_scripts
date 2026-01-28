#!/bin/bash

# Robot Latency Monitor with Live Display
# Usage: ./robot_ping.sh r0 r5 r12 r29

# Check if any arguments were provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <robot_names...>"
    echo "Example: $0 r0 r5 r12 r29"
    exit 1
fi

# Create temp directory for results
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Create latency_test directory if it doesn't exist
RESULTS_DIR="latency_test"
mkdir -p "$RESULTS_DIR"

# Create CSV file with timestamp
TIMESTAMP=$(date +"%Y%m%d-%H:%M:%S")
CSV_FILE="$RESULTS_DIR/${TIMESTAMP}-latency.csv"

# Write CSV header
echo "timestamp,robot,ip,latency_ms,status" > "$CSV_FILE"
echo "Logging results to: $CSV_FILE"

# Function to extract robot number and validate
get_robot_number() {
    local robot_name=$1
    
    if [[ ! $robot_name =~ ^r([0-9]+)$ ]]; then
        echo "Error: Invalid robot name '$robot_name'. Expected format: r0-r29" >&2
        return 1
    fi
    
    local num="${BASH_REMATCH[1]}"
    
    if [ "$num" -lt 0 ] || [ "$num" -gt 29 ]; then
        echo "Error: Robot number must be between 0 and 29 (got $num)" >&2
        return 1
    fi
    
    echo "$num"
    return 0
}

# Function to build IP address
get_robot_ip() {
    local robot_num=$1
    # Pad single digit numbers with 0 (e.g., 5 -> 05, 12 -> 12)
    local padded_num=$(printf "%02d" "$robot_num")
    echo "10.223.1.1${padded_num}"
}

# Declare associative arrays for storing results
declare -A LATENCIES
declare -A STATUSES
declare -a ROBOTS

# Validate all robot names first
for robot_name in "$@"; do
    robot_num=$(get_robot_number "$robot_name")
    if [ $? -eq 0 ]; then
        ROBOTS+=("$robot_name")
        LATENCIES["$robot_name"]="---"
        STATUSES["$robot_name"]="Waiting..."
    fi
done

# Function to draw the table
draw_table() {
    clear
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║         Robot Latency Monitor (Live)                  ║"
    echo "╠══════════╦═══════════════════╦═══════════════════════╣"
    echo "║  Robot   ║    IP Address     ║   Latency (ms)        ║"
    echo "╠══════════╬═══════════════════╬═══════════════════════╣"
    
    for robot_name in "${ROBOTS[@]}"; do
        robot_num=$(get_robot_number "$robot_name")
        ip=$(get_robot_ip "$robot_num")
        latency="${LATENCIES[$robot_name]}"
        status="${STATUSES[$robot_name]}"
        
        printf "║ %-8s ║ %-17s ║ %-21s ║\n" "$robot_name" "$ip" "$latency ($status)"
    done
    
    echo "╚══════════╩═══════════════════╩═══════════════════════╝"
    echo ""
    echo "Press Ctrl+C to exit"
}

# Function to ping a robot and write results to temp file
ping_robot() {
    local robot_name=$1
    local robot_num=$(get_robot_number "$robot_name")
    local ip=$(get_robot_ip "$robot_num")
    local result_file="$TEMP_DIR/$robot_name"
    
    # Ping once with 1 second timeout
    if ping_result=$(ping -c 1 -W 1 "$ip" 2>/dev/null); then
        # Extract the time from ping output (matches "time=3.44 ms")
        latency=$(echo "$ping_result" | grep -o 'time=[0-9.]*' | cut -d= -f2)
        if [ -n "$latency" ]; then
            latency=$(printf "%.2f" "$latency")
            echo "$latency|OK" > "$result_file"
        else
            echo "---|Error" > "$result_file"
        fi
    else
        echo "---|Unreachable" > "$result_file"
    fi
}

# Main loop
echo "Starting robot latency monitor..."
sleep 1

while true; do
    # Ping all robots in parallel
    for robot_name in "${ROBOTS[@]}"; do
        ping_robot "$robot_name" &
    done
    
    # Wait for all background jobs to complete
    wait
    
    # Read results from temp files
    for robot_name in "${ROBOTS[@]}"; do
        result_file="$TEMP_DIR/$robot_name"
        if [ -f "$result_file" ]; then
            IFS='|' read -r latency status < "$result_file"
            LATENCIES["$robot_name"]="$latency"
            STATUSES["$robot_name"]="$status"
            
            # Save to CSV with timestamp
            measurement_time=$(date +"%Y-%m-%d %H:%M:%S")
            robot_num=$(get_robot_number "$robot_name")
            ip=$(get_robot_ip "$robot_num")
            echo "$measurement_time,$robot_name,$ip,$latency,$status" >> "$CSV_FILE"
        fi
    done
    
    # Draw the updated table
    draw_table
    
    # Wait before next update
    sleep 2
done
