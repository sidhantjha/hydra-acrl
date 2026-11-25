import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from sensor_msgs.msg import Image, CameraInfo


class ImageAdaptorSemantic(Node):
    """
    Semantic-mode TB3 -> Hydra adapter.

    Publishes RGB/depth/camera_info only.
    Does NOT publish fake semantic labels.

    /tesse/left_cam/semantic/image_raw is reserved for semantic_inference_ros.
    """

    def __init__(self):
        super().__init__("image_adaptor_semantic")

        self.create_subscription(Image, "/camera/image_raw", self.rgb_callback, 10)
        self.create_subscription(Image, "/camera/depth/image_raw", self.depth_callback, 10)
        self.create_subscription(CameraInfo, "/camera/camera_info", self.info_callback, 10)

        self.rgb_pub = self.create_publisher(Image, "/tesse/left_cam/rgb/image_raw", 10)
        self.depth_pub = self.create_publisher(Image, "/tesse/depth_cam/mono/image_raw", 10)
        self.info_pub = self.create_publisher(CameraInfo, "/tesse/left_cam/camera_info", 10)
        self.rgb_info_pub = self.create_publisher(CameraInfo, "/tesse/left_cam/rgb/camera_info", 10)

        self.get_logger().info(
            "TB3 -> Hydra semantic-mode adapter started; fake semantics disabled"
        )

    def rgb_callback(self, msg: Image):
        out = Image()
        out.header = msg.header
        out.header.frame_id = "left_cam"
        out.height = msg.height
        out.width = msg.width
        out.encoding = msg.encoding
        out.is_bigendian = msg.is_bigendian
        out.step = msg.step
        out.data = msg.data
        self.rgb_pub.publish(out)

    def depth_callback(self, msg: Image):
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

    def info_callback(self, msg: CameraInfo):
        out = CameraInfo()
        out.header = msg.header
        out.header.frame_id = "left_cam"
        out.height = msg.height
        out.width = msg.width
        out.distortion_model = msg.distortion_model
        out.d = msg.d
        out.k = msg.k
        out.r = msg.r
        out.p = msg.p
        out.binning_x = msg.binning_x
        out.binning_y = msg.binning_y
        out.roi = msg.roi

        self.info_pub.publish(out)
        self.rgb_info_pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = ImageAdaptorSemantic()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()



if __name__ == "__main__":
    main()
