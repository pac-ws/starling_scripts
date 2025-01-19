#!/bin/bash

# Check if the ssh_remote_name parameter is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <ssh_remote_name>"
    exit 1
fi

# Get the SSH remote name from the parameter
SSH_REMOTE_NAME=$1

# Commands to execute on the remote
SETUP_CMD="bash -ci '/data/pac_ws/pac_ws_setup/setup_pac_ws.bash -d /data/pac_ws/'"
BUILD_CMD="docker exec pac-m0054 bash -ci 'cd /workspace/ && /workspace/pac_ws_setup/starling_build.bash'"

# SSH into the remote and execute the commands
ssh "$SSH_REMOTE_NAME" "$SETUP_CMD"
ssh "$SSH_REMOTE_NAME" "$BUILD_CMD"

# Exit message
echo "Remote setup and build completed on $SSH_REMOTE_NAME."

