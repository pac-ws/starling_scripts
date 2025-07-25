# pyright: reportAttributeAccessIssue=false
import pdb
import os
from os.path import isdir
import bag_utils as utils
from bag_utils import printR, printG, printB, printY
import re
import numpy as np
from numpy.typing import NDArray
import coverage_control
import matplotlib.pyplot as plt
import seaborn as sns
import seaborn.objects as so
from seaborn import plotting_context, axes_style
from colors import *
from bag_process import ProcessedBag

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

def plot_cost(normalized_cost_arr: NDArray[np.float32],
              t_fine: NDArray[np.float32],
              save_dir: str,
              bag_name: str,
              colors: list[str]
              ):
    fig, ax = plt.subplots(figsize=(ONE_COLUMN_WIDTH, FIGURE_HEIGHT))

    save_fn = save_dir + "/" + bag_name + "_cost.png"
    printB(f"Plotting and saving to {save_fn}...", end="")
    ax.plot(t_fine, normalized_cost_arr, color=colors[0])
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Normalized Coverage Cost')
    plt.tight_layout()
    utils.save_fig(fig, save_dir, bag_name + "_cost")
    printG("Done!")

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
                     t_coarse: NDArray[np.float32],
                     save_dir: str,
                     bag_name: str,
                     color_scheme: dict,
                     global_map: NDArray[np.float32] | None = None,
                     en_axis_labels = False,
                     en_grid = False
                     ):

    tmp_dir = save_dir + f"/{bag_name}_tmp"
    if not os.path.isdir(tmp_dir):
        os.makedirs(tmp_dir)

    print(BLUE + f"Plotting the system maps and saving to {tmp_dir}..." + RESET, end="")
    for i in range(system_maps.shape[0]):
        fig, ax = plt.subplots(figsize=(ONE_COLUMN_WIDTH, FIGURE_HEIGHT))
        if global_map is not None:
            system_map_masked = np.ma.masked_where(np.isnan(system_maps[i]), system_maps[i])
            ax.imshow(global_map, origin="lower", cmap="gray_r", alpha=0.25)
            ax.imshow(system_map_masked, origin="lower", cmap=color_scheme["idf"])
        else:
            ax.imshow(system_maps[i], origin="lower", cmap=color_scheme["idf"]) #pyright: ignore
        ax.scatter(poses[i,:,0], poses[i,:,1], marker=color_scheme["robot_marker"], color=color_scheme["robot"])
        if en_axis_labels:
            ax.set_xlabel("x (m)") 
            ax.set_ylabel("y (m)")
        else:
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
        ax.grid(visible=en_grid)

        utils.save_fig(fig, tmp_dir, f"{t_coarse[i]:.2f}_{i:06d}") 
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

def plot_bag(bag_data: ProcessedBag,
             save_dir: str,
             color_choice: str,
             ):
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    colors = seaborn_colors(catpuccin_colors)
    set_theme()

    plot_cost(bag_data.normalized_cost, bag_data.t_fine, save_dir, bag_data.bag_name, colors)
    #plot_trajectory(robot_poses, save_dir, bag_name, colors)
    plot_global_map(bag_data.global_map, save_dir, bag_data.bag_name + "_global")
    plot_system_maps(bag_data.system_maps,
                     bag_data.robot_poses,
                     bag_data.t_coarse,
                     save_dir,
                     bag_data.bag_name,
                     map_colors[color_choice],
                     bag_data.global_map
                     )

def plot_combined(bag_data_arr: list[ProcessedBag],
                  save_dir: str,
                  color_choice: str
                  ):

    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    colors = seaborn_colors(catpuccin_colors)
    set_theme()

    fig, ax = plt.subplots(figsize=(ONE_COLUMN_WIDTH, FIGURE_HEIGHT))
    save_fn = save_dir + "/" + "combined_cost.png"
    printB(f"Plotting and saving to {save_fn}...", end="")
    for i, data in enumerate(bag_data_arr):
        ax.plot(data.t_fine, data.normalized_cost, color=colors[i % len(colors)], label=data.bag_name)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Normalized Coverage Cost')
    plt.legend()
    plt.tight_layout()
    utils.save_fig(fig, save_dir, "combined_cost")
    printG("Done!")

    

    




