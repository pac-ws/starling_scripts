import pdb
import os
import re
import numpy as np
import coverage_control
from numpy.typing import NDArray
import matplotlib.pyplot as plt
from colors import *

class Robot:
    def __init__(self,
                 ns: str,
                 t_pos: NDArray[np.float64],
                 data_pos: NDArray[np.float32],
                 ):
        self.ns = ns
        self.t_pos = t_pos 
        self.data_pos = data_pos

def process_bag(bag_dict: dict):
    robots = []
    for k, v in bag_dict.items():
        if k == "/sim/all_robot_positions":
            all_pose_data = v[k]
            t_pos_arr = np.array(list(all_pose_data.keys()))
            t_pos_arr = np.sort(t_pos_arr)
            data_vec = [coverage_control.PointVector(all_pose_data[t]) for t in t_pos_arr]
        if re.match(r"r\d+", k):
            pose_data = v["pose"]
            t_pos_arr = np.array(list(pose_data.keys()))
            t_pos_arr = np.sort(t_pos_arr)
            data_vec = [pose_data[t] for t in t_pos_arr]
            #t_pos_arr -= t_pos_arr[0]
            data_arr = np.array(data_vec)
            robots.append(Robot(ns=k, t_pos=t_pos_arr, data_pos=data_arr))
    return robots


def get_robot_poses(bag_dict: dict):
    all_pose_data = bag_dict["sim"]["all_robot_positions"]
    t_pos_arr = np.array(list(all_pose_data.keys()))
    t_pos_arr = np.sort(t_pos_arr)
    data_vec = [coverage_control.PointVector(all_pose_data[t]) for t in t_pos_arr]
    return data_vec

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
        print(RED + f"Failed to create CoverageSystem: {e}" + RESET)
        return None
    return cc_env

def plot_bag(bag_dict: dict,
             params_file: str,
             idf_file: str,
             save_dir: str
             ):
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    cc_parameters = coverage_control.Parameters(params_file)

    #robots = process_bag(bag_dict)
    robot_poses = get_robot_poses(bag_dict)
    cc_env = create_cc_env(cc_parameters, idf_file, robot_poses[0])
    if cc_env is None:
        print(RED + "Exiting" + RESET)
        exit(0)
    total_steps = len(robot_poses)
    normalized_cost_arr = np.empty(total_steps, dtype=np.float64)
    initial_cost = cc_env.GetObjectiveValue()
    normalized_cost_arr[0] = 1.
    for i in range(1, total_steps):
        cc_env.SetGlobalRobotPositions(robot_poses[i])
        normalized_cost = cc_env.GetObjectiveValue() / initial_cost
        normalized_cost_arr[i] = normalized_cost
   
    plt.plot(normalized_cost_arr)
    plt.xlabel('Step')
    plt.ylabel('Normalized Coverage Cost')
    plt.grid(True)
    plt.show()
