from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import PushRosNamespace, SetRemap
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("model_name", default_value="ade20k-efficientvit_seg_l2"),
        DeclareLaunchArgument("labelspace_name", default_value="ade20k_full"),
        DeclareLaunchArgument("force_rebuild", default_value="false"),

        GroupAction([
            PushRosNamespace("tesse/left_cam"),

            # Inside /tesse/left_cam:
            # color/image_raw -> rgb/image_raw
            # so absolute input becomes /tesse/left_cam/rgb/image_raw
            SetRemap(src="color/image_raw", dst="rgb/image_raw"),

            IncludeLaunchDescription(
                AnyLaunchDescriptionSource(
                    PathJoinSubstitution([
                        FindPackageShare("semantic_inference_ros"),
                        "launch",
                        "closed_set.launch.yaml",
                    ])
                ),
                launch_arguments={
                    "model_name": LaunchConfiguration("model_name"),
                    "labelspace_name": LaunchConfiguration("labelspace_name"),
                    "force_rebuild": LaunchConfiguration("force_rebuild"),
                }.items(),
            ),
        ]),
    ])
