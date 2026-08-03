import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    bringup = get_package_share_directory("irc_ros_bringup")
    twin = get_package_share_directory("rebel_twin")

    real = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(bringup, "launch", "rebel.launch.py")),
        launch_arguments={
            "robot_name": "igus_rebel_4dof",
            "hardware_protocol": "cri",
            "use_rviz": "false",
            "rebel_version": "01",
        }.items())

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(twin, "launch", "sim.launch.py")))

    mirror = Node(package="rebel_twin", executable="mirror_node", output="screen")

    return LaunchDescription([real, sim, mirror])
