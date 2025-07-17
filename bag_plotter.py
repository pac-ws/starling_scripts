import pdb
import os
import re
import numpy as np
import coverage_control as cc
from coverage_control import CoverageSystem
from coverage_control import IOUtils
from coverage_control import WorldIDF
from numpy.typing import NDArray
import matplotlib.pyplot as plt

class Robot:
    def __init__(self,
                 ns: str,
                 data: NDArray[np.float32],
                 ):
        self.ns = ns
        self.data = data
        

def plot_bag(bag_dict: dict, save_dir: str):
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    robots = []
    for k, v in bag_dict.items():
        if re.match(r"r\d+", k):
            pose_data = v["pose"]
            t_pos_arr = np.array(list(pose_data.keys()))
            #t_pos_arr = sorted(t_pos_arr)
            data_vec = [v[t] for t in t_pos_arr]
            t_pos_arr -= t_pos_arr[0]
            data_arr = np.array(data_vec)


            #robots.append(Robot(ns=v, data=
