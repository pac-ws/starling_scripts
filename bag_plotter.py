# pyright: reportAttributeAccessIssue=false
import pdb
import os
from os.path import isdir
import bag_utils as utils
from bag_utils import printC
import re
import numpy as np
from numpy.typing import NDArray
import coverage_control
import matplotlib.pyplot as plt
import cv2
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
    printC(f"Plotting and saving to {save_fn}...", BLUE, end="")
    ax.plot(t_fine, normalized_cost_arr, color=colors[0])
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Normalized Coverage Cost')
    plt.tight_layout()
    utils.save_fig(fig, save_dir, bag_name + "_cost")
    printC("Done!", GREEN)

def plot_trajectory(robot_poses: list[coverage_control.PointVector],
                    save_dir: str,
                    bag_name: str,
                    colors: list[str]
                    ):
    fig, ax = plt.subplots(figsize=(ONE_COLUMN_WIDTH, FIGURE_HEIGHT))
    save_fn = save_dir + "/" + bag_name + "_traj.png"
    printC(f"Plotting the trajectories and saving to {save_fn}...", BLUE, end="")
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
    printC("Done!", GREEN)

def plot_system_maps(system_maps: NDArray[np.float32],
                     poses: NDArray[np.float32],
                     t_coarse: NDArray[np.float32],
                     save_dir: str,
                     bag_name: str,
                     color_scheme: dict,
                     global_map: NDArray[np.float32] | None = None,
                     en_axis_labels = False,
                     en_grid = False,
                     generate_video: bool = True
                     ):

    tmp_dir = save_dir + f"/{bag_name}_tmp"
    if not os.path.isdir(tmp_dir):
        os.makedirs(tmp_dir)

    printC(f"Plotting the system maps and saving to {tmp_dir}...", BLUE, end="")
    for i in range(system_maps.shape[0]):
        fig, ax = plt.subplots(figsize=(ONE_COLUMN_WIDTH, FIGURE_HEIGHT))
        if global_map is not None:
            system_map_masked = np.ma.masked_where(np.isnan(system_maps[i]), system_maps[i])
            ax.imshow(global_map, origin="lower", cmap="gray_r", alpha=0.5)
            ax.imshow(system_map_masked, origin="lower", cmap=color_scheme["idf"], vmin=0.0, vmax=1.0)
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
    printC("Done!", GREEN)

    if generate_video:
        printC(f"Generating video and saving in {save_dir}...", BLUE, end="")
        create_sys_map_video(tmp_dir, save_dir + "/" + bag_name + "_sys.mp4")
        printC("Done!", GREEN)

@staticmethod
def create_sys_map_video(images_path, video_name, fps=10):
    images = [img for img in os.listdir(images_path) if img.endswith(".png")]
    images.sort()
    frame = cv2.imread(os.path.join(images_path, images[0]))
    height, width, layers = frame.shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  
    video = cv2.VideoWriter(video_name, fourcc, fps, (width, height))
    for image in images:
        video.write(cv2.imread(os.path.join(images_path, image)))
    cv2.destroyAllWindows()
    video.release()

def plot_global_map(global_map: NDArray[np.float32],
                    save_dir: str,
                    filename: str,
                    color_scheme: dict,
                    robot_poses: NDArray[np.float32] | None = None,
                    en_axis_labels: bool = False,
                    en_grid: bool = False,
                    alt_marker_colors: list[float] | None = None # used if plotting multiple bags
                    ):
    save_fn = save_dir + "/" + filename + ".png"
    printC(f"Plotting the global map and saving to {save_fn}...", BLUE, end="", flush=True)
    fig, ax = plt.subplots(figsize=(ONE_COLUMN_WIDTH, FIGURE_HEIGHT))
    ax.imshow(global_map, origin="lower", cmap=color_scheme["idf"], vmin=0.0, vmax=1.0)
    if robot_poses is not None:
        for i in range(robot_poses.shape[0]):
            if alt_marker_colors is not None and robot_poses.shape[0] > 1:
                color = alt_marker_colors[i % len(alt_marker_colors)]
            else:
                color = color_scheme["robot"]
            ax.scatter(robot_poses[:,0], robot_poses[:,1], marker=color_scheme["robot_marker"], color=color)
    if en_axis_labels:
        ax.set_xlabel("x (m)") 
        ax.set_ylabel("y (m)")
    else:
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
    ax.grid(visible=en_grid)

    utils.save_fig(fig, save_dir, filename) 
    plt.close()
    printC("Done!", GREEN)

def plot_bag(bag_data: ProcessedBag,
             save_dir: str,
             color_choice: str,
             global_map_time: float = 60.
             ):
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    colors = seaborn_colors(catpuccin_colors)
    set_theme()

    plot_cost(bag_data.normalized_cost, bag_data.t_fine, save_dir, bag_data.bag_name, colors)
    #plot_trajectory(robot_poses, save_dir, bag_name, colors)

    global_map_idx = np.argmin(np.abs(bag_data.t_coarse - global_map_time))
    plot_global_map(bag_data.global_map,
                    save_dir,
                    bag_data.bag_name + f"_global_{global_map_time}",
                    map_colors[color_choice],
                    bag_data.robot_poses[global_map_idx]
                    )
    plot_system_maps(bag_data.system_maps,
                     bag_data.robot_poses,
                     bag_data.t_coarse,
                     save_dir,
                     bag_data.bag_name,
                     map_colors[color_choice],
                     bag_data.global_map
                     )

def plot_combined_cost(bag_data_arr: list[ProcessedBag],
                       save_dir: str,
                       color_choice: str
                      ):

    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    colors = seaborn_colors(catpuccin_colors)
    set_theme()

    fig, ax = plt.subplots(figsize=(ONE_COLUMN_WIDTH, FIGURE_HEIGHT))
    save_fn = save_dir + "/" + "combined_cost.png"
    printC(f"Plotting and saving to {save_fn}...", GREEN, end="")
    for i, data in enumerate(bag_data_arr):
        ax.plot(data.t_fine, data.normalized_cost, color=colors[i % len(colors)], label=data.bag_name)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Normalized Coverage Cost')
    plt.legend()
    plt.tight_layout()
    utils.save_fig(fig, save_dir, "combined_cost")
    printC("Done!", GREEN)
    plt.close()


def plot_combined_global_map(bag_data_arr: list[ProcessedBag],
                             save_dir: str,
                             color_choice: str
                            ):
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    colors = seaborn_colors(catpuccin_colors)
    set_theme()

    fig, ax = plt.subplots(figsize=(ONE_COLUMN_WIDTH, FIGURE_HEIGHT))
    times_to_plot = [0.0, 60.0]

    for t in times_to_plot:
        robot_poses = []
        for bag_data in bag_data_arr:
            pose_idx = np.argmin(np.abs(bag_data.t_coarse - t))
            robot_poses.append(bag_data.robot_poses[pose_idx])

        printC(f"Plotting the combined global_map for t=${t}s...", BLUE, end="")
        plot_global_map(bag_data_arr[0].global_map,
                        save_dir,
                        f"global_combined_{t}",
                        map_colors[color_choice],
                        robot_poses,
                        alt_marker_colors=colors
                        )
        printC("Done!", GREEN)
