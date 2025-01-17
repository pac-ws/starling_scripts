#!/bin/bash

# Use this script when the drone has no internet access. Pulls changes from the GCS.

# ----------------------------
# Color Definitions
# ----------------------------
RED='\033[0;31m'    # Red
GREEN='\033[0;32m'  # Green
YELLOW='\033[0;33m' # Yellow
NC='\033[0m'        # No Color

# ----------------------------
# Function Definitions
# ----------------------------

# Function to display usage information
usage() {
  echo "Usage: $0 --user <user> --dev [--help]"
  exit 1
}

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to handle errors with colored output
error_exit() {
  echo -e "${RED}Error: $1${NC}" >&2
  exit 1
}

# Function to display informational messages
info_message() {
  echo -e "${GREEN}$1${NC}"
}

# Function to display warnings
warning_message() {
  echo -e "${YELLOW}Warning: $1${NC}"
}

clone() {
    # 1 - Target directory
    # 2 - Source directory
    # 3 - User
    # 4 - IP
    # 5 - Entry
    # Create the target directory's parent directories if they don't exist
    mkdir -p "$(dirname "$1")"

    # Clone the repository
    if git clone "ssh://$3@$4:$2/.git" "$1"; then
      info_message "Successfully cloned '$5' into '$1'."
    else
      error_exit "Failed to clone repository '$5' into '$1'."
    fi
}

DEV_MODE=0

params="$(getopt -o 'd:h' -l user:,dir:,dev,help --name "$(basename "$0")" -- "$@")"
eval set -- "$params"
unset params

while true; do
    case ${1} in
        --user) 
            GCS_USER=$2
            if [ -z "$GCS_USER" ]; then
                echo -e "${RED}Error: --user requires an argument${NC}"
                usage
                exit 1
            fi
            shift 2
            ;;

        -d|--dir) 
            PAC_WS=$2
            if [ -z "$PAC_WS" ]; then
                echo -e "${RED}Error: [-d | --dir] requires an argument${NC}"
                usage
                exit 1
            fi
            shift 2
            ;;

        --dev) 
            DEV_MODE=1
            shift
            ;;
        -h|--help) 
            usage
            exit 0
            ;;
        --) 
            shift
            break
            ;;
        *) 
            usage
            exit 1
            ;;
    esac
done

case $GCS_USER in
    "fred")
        GCS_IP="192.168.0.204"
        GCS_PAC_WS="/home/fred/Penn/pac_ws"
        ;;
    "saurav")
        GCS_IP="192.168.0.158"
        GCS_PAC_WS="/home/saurav/pac_ws"
        ;;
    *)
        echo -e "${RED}Error: Unknown user $GCS_USER${NC}"
        usage
        exit 1
        ;;
esac

echo "GCS_USER: $GCS_USER"
echo "GCS_IP: $GCS_IP"
echo "GCS_PAC_WS: $GCS_PAC_WS"
        
# Check if PAC_WS is set
if [ -z "${PAC_WS}" ]; then
  error_exit "The -d <directory> argument is required."
fi

# Ensure PAC_WS is an absolute path
PAC_WS=$(realpath "${PAC_WS}")

# Check if PAC_WS is a directory
if [ ! -d "${PAC_WS}" ]; then
  error_exit "'${PAC_WS}' is not a directory."
fi

# Ensure PAC_WS/src exists
if [ ! -d "${PAC_WS}/src" ]; then
  mkdir -p "${PAC_WS}/src"
fi

REPOS=(
    "pac_ws_setup"
    "pt"
    "launch"
    "configs"
    "src/px4_homify"
    "src/async_pac_gnn_py"
    "src/async_pac_gnn_interfaces"
    "src/coveragecontrol_sim"
    "src/starling_offboard_cpp"
    "src/starling_demos_cpp"
)

if [ $DEV_MODE -eq 1 ]; then
  REPOS+=(
    "docker"
    "starling_scripts"
    "src/px4_multi_sim"
    "src/cc_rviz"
    "src/gcs"
  )
fi

CLONE_ALL=0

for ENTRY in "${REPOS[@]}"; do
  # Skip empty lines or lines starting with '#'
  [[ -z "$ENTRY" || "$ENTRY" == \#* ]] && continue

  # Combine PAC_WS and RELATIVE_TARGET_DIR to get the absolute target directory
  TARGET_DIR="${PAC_WS}/${ENTRY}"

  SOURCE_DIR="${GCS_PAC_WS}/${ENTRY}"

  info_message "Processing repository '$ENTRY' at '$TARGET_DIR'..."

  if [[ -d "$TARGET_DIR/.git" ]]; then
    info_message "Repository already exists. Checking for updates..."
    cd "$TARGET_DIR" || error_exit "Failed to navigate to '$TARGET_DIR'."

    # Check for local changes
    if [[ -n $(git status --porcelain) ]]; then
      warning_message "There are local changes in '$TARGET_DIR'."
    fi

    git fetch "ssh://$GCS_USER@$GCS_IP:$SOURCE_DIR/.git" || error_exit "Failed to fetch updates from '$SOURCE_DIR'."

    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse FETCH_HEAD || echo "no_upstream")
    BASE=$(git merge-base @ @{u} 2>/dev/null || echo "no_merge_base")

    if [ "$LOCAL" = "$REMOTE" ]; then
      info_message "Repository '$TARGET_DIR' is up-to-date."
    elif [ "$LOCAL" = "$BASE" ]; then
      info_message "Updating repository '$TARGET_DIR'..."
      if git -C "$TARGET_DIR" pull "ssh://$GCS_USER@$GCS_IP:$SOURCE_DIR/.git"; then
        info_message "Successfully updated repository at '$TARGET_DIR'."
        # If the directory was pac_ws_setup, print warning to re-run setup_pac_ws.bash
        if [[ "$ENTRY" == "pac_ws_setup" ]]; then
          echo -e "${RED}Please re-run the setup_pac_ws.bash script to ensure the changes are applied.${NC}"
        fi
      else
        error_exit "Failed to update repository at '$TARGET_DIR'."
      fi
    elif [ "$REMOTE" = "$BASE" ]; then
      warning_message "Local commits found in '$TARGET_DIR' that are not in the remote repository."
    else
      warning_message "Git branches have diverged in '$TARGET_DIR'. Manual intervention is required."
    fi

  else
    warning_message "Repository does not exist. Cloning repository '$ENTRY' into '$TARGET_DIR'."
    if [ $CLONE_ALL -eq 0 ]; then
      read -p "Do you want to clone all missing repositories? This will set the remote origin to the GCS [y/n]: " -n 1 -r
      echo
      if [[ $REPLY =~ ^[Yy]$ ]]; then
        CLONE_ALL=1
      else
        CLONE_ALL=-1
      fi
    fi

    if [ $CLONE_ALL -eq -1 ]; then
        read -p "Proceed? This will set the remote origin of '$ENTRY' to the GCS. [y/n]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
          echo "Skipping repository '$ENTRY'."
          continue
        else
            clone "$TARGET_DIR" "$SOURCE_DIR" "$GCS_USER" "$GCS_IP" "$ENTRY"
        fi
    elif [ $CLONE_ALL -eq 1 ]; then
        clone "$TARGET_DIR" "$SOURCE_DIR" "$GCS_USER" "$GCS_IP" "$ENTRY"
    fi
  fi

  echo "----------------------------------------"
done

#ssh r16 'docker logs pac-m0054 --follow'

