import pdb
import os
from os.path import isdir
import bag_utils as utils
import re
import numpy as np
from numpy.typing import NDArray
import coverage_control
import matplotlib.pyplot as plt
import seaborn as sns
import seaborn.objects as so
from seaborn import plotting_context, axes_style
from colors import *

ONE_COLUMN_WIDTH = 3.5
TWO_COLUMN_WIDTH = 7.16
LEGEND_WIDTH = 0.5
FIGURE_HEIGHT = 3.5


def seaborn_colors(colors : list[str]) -> list[[float]]:
    sns_colors = []
    for color in colors:
        m = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d\.]+)\)', color)
        if not m:
            print("invalid rgba string")
            exit(1)
        r, g, b, a = m.groups()
        r = int(r) / 255
        g = int(g) / 255
        b = int(b) / 255
        a = float(a)
        sns_colors.append((r, g, b, a))
    return sns_colors
        
def set_theme():
    sns.set_theme(
        context="paper",
        style="ticks",
        font_scale=0.8,  # default font size is 10pt
        rc={ "figure.figsize": (2.0, 3.5),
            "figure.dpi": 300,
            "savefig.dpi": 300,
            #"text.usetex": True,
            #"text.latex.preamble": r"\usepackage{amsmath}",
            "lines.linewidth": 0.7,
            "axes.linewidth": 0.7,
            "axes.grid": True,
            "grid.linestyle": "--",
            "grid.linewidth": 0.5,
            "pdf.fonttype": 42,
        },
    )

def so_theme():
    return (
        plotting_context("paper", font_scale=1.0)
        | axes_style("ticks")
        | {
            "figure.figsize": (2.0, 3.5),
            "figure.dpi": 300,
            "savefig.dpi": 300,
            #"text.usetex": True,
            #"text.latex.preamble": r"\usepackage{amsmath}",
            "lines.linewidth": 0.7,
            "axes.linewidth": 0.7,
            "axes.grid": True,
            "grid.linestyle": "--",
            "grid.linewidth": 0.5,
            "pdf.fonttype": 42,
        }
    )

def plot_cost(cc_env: coverage_control.CoverageSystem,
              robot_poses: list[coverage_control.PointVector],
              save_dir: str,
              bag_name: str,
              colors: list[str]
              ):
    fig, ax = plt.subplots(figsize=(ONE_COLUMN_WIDTH, FIGURE_HEIGHT))

    total_steps = len(robot_poses)
    normalized_cost_arr = np.empty(total_steps, dtype=np.float64)

    print(BLUE + f"Evaluating coverage cost for {bag_name}..." + RESET, end="")

    initial_cost = cc_env.GetObjectiveValue()
    normalized_cost_arr[0] = 1.
    for i in range(1, total_steps):
        cc_env.SetGlobalRobotPositions(robot_poses[i])
        normalized_cost = cc_env.GetObjectiveValue() / initial_cost
        normalized_cost_arr[i] = normalized_cost

    print(GREEN + "Done!" + RESET)

    save_fn = save_dir + "/" + bag_name + "_cost.png"
    print(BLUE + f"Plotting and saving to {save_fn}..." + RESET, end="")

    ax.plot(normalized_cost_arr, color=colors[0])
    ax.set_xlabel('Step')
    ax.set_ylabel('Normalized Coverage Cost')
    plt.tight_layout()
    utils.save_fig(fig, save_dir, bag_name + "_cost")
    print(GREEN + "Done!" + RESET)

def plot_trajectory(robot_poses: list[coverage_control.PointVector],
                    save_dir: str,
                    bag_name: str,
                    colors: list[str]
                    ):
    fig, ax = plt.subplots(figsize=(ONE_COLUMN_WIDTH, FIGURE_HEIGHT))
    save_fn = save_dir + "/" + bag_name + "_traj.png"
    print(BLUE + f"Plotting the trajectories and saving to {save_fn}..." + RESET, end="")
    # Get the trajectories
    total_steps = len(robot_poses)
    for i in range(0, len(robot_poses[0])):
        data_arr = np.empty((total_steps, 2), dtype=np.float64)
        for t in range(0, total_steps):
            data_arr[t] = robot_poses[t][i]
        color = colors[i % len(colors)]
        ax.plot(data_arr[:,0],
                   data_arr[:,1],
                   color=color
                   )
        ax.plot(data_arr[0,0],
                   data_arr[0,1],
                   color="red",
                   marker="*",
                   markersize=1
                   )
        ax.plot(data_arr[-1,0],
                   data_arr[-1,1],
                   color="black",
                   marker="x",
                   markersize=1
                   )
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    ax.set_xlim([0,512])
    ax.set_ylim([0,512])
    plt.tight_layout
    utils.save_fig(fig, save_dir, bag_name+"_traj")
    print(GREEN + "Done!" + RESET)

def plot_system_maps(system_maps: NDArray[np.float32],
                     poses: NDArray[np.float32],
                     t_maps: NDArray[np.float32],
                     save_dir: str,
                     filename: str,
                     color_scheme: dict,
                     global_map: NDArray[np.float32] | None = None,
                     en_axis_labels = False,
                     en_grid = False
                     ):
    t_maps_normalized = t_maps -  t_maps[0]

    tmp_dir = save_dir + "/tmp"
    if not os.path.isdir(tmp_dir):
        os.makedirs(save_dir + "/tmp")

    print(BLUE + f"Plotting the system maps and saving to {tmp_dir}..." + RESET, end="")
    for i in range(system_maps.shape[0]):
        fig, ax = plt.subplots(figsize=(ONE_COLUMN_WIDTH, FIGURE_HEIGHT))
        if global_map is not None:
            system_map_masked = np.ma.masked_where(np.isnan(system_maps[i]), system_maps[i])
            ax.imshow(global_map, origin="lower", cmap="gray_r", alpha=0.25)
            ax.imshow(system_map_masked, origin="lower", cmap=color_scheme["idf"])
        else:
            ax.imshow(system_maps[i], origin="lower", cmap=color_scheme["idf"])
        ax.scatter(poses[i,:,0], poses[i,:,1], marker=color_scheme["robot_marker"], color=color_scheme["robot"])
        if en_axis_labels:
            ax.set_xlabel("x (m)") 
            ax.set_ylabel("y (m)")
        else:
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
        ax.grid(visible=en_grid)

        utils.save_fig(fig, tmp_dir, f"{t_maps_normalized[i]}_{i:06d}") 
        plt.close()
    print(GREEN + "Done!" + RESET)

def plot_global_map(global_map: NDArray[np.float32],
                    save_dir: str,
                    filename: str
                    ):
    save_fn = save_dir + "/" + filename + ".png"
    print(BLUE + f"Plotting the global map and saving to {save_fn}..." + RESET, end="", flush=True)
    plot_map(global_map, save_dir, filename)
    print(GREEN + "Done!" + RESET)
    plt.close()

def plot_map(map: NDArray[np.float32],
             save_dir: str,
             filename: str
             ):
    fig, ax = plt.subplots(figsize=(ONE_COLUMN_WIDTH, FIGURE_HEIGHT))
    ax.imshow(map, origin="lower")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    utils.save_fig(fig, save_dir, filename) 

def plot_bag(bag_dict: dict,
             params_file: str,
             idf_file: str,
             save_dir: str,
             bag_name: str,
             color_choice: str,
             ):
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    colors = seaborn_colors(catpuccin_colors)
    set_theme()

    cc_parameters = coverage_control.Parameters(params_file)
    total_time = bag_dict["total_time"]

    mission_control_data, t_mission_control = utils.get_mission_control(bag_dict)
    start_time, stop_time = utils.experiment_window(mission_control_data, t_mission_control)

    robot_poses, t_poses  = utils.get_robot_poses(bag_dict)
    poses_start = utils.align(t_poses, start_time)
    poses_stop  = utils.align(t_poses, stop_time)
    robot_poses = robot_poses[poses_start:poses_stop]
    t_poses = t_poses[poses_start:poses_stop]

    global_map_upscaled, system_maps_upscaled, t_system_maps = utils.get_maps(bag_dict)
    maps_start = utils.align(t_system_maps, start_time)
    maps_stop = utils.align(t_system_maps, stop_time)
    system_maps_upscaled = system_maps_upscaled[maps_start:maps_stop]
    t_system_maps = t_system_maps[maps_start:maps_stop]

    # Create a mapping of poses to system_maps
    X, Y = np.meshgrid(t_poses, t_system_maps) 
    pose_indices = np.argmin(np.abs(X - Y), axis=1)
    poses_for_maps = np.array(robot_poses)[pose_indices]

    # Used for simulating with the same start conditions
    utils.create_pose_file(poses_for_maps[0], bag_name)

    cc_env = utils.create_cc_env(cc_parameters, idf_file, robot_poses[0])
    if cc_env is None:
        print(RED + "Exiting" + RESET)
        exit(1)
    plot_cost(cc_env,robot_poses, save_dir, bag_name, colors)
    plot_trajectory(robot_poses, save_dir, bag_name, colors)
    plot_global_map(global_map_upscaled, save_dir, bag_name + "_global")
    plot_system_maps(system_maps_upscaled,
                     poses_for_maps,
                     t_system_maps,
                     save_dir,
                     bag_name + "_system",
                     map_colors[color_choice],
                     global_map_upscaled
                     )
