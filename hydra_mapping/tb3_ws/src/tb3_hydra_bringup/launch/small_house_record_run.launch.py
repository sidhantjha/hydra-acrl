from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


def include_launch(pkg_share, file_name, **launch_arguments):
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            pkg_share,
            "/launch/",
            file_name,
        ]),
        launch_arguments=launch_arguments.items(),
    )


def generate_launch_description():
    pkg_share = FindPackageShare("tb3_hydra_bringup")

    # AWS Small House world
    world = include_launch(
        pkg_share,
        "small_house_world.launch.py",
        assets_models=LaunchConfiguration("assets_models"),
        gui=LaunchConfiguration("gui"),
    )

    # Spawn our known-working Hydra Waffle.
    # This location comes from the upstream Small House
    # TurtleBot3 test region.
    spawn_robot = TimerAction(
        period=3.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([
                    pkg_share,
                    "/launch/spawn_robot.launch.py",
                ]),
                launch_arguments={
                    "x": "-3.6655",
                    "y": "-0.4874",
                    "z": "0.00",
                }.items(),
            )
        ],
    )

    # Existing TurtleBot3 Gazebo <-> ROS bridge
    bridge = TimerAction(
        period=4.0,
        actions=[
            Node(
                package="ros_gz_bridge",
                executable="parameter_bridge",
                parameters=[{
                    "config_file": PathJoinSubstitution([pkg_share, "config", "bridge.yaml"]),
                }],
                output="screen",
            )
        ],
    )

    # RGB bridge
    rgb_image_bridge = TimerAction(
        period=4.0,
        actions=[
            Node(
                package="ros_gz_image",
                executable="image_bridge",
                arguments=[
                    "/camera/image_raw",
                ],
                output="screen",
            )
        ],
    )

    # Existing adapter that exposes the topics Hydra expects.
    hydra_interface = TimerAction(
        period=5.0,
        actions=[
            include_launch(
                pkg_share,
                "hydra_interface_semantic.launch.py",
            )
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument("assets_models"),
        DeclareLaunchArgument("gui", default_value="false"),
        world,
        spawn_robot,
        bridge,
        rgb_image_bridge,
        hydra_interface,
    ])
