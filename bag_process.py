import pdb
import pickle
from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray
import coverage_control
import bag_utils as utils
from bag_utils import printC
from colors import *

@dataclass
class ProcessedBag:
    bag_name: str
    robot_poses: NDArray[np.float32]
    normalized_cost: NDArray[np.float32]
    global_map: NDArray[np.float32]
    system_maps: NDArray[np.float32]
    t_coarse: NDArray[np.float32]
    t_fine: NDArray[np.float32]

def calc_cost(cc_env: coverage_control.CoverageSystem,
              robot_poses: list[coverage_control.PointVector],
              ):
    total_steps = len(robot_poses)
    normalized_cost_arr = np.empty(total_steps, dtype=np.float64)
    initial_cost = cc_env.GetObjectiveValue()
    normalized_cost_arr[0] = 1.
    for i in range(1, total_steps):
        cc_env.SetGlobalRobotPositions(robot_poses[i])
        normalized_cost = cc_env.GetObjectiveValue() / initial_cost
        normalized_cost_arr[i] = normalized_cost
    return normalized_cost_arr

def process_bag(bag_dict: dict,
                params_file: str,
                idf_file: str,
                save_dir: str,
                bag_name: str,
                save: bool = True
                ):
    cc_parameters = coverage_control.Parameters(params_file)
    total_time = bag_dict["total_time"]

    mission_control_data, t_mission_control = utils.get_mission_control(bag_dict)
    start_time, stop_time = utils.experiment_window(mission_control_data, t_mission_control)

    robot_poses, t_poses  = utils.get_robot_poses(bag_dict)
    poses_start = utils.align(t_poses, start_time)
    poses_stop  = utils.align(t_poses, stop_time)
    robot_poses = robot_poses[poses_start:poses_stop]
    t_fine = t_poses[poses_start:poses_stop]

    global_map_upscaled, system_maps_upscaled, t_system_maps = utils.get_maps(bag_dict)
    maps_start = utils.align(t_system_maps, start_time)
    maps_stop = utils.align(t_system_maps, stop_time)
    system_maps_upscaled = system_maps_upscaled[maps_start:maps_stop]
    t_coarse = t_system_maps[maps_start:maps_stop]

    X, Y = np.meshgrid(t_fine, t_coarse) 
    pose_indices = np.argmin(np.abs(X - Y), axis=1)
    poses_for_maps = np.array(robot_poses)[pose_indices]

    # Creates a file containing start positions of the robots from the current bag.
    # Allows future simulation runs to be initialized with the same start positions.
    utils.create_pose_file(poses_for_maps[0], bag_name)

    cc_env = utils.create_cc_env(cc_parameters, idf_file, robot_poses[0])
    if cc_env is None:
        printC("Exiting...", RED)
        exit(1)

    printC(f"Evaluating coverage cost for {bag_name}...", BLUE, end="")
    normalized_cost = calc_cost(cc_env, robot_poses)
    printC("Done!", GREEN)

    t_coarse -= t_coarse[0]
    t_fine -= t_fine[0]

    pb = ProcessedBag(bag_name, 
                      poses_for_maps,
                      normalized_cost,
                      global_map_upscaled,
                      system_maps_upscaled,
                      t_coarse,
                      t_fine
                      )
    if save:
        save_path = save_dir + "/" + bag_name + "_processed.pkl"
        printC(f"Saving to {save_path}...", BLUE, end="")
        with open(save_path, "wb") as f:
            pickle.dump(pb, f, protocol=pickle.HIGHEST_PROTOCOL)
        printC("Done!", GREEN)
    return pb
