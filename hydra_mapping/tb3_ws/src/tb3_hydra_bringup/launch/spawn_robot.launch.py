from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


def generate_launch_description():

    model_file = PathJoinSubstitution([
        FindPackageShare("tb3_hydra_bringup"), "models", "hydra_waffle", "model.sdf",
    ])

    x = LaunchConfiguration("x", default="10.0")
    y = LaunchConfiguration("y", default="0.0")
    z = LaunchConfiguration("z", default="0.05")

    return LaunchDescription([

        DeclareLaunchArgument("x", default_value="10.0"),
        DeclareLaunchArgument("y", default_value="0.0"),
        DeclareLaunchArgument("z", default_value="0.05"),

        Node(
            package="ros_gz_sim",
            executable="create",
            arguments=[
                "-name", "hydra_waffle",
                "-file", model_file,
                "-x", x,
                "-y", y,
                "-z", z,
            ],
            output="screen",
        ),
    ])
