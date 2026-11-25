"""Run the existing Small House components with the audited Hydra dataset settings."""

import json
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, IncludeLaunchDescription
from launch.actions import OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def mapping_actions(context):
    share = Path(get_package_share_directory("tb3_hydra_bringup"))
    hydra_share = Path(get_package_share_directory("hydra"))
    ros_share = Path(get_package_share_directory("hydra_ros"))
    run = LaunchConfiguration("run_directory")

    def include(name, **launch_arguments):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(share / "launch" / f"{name}.launch.py")),
            launch_arguments=launch_arguments.items(),
        )

    # Same input, core, labelspace, sink and LCD layers as the dataset launch.
    config_files = [
        share / "config/hydra_input.yaml",
        share / "config/hydra.yaml",
        hydra_share / "config/label_spaces/ade20k_full_label_space.yaml",
        f"{ros_share}/config/sinks/mesh_segmenter_sinks.yaml@frontend/objects",
        f"{ros_share}/config/sinks/gvd_places_sinks.yaml@frontend/freespace_places",
        f"{ros_share}/config/sinks/active_window_sinks.yaml@active_window",
        hydra_share / "config/lcd/uhumans2.yaml",
    ]
    args = []
    for path in config_files:
        args.extend(["--config-utilities-file", str(path)])
    runtime = {
        "enable_lcd": False, "exit_after_clock": False, "enable_zmq": False,
        "robot_id": 0, "odom_frame": "world", "robot_frame": "base_link_gt",
        "map_frame": "map", "log_path": str(Path(run.perform(context)) / "hydra"),
    }
    args.extend(["--config-utilities-yaml", json.dumps(runtime)])
    hydra = Node(
        package="hydra_ros", executable="hydra_ros_node", name="hydra",
        parameters=[{"use_sim_time": True}],
        remappings=[
            ("hydra/input/left_cam/depth_registered/image_rect", "/tesse/depth_cam/mono/image_raw"),
            ("hydra/input/left_cam/rgb/image_raw", "/tesse/left_cam/rgb/image_raw"),
            ("hydra/input/left_cam/rgb/camera_info", "/tesse/left_cam/camera_info"),
            ("hydra/input/left_cam/semantic/image_raw", "/tesse/left_cam/semantic/image_raw"),
            ("hydra/input/left_cam/feature", "/tesse/left_cam/semantic/feature"),
        ],
        arguments=args, output="screen",
        sigterm_timeout=LaunchConfiguration("shutdown_grace"),
        sigkill_timeout="15",
    )

    def hydra_exited(event, context):
        status = Path(run.perform(context)) / "hydra_exit.json"
        status.write_text(json.dumps({
            "returncode": event.returncode,
            "launch_was_shutting_down": context.is_shutdown,
        }) + "\n")
        if not context.is_shutdown:
            return [EmitEvent(event=Shutdown(reason="Hydra exited"))]
        return []

    return [
        RegisterEventHandler(OnProcessExit(target_action=hydra, on_exit=hydra_exited)),
        include(
            "small_house_record_run",
            assets_models=LaunchConfiguration("assets_models"),
            gui=LaunchConfiguration("gui"),
        ),
        include("semantic_segmentation", force_rebuild=LaunchConfiguration("force_rebuild")),
        Node(
            package="tf2_ros", executable="static_transform_publisher", name="world_to_map",
            arguments=["--frame-id", "world", "--child-frame-id", "map"],
        ),
        hydra,
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("run_directory"),
        DeclareLaunchArgument("shutdown_grace", default_value="180"),
        DeclareLaunchArgument("assets_models"),
        DeclareLaunchArgument("gui", default_value="false"),
        DeclareLaunchArgument("force_rebuild", default_value="false"),
        OpaqueFunction(function=mapping_actions),
    ])
