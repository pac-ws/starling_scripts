A collection of helper scripts for setting up the Starling drones.


## Clone to starling
```
git clone https://github.com/pac-ws/starling_scripts.git /data/starling_scripts
```

## Check the current status
```
bash /data/starling_scripts/setup-local.bash --status
```

## Install
Modify the list of flags for the following command to resolve any failures revealed in the status check.
For a complete setup:
```
export ROS_NAMESPACE=<robot_number>
```
```
bash /data/starling_scripts/setup-local.bash --ros ${ROS_NAMESPACE} --params --docker --offboard --disable-cams --pac ${ROS_NAMESPACE}
```
To update only pac:
```
bash /data/starling_scripts/setup-local.bash --pac ${ROS_NAMESPACE}
```
