from warnings import warn
from rosbags.rosbag2 import Reader 
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
from sensor_msgs_py import point_cloud2
import argparse
import numpy as np
import pdb
import sys
import pickle
from colors import *


typestore = get_typestore(Stores.ROS2_JAZZY)

def hline():
    print("--------------------------------------------------------------------------------")

def pc2_to_native(msg: object) -> object:
    dtype = np.dtype([ 
            ("x", np.float32),
            ("y", np.float32),
            ("z", np.float32),
            ("intensity", np.float32)
            ])
    arr = np.frombuffer(msg.data, dtype=dtype)
    points = [tuple(pt) for pt in arr]
    pc2_native = point_cloud2.create_cloud(msg.header, msg.fields, points)
    return pc2_native

def extract_topic(
        connection,
        rawdata
    ) -> tuple[str, str, dict] | None:

    split = connection.topic.split("/")
    namespace = split[1]
    topic_name = split[-1]
    msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
    if connection.msgtype == "geometry_msgs/msg/PoseStamped":
        data = get_position(msg)
    elif connection.msgtype == "geometry_msgs/msg/TwistStamped":
        data = get_vel(msg)
    elif connection.msgtype == "sensor_msgs/msg/PointCloud2":
        data = get_pc2(msg)
    elif connection.msgtype == "async_pac_gnn_interfaces/msg/MissionControl":
        if "offboard_enable" in msg.__dataclass_fields__:
              data = get_mission_ctrl_legacy(msg)
        else:
              data = get_mission_ctrl(msg)
    else:
        return None
    if "header" in msg.__dataclass_fields__:
        t = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        entry = {t: data}
    else:
        entry = {0: data}
    return namespace, topic_name, entry

def get_position(msg):
    return np.array([msg.pose.position.x, msg.pose.position.y, msg.pose.position.z])
def get_vel(msg):
    return np.array([msg.twist.linear.x, msg.twist.linear.y, msg.twist.linear.z])
def get_pc2(msg):
    pc2_native = pc2_to_native(msg)
    return np.array(point_cloud2.read_points_list(pc2_native, field_names=["x", "y", "z", "intensity"]))
def get_mission_ctrl_legacy(msg): # supporting old naming conventions
    return np.array([
            msg.hw_enable,
            msg.offboard_enable,
            msg.takeoff,
            msg.land,
            msg.geofence,
            msg.pac_offboard_only,
            msg.pac_lpac_l1,
            msg.pac_lpac_l2
            ], dtype = bool)
def get_mission_ctrl(msg):
    return np.array([
            msg.hw_enable,
            msg.ob_enable,
            msg.ob_takeoff,
            msg.ob_land,
            msg.geofence,
            msg.pac_offboard_only,
            msg.pac_lpac_l1,
            msg.pac_lpac_l2
            ], dtype = bool)

def extract_bag(filepath: str):
    print(BLUE + f"Reading from {filepath}" + RESET)
    if filepath[-1] == "/": # Account for trailing slash
        filepath = filepath[:-1]
    split = filepath.split("/")
    filename = split[-1]
    save_path = filepath + "/" + filename + ".pkl"

    with Reader(filepath) as reader:
        # Get any custom message definitions not included in the default typestore
        typs = {}
        for conn in reader.connections:
            typs.update(get_types_from_msg(conn.msgdef.data, conn.msgtype))
        typestore.register(typs)

        print(GREEN + "Found the following topics:" + RESET)
        hline()
        for connection in reader.connections:
            print(connection.topic, connection.msgtype)
        hline()

        table = {}
        cnt = 1
        num_msgs = reader.message_count
        for connection, timestamp, rawdata in reader.messages():
            result = extract_topic(connection, rawdata)
            sys.stdout.write(f"Processed {cnt}/{num_msgs} messages in the playback.\r")
            sys.stdout.flush()
            cnt+=1
            if result is None:
                continue
            namespace, topic_name, entry = result
            if namespace not in table.keys():
                table[namespace] = {}
            if topic_name not in table[namespace].keys():
                table[namespace][topic_name] = entry
            else:
                table[namespace][topic_name].update(entry)
        print(GREEN + "\nDone!" + RESET)
        print(BLUE + f"Saving to {save_path}..." + RESET, end="")
        with open(save_path, "wb") as f:
            pickle.dump(table, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(GREEN + "Done!" + RESET)

if __name__ ==  "__main__":
    parser = argparse.ArgumentParser(
                prog="bag_reader",
                description="Extracts results from an LPAC experiment ROS2 bag file"
            )
    parser.add_argument("filepath")
    args = parser.parse_args()
    extract_bag(args.filepath)

    #filepath = args.filepath
    #if filepath[-1] == "/": # Account for trailing slash
    #    filepath = filepath[:-1]
    #split = filepath.split("/")
    #filename = split[-1] + ".pkl"
    #test_loading(filepath, filename)
