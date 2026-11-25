import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    share = Path(get_package_share_directory("tb3_hydra_bringup"))
    robotis = Path(get_package_share_directory("turtlebot3_gazebo"))
    resources = [
        str(share / "models"),
        LaunchConfiguration("assets_models"),
        str(robotis / "models"),
    ]
    inherited = os.environ.get("GZ_SIM_RESOURCE_PATH")
    if inherited:
        resources.append(inherited)
    paths = []
    for resource in resources:
        paths.extend([os.pathsep, resource])

    world = str(share / "worlds" / "small_house_hydra.world")
    server = ["gz", "sim", "-r", "-s"]
    if os.environ.get("HYDRA_ACRL_EGL") == "1":
        server.append("--headless-rendering")
    return LaunchDescription([
        DeclareLaunchArgument("assets_models"),
        DeclareLaunchArgument("gui", default_value="false"),
        SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", paths[1:]),
        ExecuteProcess(cmd=[*server, world], output="screen"),
        ExecuteProcess(
            cmd=["gz", "sim", "-g"], output="screen",
            condition=IfCondition(LaunchConfiguration("gui")),
        ),
    ])
