from warnings import warn
from rosbags.rosbag2 import Reader 
from rosbags.typesys import Stores, get_typestore, get_types_from_msg
from sensor_msgs_py import point_cloud2
import argparse
import numpy as np
import pdb

typestore = get_typestore(Stores.ROS2_JAZZY)

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

    namespace = connection.topic.split("/")[1]
    msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
    t = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
    if connection.msgtype == "geometry_msgs/msg/PoseStamped":
        data = get_position(msg)
    elif connection.msgtype == "geometry_msgs/msg/TwistStamped":
        data = get_vel(msg)
    elif connection.msgtype == "sensor_msgs/msg/PointCloud2":
        data = get_pc2(msg)
    else:
        return None
    entry = np.concatenate(([t], data))
    return namespace, connection.msgtype, entry

def get_position(msg):
    return np.array([msg.pose.position.x, msg.pose.position.y, msg.pose.position.z])
def get_vel(msg):
    return np.array([msg.twist.linear.x, msg.twist.linear.y, msg.twist.linear.z])
def get_pc2(msg):
    pc2_native = pc2_to_native(msg)
    return np.array(point_cloud2.read_points_list(pc2_native, field_names=["x", "y", "z"]))

def process_bag(filepath: str):
    print(f"Reading from {filepath}")
    with Reader(filepath) as reader:
        # Get any custom message definitions not included in the default typestore
        typs = {}
        for conn in reader.connections:
            typs.update(get_types_from_msg(conn.msgdef.data, conn.msgtype))
        typestore.register(typs)

        print("Found the following topics:")
        for connection in reader.connections:
            print(connection.topic, connection.msgtype)

        table = {}
        for connection, timestamp, rawdata in reader.messages():
            result = extract_topic(connection, rawdata)
            if result is None:
                continue
            namespace, msgtype, entry = result
            if namespace not in table.keys():
                table[namespace] = {}
            if msgtype not in table[namespace].keys():
                table[namespace][msgtype] = entry
            else:
                table[namespace][msgtype].append(entry, axis=0)
        pdb.set_trace()


if __name__ ==  "__main__":
    parser = argparse.ArgumentParser(
                prog="bag_reader",
                description="Extracts results from an LPAC experiment ROS2 bag file"
            )
    parser.add_argument("filepath")
    args = parser.parse_args()
    process_bag(args.filepath)
