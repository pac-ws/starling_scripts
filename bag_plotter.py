import pdb
import os
import re
import numpy as np
import coverage_control
from numpy.typing import NDArray
import matplotlib.pyplot as plt
import seaborn as sns
import seaborn.objects as so
from seaborn import plotting_context, axes_style
from colors import *

ONE_COLUMN_WIDTH = 3.5
TWO_COLUMN_WIDTH = 7.16
LEGEND_WIDTH = 0.5
FIGURE_HEIGHT = 2.5

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

def seaborn_colors(colors : list[str]) -> list[[float]]:
    sns_colors = []
    for color in colors:
        m = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d\.]+)\)', color)
        if not m:
            print("invalid rgba string")
            exit(0)
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
            robots.append(Robot(ns=k, data_pos=data_arr))
    return robots


def get_robot_poses(bag_dict: dict):
    all_pose_data = bag_dict["sim"]["all_robot_positions"]
    t_pos_arr = np.array(list(all_pose_data.keys()))
    t_pos_arr = np.sort(t_pos_arr)
    data_vec = [coverage_control.PointVector(np.clip(all_pose_data[t], 1, 512)) for t in t_pos_arr] # TODO BAD!
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
    save_fig(fig, save_dir, bag_name + "_cost")
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
    plt.tight_layout
    save_fig(fig, save_dir, bag_name+"_traj")
    print(GREEN + "Done!" + RESET)


def plot_bag(bag_dict: dict,
             params_file: str,
             idf_file: str,
             save_dir: str,
             bag_name: str,
             ):
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    catpuccin_colors = [
        'rgba(239, 159, 118, 1.0)',  # Peach
        'rgba(166, 209, 137, 1.0)',  # Green
        'rgba(202, 158, 230, 1.0)',  # Mauve
        'rgba(133, 193, 220, 1.0)',  # Sapphire
        'rgba(231, 130, 132, 1.0)',  # Red
        'rgba(129, 200, 190, 1.0)',  # Teal
        'rgba(242, 213, 207, 1.0)',  # Rosewater
        'rgba(229, 200, 144, 1.0)',  # Yellow
        'rgba(108, 111, 133, 1.0)',  # subtext0
    ]

    colors = seaborn_colors(catpuccin_colors)
    set_theme()

    cc_parameters = coverage_control.Parameters(params_file)

    robot_poses = get_robot_poses(bag_dict)
    cc_env = create_cc_env(cc_parameters, idf_file, robot_poses[0])
    if cc_env is None:
        print(RED + "Exiting" + RESET)
        exit(0)
    plot_cost(cc_env,robot_poses, save_dir, bag_name, colors)
    plot_trajectory(robot_poses, save_dir, bag_name, colors)


