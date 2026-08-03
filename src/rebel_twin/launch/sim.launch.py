import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    pkg = get_package_share_directory("rebel_twin")
    xacro_file = os.path.join(pkg, "urdf", "rebel4dof_on_platform.gazebo.urdf.xacro")
    robot_desc = xacro.process_file(xacro_file).toxml()

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory("gazebo_ros"), "launch", "gazebo.launch.py")))

    rsp = Node(
        package="robot_state_publisher", executable="robot_state_publisher",
        namespace="sim", output="screen",
        parameters=[{"robot_description": robot_desc}, {"use_sim_time": True}])

    spawn = Node(
        package="gazebo_ros", executable="spawn_entity.py",
        namespace="sim", output="screen",
        arguments=["-topic", "robot_description", "-entity", "rebel4dof_twin"])

    jsb = Node(package="controller_manager", executable="spawner", output="screen",
               arguments=["joint_state_broadcaster", "-c", "/sim/controller_manager"])
    arm = Node(package="controller_manager", executable="spawner", output="screen",
               arguments=["arm_position_controller", "-c", "/sim/controller_manager"])

    return LaunchDescription([
        gazebo, rsp, spawn,
        RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=[jsb])),
        RegisterEventHandler(OnProcessExit(target_action=jsb, on_exit=[arm])),
    ])
