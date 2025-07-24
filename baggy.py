import bag_reader
import bag_process
import bag_plotter
import argparse
import os
import pickle
from colors import *

import pdb

def list_directories(dir: str, 
                     all: bool, 
                     match: str,
                     single: str
                     ) -> list[str]:
    bags = os.listdir(dir)
    if all:
        return bags
    elif match:
        filtered_bags = []
        for d in bags:
            if d.__contains__(match):
                filtered_bags.append(d)
        return filtered_bags
    elif single:
        filtered_bags = [single]
        if not os.path.isdir(dir + "/" + single):
            print(RED + "Error: The specified path is not a directory." + RESET)
        return filtered_bags
    else:
        print(RED + "Error: missing at least one input (all, match, single) when listing directories.\
                Exiting..." + RESET)
        exit(0)

def load_bag(filepath: str):
    with open(filepath, "rb") as f:
        bag_dict = pickle.load(f)
    return bag_dict

def main(args):
    bags = list_directories(args.dir, args.all, args.match, args.single)
    data = []
    for b in bags:
        if args.command == "extract":
            filepath = args.dir + "/" + b
            bag_reader.extract_bag(filepath)
        elif args.command == "plot":
            filepath = args.dir + "/" + b + "/" + b + ".pkl" # pkl file shares name of bag dir
            bag_dict = load_bag(filepath)
            data.append(bag_process.process_bag(bag_dict, args.params, args.idf, args.output, b))
            if args.single:
                bag_plotter.plot_bag(data[0], args.output, args.color)
                return
    if args.command == "plot":
        bag_plotter.plot_combined(data, args.output, args.color)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="bag_plotter.py",
                                     description="Reads bag files and generates plots"
                                     )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Loading
    parser_extractor = subparsers.add_parser("extract", help="Extract data from bag files, generating a friendlier data file")
    parser_extractor.add_argument("-d",
                               "--dir",
                               type=str,
                               default="/workspace/bags",
                               help="Directory containing bag files. default: /workspace/bags"
                               )
    parser_ext_xor = parser_extractor.add_mutually_exclusive_group(required=True)
    parser_ext_xor.add_argument("-a", "--all", action="store_true", help="Process all bag files\
            in the given directory")
    parser_ext_xor.add_argument("-m", "--match", type=str, help="Process all bag files that\
            contain a given substring")
    parser_ext_xor.add_argument("-s", "--single", type=str, help="Path to a specific bag file")

    # Calculate Cost
    parser_cost = subparsers.add_parser("cost", help="Calculate the raw coverage cost of the bag file(s)")
    parser_cost.add_argument("-d",
                             "--dir",
                             type=str,
                             default="/workspace/bags",
                             help="Directory containing bag files. default: /workspace/bags"
                             )
    parser_cost.add_argument("-c",
                             "--config",
                             type=str,
                             default="/workspaces/configs/penn_envs",
                             help="Directory containing the IDF enviornment files.\
                                     default: /workspace/configs/penn_envs"
                             )
    parser_cost_xor = parser_cost.add_mutually_exclusive_group(required=True)
    parser_cost_xor.add_argument("-a", "--all", action="store_true", help="Plot bags in the given directory")
    parser_cost_xor.add_argument("-m", "--match", type=str, help="Plot a subsection of bags in the directory")
    parser_cost_xor.add_argument("-s", "--single", type=str, help="Plot a specific bag file")

    # Plotting
    parser_plotter = subparsers.add_parser("plot", help="Plot bag files [Requires processing first!]")
    parser_plotter.add_argument("-d",
                               "--dir",
                               type=str,
                               default="/workspace/bags",
                               help="Directory containing bag files. default: /workspace/bags"
                               )
    parser_plotter.add_argument("-o",
                                "--output",
                                type=str,
                                default="/workspace/figures",
                                help="Output directory for generated figures. default: /workspace/figures"
                                )
    parser_plotter.add_argument("-p",
                                "--params",
                                type=str,
                                default="/workspace/pt/models_256/coverage_control_params_512.toml",
                                help="Coverage control parameters file.\
                                        default: /workspace/pt/models_256/coverage_control_params_512.toml"
                                )
    parser_plotter.add_argument("-i",
                                "--idf",
                                type=str,
                                default="/workspace/configs/penn_envs/10r_2.env",
                                help="Importance density function file.\
                                        default: /workspace/configs/penn_envs/10r_2.env"
                                )
    parser_plotter.add_argument("-c",
                                "--color",
                                type=str,
                                default="red",
                                help="Colorscheme to use when plotting the system maps. default: red"
                                )
    parser_plotter.add_argument("-x",
                                "--combine",
                                action="store_true",
                                help="Create combine plots for the bags selection (use with match or all)"
                                )
                                

    parser_plot_xor = parser_plotter.add_mutually_exclusive_group(required=True)
    parser_plot_xor.add_argument("-a", "--all", action="store_true", help="Plot bags in the given directory")
    parser_plot_xor.add_argument("-m", "--match", type=str, help="Plot a subsection of bags in the directory")
    parser_plot_xor.add_argument("-s", "--single", type=str, help="Plot a specific bag file")

    #Execution
    args = parser.parse_args()
    main(args)
