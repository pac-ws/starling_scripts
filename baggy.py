import bag_reader
import bag_process
import bag_plotter
import argparse
import os
import pickle
from colors import *
from bag_utils import printC

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
            printC("Error: The specified path is not a directory.", RED)
        return filtered_bags
    else:
        printC("Error: missing at least one input (all, match, single) when listing directories.\
                Exiting...", RED)
        exit(1)

def load_bag(filepath: str):
    with open(filepath, "rb") as f:
        bag = pickle.load(f)
    return bag

def main(args):
    bags = list_directories(args.dir, args.all, args.match, args.single)
    data = []
    for b in bags:
        printC(f"Begin {b}", RED) 
        if args.command == "extract":
            filepath = args.dir + "/" + b
            bag_dict = bag_reader.extract_bag(filepath, save=True)
        elif args.command == "process":
            filedir = args.dir + "/" + b 
            filepath = filedir + "/" + b + ".pkl" # pkl file shares name of bag dir
            bag_dict = load_bag(filepath)
            bag_process.process_bag(bag_dict, args.params, args.idf, filedir, b, save=True)
        elif args.command == "plot":
            filepath = args.dir + "/" + b + "/" + b + "_processed.pkl" # pkl file shares name of bag dir
            bag_data = load_bag(filepath)
            data.append(bag_data)
            if not args.combine:
                bag_plotter.plot_bag(data[-1], args.output, args.color)
    if args.command == "plot" and args.combine:
        bag_plotter.plot_combined_cost(data, args.output, args.color)
        bag_plotter.plot_combined_global_map(data, args.output, args.color)

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
    parser_cost = subparsers.add_parser("process", help="Process the raw bag output calculating coverage cost and maps")
    parser_cost.add_argument("-d",
                             "--dir",
                             type=str,
                             default="/workspace/bags",
                             help="Directory containing bag files. default: /workspace/bags"
                             )
    parser_cost.add_argument("-o",
                             "--output",
                             type=str,
                             default="/workspace/figures",
                             help="Output directory for generated figures. default: /workspace/figures"
                             )
    parser_cost.add_argument("-p",
                             "--params",
                             type=str,
                             default="/workspace/pt/models_256/coverage_control_params_512.toml",
                             help="Coverage control parameters file.\
                                     default: /workspace/pt/models_256/coverage_control_params_512.toml"
                             )
    parser_cost.add_argument("-i",
                             "--idf",
                             type=str,
                             default="/workspace/configs/penn_envs/10r_2.env",
                             help="Importance density function file.\
                                     default: /workspace/configs/penn_envs/10r_2.env"
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
