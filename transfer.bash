#!/bin/bash

# Define the list of IP addresses and corresponding namespaces
IP_ADDRESSES=("192.168.129.222")  # Add your IPs here
NAMESPACES=("r10")
PASSWORD="oelinux123"  # Replace with the actual root password
LOCAL_SCRIPT="setup-local.bash"  # Ensure this file is present in the same directory

# Check if the number of IPs matches the number of namespaces
if [ "${#IP_ADDRESSES[@]}" -ne "${#NAMESPACES[@]}" ]; then
    echo "Error: Number of IP addresses and namespaces must match!"
    exit 1
fi

# Function to handle SCP and remote execution
execute_remote() {
    local ip="$1"
    local namespace="$2"
    
    echo "Starting transfer and setup for $ip with namespace $namespace"
    
    sshpass -p "$PASSWORD" scp "$LOCAL_SCRIPT" root@"$ip":/data/
    sshpass -p "$PASSWORD" ssh root@"$ip" "chmod +x /data/$LOCAL_SCRIPT && /data/$LOCAL_SCRIPT --ros $namespace --params --docker --disable-cams --pac $namespace"

    #sshpass -p "$PASSWORD" ssh -T root@"$ip" /data/pac_ws/pac_ws_setup/pac_create_container.sh -d /data/pac_ws --ns r6
    #sshpass -p "$PASSWORD" ssh -T root@"$ip" "chmod +x /data/$LOCAL_SCRIPT && /data/$LOCAL_SCRIPT --pac $namespace"
    
    if [ $? -eq 0 ]; then
        echo "Successfully processed $ip"
    else
        echo "Failed to process $ip"
    fi
}

export -f execute_remote  # Export the function for parallel use
export PASSWORD LOCAL_SCRIPT  # Export variables

# Use parallel to run the commands concurrently
#parallel --eta --jobs 5 execute_remote ::: "${IP_ADDRESSES[@]}" ::: "${NAMESPACES[@]}"
execute_remote "${IP_ADDRESSES[0]}" "${NAMESPACES[0]}"

echo "All parallel processes completed."

