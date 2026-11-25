"""Connect the upstream streaming visualizer to the Hydra backend."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import SetRemap
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    upstream = PathJoinSubstitution([
        FindPackageShare("hydra_visualizer"), "launch", "streaming_visualizer.launch.yaml",
    ])
    return LaunchDescription([
        DeclareLaunchArgument("start_rviz", default_value="true"),
        SetRemap(src="/hydra_visualizer/dsg", dst="/hydra/backend/dsg"),
        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(upstream),
            launch_arguments={"start_rviz": LaunchConfiguration("start_rviz")}.items(),
        ),
    ])
