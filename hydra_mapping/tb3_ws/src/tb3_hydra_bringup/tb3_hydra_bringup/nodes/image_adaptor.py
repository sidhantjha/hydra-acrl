import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from sensor_msgs.msg import Image, CameraInfo

import numpy as np
from cv_bridge import CvBridge


class ImageAdaptor(Node):
    def __init__(self):
        super().__init__("tb3_hydra_input_adapter")

        self.bridge = CvBridge()

        # Raw Gazebo/TB3 inputs
        self.rgb_sub = self.create_subscription(
            Image,
            "/camera/image_raw",
            self.rgb_callback,
            10,
        )

        self.depth_sub = self.create_subscription(
            Image,
            "/camera/depth/image_raw",
            self.depth_callback,
            10,
        )

        self.info_sub = self.create_subscription(
            CameraInfo,
            "/camera/camera_info",
            self.camera_info_callback,
            10,
        )

        self.rgb_info_pub = self.create_publisher(
            CameraInfo,
            "/tesse/left_cam/rgb/camera_info",
            10,
        )

        # Official-ish uHumans2/Hydra outputs
        self.rgb_pub = self.create_publisher(
            Image,
            "/tesse/left_cam/rgb/image_raw",
            10,
        )

        self.depth_pub = self.create_publisher(
            Image,
            "/tesse/depth_cam/mono/image_raw",
            10,
        )

        # Hydra/uHumans2 launch commonly consumes converted semantic labels.
        self.semantic_pub = self.create_publisher(
            Image,
            "/tesse/seg_cam/converted/image_raw",
            10,
        )

        # Keep old topic too for compatibility with any custom launch remnants.
        self.legacy_semantic_pub = self.create_publisher(
            Image,
            "/tesse/left_cam/semantic/image_raw",
            10,
        )

        self.info_pub = self.create_publisher(
            CameraInfo,
            "/tesse/left_cam/camera_info",
            10,
        )

        self.get_logger().info("TB3 -> Hydra uHumans2-style topic adapter started")

    def camera_info_callback(self, msg: CameraInfo):
        out = CameraInfo()
        out.header = msg.header
        out.header.frame_id = "left_cam"

        out.height = msg.height
        out.width = msg.width
        out.distortion_model = msg.distortion_model
        out.d = list(msg.d)
        out.k = list(msg.k)
        out.r = list(msg.r)
        out.p = list(msg.p)
        out.binning_x = msg.binning_x
        out.binning_y = msg.binning_y
        out.roi = msg.roi

        self.info_pub.publish(out)
        self.rgb_info_pub.publish(out)

    def rgb_callback(self, msg: Image):
        # Official uHumans2 RGB is rgb8.
        # Gazebo may publish rgb8 or bgr8 depending on bridge/config.
        try:
            img = self.bridge.imgmsg_to_cv2(msg, desired_encoding="rgb8")
            rgb_msg = self.bridge.cv2_to_imgmsg(img, encoding="rgb8")
        except Exception:
            img_bgr = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            img_rgb = img_bgr[:, :, ::-1]
            rgb_msg = self.bridge.cv2_to_imgmsg(img_rgb, encoding="rgb8")

        rgb_msg.header = msg.header
        rgb_msg.header.frame_id = "left_cam"
        self.rgb_pub.publish(rgb_msg)

        height, width = rgb_msg.height, rgb_msg.width

        # Fake semantic labels for now.
        # 8UC1 class-ID image, all zeros.
        semantic_image = np.zeros((height, width), dtype=np.uint8)
        semantic_msg = self.bridge.cv2_to_imgmsg(semantic_image, encoding="8UC1")
        semantic_msg.header = msg.header
        semantic_msg.header.frame_id = "left_cam"

        self.semantic_pub.publish(semantic_msg)
        self.legacy_semantic_pub.publish(semantic_msg)

    def depth_callback(self, msg: Image):
        # Depth should already be 32FC1 from Gazebo.
        # Relay it to official uHumans2-style depth topic.
        out = Image()
        out.header = msg.header
        out.header.frame_id = "left_cam"
        out.height = msg.height
        out.width = msg.width
        out.encoding = msg.encoding
        out.is_bigendian = msg.is_bigendian
        out.step = msg.step
        out.data = msg.data

        self.depth_pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = ImageAdaptor()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
