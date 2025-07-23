import pdb
import os
import numpy as np
from numpy.typing import NDArray
import matplotlib.pyplot as plt
import coverage_control
from scipy import ndimage
from colors import *

class Robot:
    def __init__(self,
                 ns: str,
                 data_pos: NDArray[np.float32],
                 ):
        self.ns = ns
        self.data_pos = data_pos

def save_fig(fig: plt.Figure,
             figure_dir: str,
             filename_no_ext: str
             ):
    fig.savefig(figure_dir + "/" + filename_no_ext + ".pdf")
    fig.savefig(figure_dir + "/" + filename_no_ext + ".png")

def get_robot_poses(bag_dict: dict) -> tuple[list[coverage_control.PointVector], NDArray[np.float32]]:
    all_pose_data = bag_dict["sim"]["all_robot_positions"]
    t_pos_arr = np.array(list(all_pose_data.keys()))
    t_pos_arr = np.sort(t_pos_arr)
    data_vec = [coverage_control.PointVector(np.clip(all_pose_data[t], 1, 512)) for t in t_pos_arr] # TODO BAD!
    return data_vec, t_pos_arr

def get_mission_control(bag_dict: dict) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    mission_control_data = np.array(list(bag_dict["mission_control"]["mission_control"].values()))
    t_mission_control = np.array(list(bag_dict["mission_control"]["mission_control"].keys()))
    return mission_control_data, t_mission_control

def upscale_map(map: NDArray[np.float32], map_size=512, binning_factor = 2, order=1):
    # Assumes binning
    x_coord = map[:, 0].astype(int) // binning_factor
    y_coord = map[:, 1].astype(int) // binning_factor
    val = map[:, 2]
    dense_size = map_size // binning_factor
    map_dense = np.full((dense_size, dense_size), np.nan) 
    for i in range(map.shape[0]):
        map_dense[y_coord[i], x_coord[i]] = val[i]
    map_upscaled = np.clip(ndimage.zoom(map_dense, 2, order=order), 0, 1)
    return map_upscaled

def get_maps(bag_dict: dict) -> tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
    # Only need one global map
    global_map = next(iter(bag_dict["sim"]["global_map"].values()), None)
    if global_map is None:
        print(RED + "Error: global map is none. Exiting..." + RESET)
        exit(1)
    global_map_upscaled = upscale_map(global_map, order=3)

    # System maps are indexed by timestep
    system_maps = list(bag_dict["sim"]["system_map"].values())
    t_system_maps = np.array(list(bag_dict["sim"]["system_map"].keys()))
    system_maps_upscaled = np.zeros((len(t_system_maps), 512,512), dtype=np.float32) # TODO fix magic numbers
    for i in range(system_maps_upscaled.shape[0]):
        system_maps_upscaled[i] = upscale_map(system_maps[i])
    return global_map_upscaled, system_maps_upscaled, t_system_maps

def align(arr: NDArray[np.float64], 
          val: np.float64
          ) -> np.int64:
    return np.argmin(np.abs(arr - val))

def experiment_window(mission_control_data: NDArray[bool], 
                      t_mission_control: NDArray[np.float32]
                      ) -> tuple[np.float64, np.float64]:
    takeoff = mission_control_data[:,2]
    landing = mission_control_data[:,3]

    idx_start = np.argmax(np.diff(takeoff, n=1))
    idx_stop = np.argmax(np.diff(landing, n=1))

    start_time = t_mission_control[idx_start] / 1e9
    stop_time = t_mission_control[idx_stop] / 1e9
    return start_time, stop_time

def create_cc_env(cc_parameters: coverage_control.Parameters,
                  idf_path: str,
                  robot_poses: coverage_control.PointVector
                  ) -> coverage_control.CoverageSystem | None:
    if not os.path.isfile(idf_path):
        return False
    try:
        world_idf = coverage_control.WorldIDF(cc_parameters, idf_path)
        cc_env = coverage_control.CoverageSystem(
                cc_parameters,
                world_idf,
                robot_poses)
    except Exception as e:
        print(RED + f"Failed to create CoverageSystem" + RESET)
        return None
    return cc_env

def create_pose_file(robot_poses: NDArray[np.float32],
                     bag_name: str
                     ):
    fp = f"/workspace/px4_multi_sim/robot_poses_{bag_name}.sh"
    print(BLUE + f"Creating pose file for sim testing at {fp} ..." + RESET, flush=True)
    with open(fp, "w") as f:
        for i in range(robot_poses.shape[0]):
            f.write(f"{i} {robot_poses[i,0]} {robot_poses[i,1]} 1.5708\n")
        f.close()
    print(GREEN + "Done!" + RESET)
        
        
