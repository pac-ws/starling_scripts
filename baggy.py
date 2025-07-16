import bag_reader
import argparse
import os
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
        if not os.path.isdir(single):
            print(RED + "Error: The specified path is not a directory." + RESET)
        return filtered_bags
    else:
        print(RED + "Error: missing at least one input (all, match, single) when listing directories.\
                Exiting..." + RESET)
        exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="bag_plotter.py",
                                     description="Reads bag files and generates plots"
                                     )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Loading
    parser_processor = subparsers.add_parser("process", help="Process bag files, generating a data file")
    parser_processor.add_argument("-d",
                               "--dir",
                               type=str,
                               default="/workspace/bags",
                               help="Directory containing bag files. default: /workspace/bags"
                               )
    parser_xor = parser_processor.add_mutually_exclusive_group(required=True)
    parser_xor.add_argument("-a", "--all", action="store_true", help="Process all bag files in the given directory")
    parser_xor.add_argument("-m", "--match", type=str, help="Process all bag files that contain a given substring")
    parser_xor.add_argument("-s", "--single", type=str, help="Path to a specific bag file")
    args = parser.parse_args()

    # Plotting
    parser_plotter = subparsers.add_parser("plot", help="Plot bag files [Requires processing first!]")
    parser_plotter.add_argument("-d",
                               "--dir",
                               type=str,
                               default="/workspace/bags",
                               help="Directory containing bag files. default: /workspace/bags"
                               )
    parser_xor = parser_processor.add_mutually_exclusive_group(required=True)
    parser_xor.add_argument("-a", "--all", action="store_true", help="Process all bag files in the given directory")
    parser_xor.add_argument("-m", "--match", type=str, help="Process all bag files that contain a given substring")
    parser_xor.add_argument("-s", "--single", type=str, help="Path to a specific bag file")

    #Execution
    bags = list_directories(args.dir, args.all, args.match, args.single)
    for b in bags:
        if args.process:
            filepath = args.dir + "/" + b
            bag_reader.process_bag(filepath)
        elif args.plot:
            filepath = args.dir + "/" + b + "/" + b + ".pkl" # pkl file shares name of bag dir
            
