from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="tb3_hydra_bringup",
            executable="image_adaptor_semantic",
            name="image_adaptor_semantic",
            output="screen",
        ),

        # Image adaptor now publishes:
        # /tesse/left_cam/rgb/image_raw
        # /tesse/depth_cam/mono/image_raw
        # /tesse/left_cam/camera_info
        #
        # Keep this legacy relay only if some older Hydra config still uses it.
        Node(
            package="topic_tools",
            executable="relay",
            name="relay_depth_registered",
            arguments=[
                "/camera/depth/image_raw",
                "/tesse/left_cam/depth_registered/image_rect",
            ],
            output="screen",
        ),

        Node(
            package="topic_tools",
            executable="relay",
            name="relay_odom",
            arguments=[
                "/odom",
                "/tesse/odom",
            ],
            output="screen",
        ),

        Node(
            package="topic_tools",
            executable="relay",
            name="relay_imu",
            arguments=[
                "/imu",
                "/tesse/imu/clean/imu",
            ],
            output="screen",
        ),

        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="tf_world_to_odom",
            arguments=[
                "--x", "0",
                "--y", "0",
                "--z", "0",
                "--roll", "0",
                "--pitch", "0",
                "--yaw", "0",
                "--frame-id", "world",
                "--child-frame-id", "odom",
            ],
            output="screen",
        ),

        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="tf_base_footprint_to_base_link",
            arguments=[
                "--x", "0",
                "--y", "0",
                "--z", "0",
                "--roll", "0",
                "--pitch", "0",
                "--yaw", "0",
                "--frame-id", "base_footprint",
                "--child-frame-id", "base_link",
            ],
            output="screen",
        ),

        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="tf_base_link_to_base_link_gt",
            arguments=[
                "--x", "0",
                "--y", "0",
                "--z", "0",
                "--roll", "0",
                "--pitch", "0",
                "--yaw", "0",
                "--frame-id", "base_link",
                "--child-frame-id", "base_link_gt",
            ],
            output="screen",
        ),

        # Hydra-facing camera frame.
        # Keeps your elevated camera position, but uses uHumans2 optical-frame rotation.
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="tf_base_link_gt_to_left_cam",
            arguments=[
                "--x", "0.80",
                "--y", "0.0",
                "--z", "0.75",
                "--qx", "0.5",
                "--qy", "-0.5",
                "--qz", "0.5",
                "--qw", "-0.5",
                "--frame-id", "base_link_gt",
                "--child-frame-id", "left_cam",
            ],
            output="screen",
        ),
    ])
