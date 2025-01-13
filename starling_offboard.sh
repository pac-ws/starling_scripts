#!/bin/bash

MAV_TYPE=starling2
MAV_NAME=$ROS_NAMESPACE

echo "MAV name: $MAV_NAME MAV Type: $MAV_TYPE"

SESSION_NAME=technion
SETUP_ROS_STRING="source install/setup.bash"

CURRENT_DISPLAY=${DISPLAY}
if [ -z ${DISPLAY} ];
then
  echo "DISPLAY is not set"
  CURRENT_DISPLAY=:0
fi

if [ -z ${TMUX} ];
then
  TMUX= tmux new-session -s $SESSION_NAME -d
  echo "Starting new session."
else
  echo "Already in tmux, leave it first."
  exit
fi


# Make mouse useful in copy mode
tmux setw -g mouse on

tmux rename-window -t $SESSION_NAME "Main"
tmux send-keys -t $SESSION_NAME "$SETUP_ROS_STRING; ros2 launch launch/homify_launch.yaml" Enter
tmux split-window -t $SESSION_NAME
tmux send-keys -t $SESSION_NAME "$SETUP_ROS_STRING; ros2 launch launch/starling_offboard.yaml"
tmux split-window -t $SESSION_NAME
tmux send-keys -t $SESSION_NAME "$SETUP_ROS_STRING; ros2 launch launch/lpac_l1.yaml"
tmux select-layout -t $SESSION_NAME tiled   

# Add window to easily kill all processes
tmux new-window -t $SESSION_NAME -n "Kill"
tmux send-keys -t $SESSION_NAME "tmux kill-session -t ${SESSION_NAME}"

tmux select-window -t $SESSION_NAME:0
tmux -2 attach-session -t $SESSION_NAME
