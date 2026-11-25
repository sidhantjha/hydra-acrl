import math
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TwistStamped
from tf_transformations import euler_from_quaternion

class WaypointController(Node):
    def __init__(self):
        super().__init__("waypoint_controller")
        self.waypoints = [
            (2.0, 0.0),
            (4.0, 0.0),
            (8.0, 0.0),
            (8.0,-12.0),
        ]
        self.current_waypoint = 0
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.odom_sub = self.create_subscription(
            Odometry,
            "/odom",
            self.odom_callback,
            10,
        )
        self.vel_pub = self.create_publisher(
            TwistStamped,
            "/cmd_vel",
            10,
        )
        self.timer = self.create_timer(
            0.1,
            self.control_loop,
        )
    
    def odom_callback(self,msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        _, _, self.yaw = euler_from_quaternion(
            [q.x,q.y,q.z,q.w]
        )

    def publish_cmd(self, linear_x, angular_z):
        cmd = TwistStamped()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = "base_link"
        cmd.twist.linear.x = linear_x
        cmd.twist.angular.z = angular_z
        self.vel_pub.publish(cmd)
    def control_loop(self):
        if self.current_waypoint >= len(self.waypoints):
            self.publish_cmd(0.0, 0.0)
            return

        goal_x, goal_y = self.waypoints[self.current_waypoint]

        dx = goal_x - self.x
        dy = goal_y - self.y
        distance = math.hypot(dx, dy)

        target_heading = math.atan2(dy, dx)
        heading_error = self.normalize_angle(target_heading - self.yaw)

        self.get_logger().info(
            f"wp={self.current_waypoint} "
            f"x={self.x:.2f} y={self.y:.2f} "
            f"goal=({goal_x:.2f},{goal_y:.2f}) "
            f"dist={distance:.2f} head_err={heading_error:.2f}",
            throttle_duration_sec=0.5,
        )

        if distance < 0.005:
            self.publish_cmd(0.0, 0.0)
            self.get_logger().info(f"Waypoint {self.current_waypoint} reached")
            self.current_waypoint += 1
            return

        # TURN IN PLACE FIRST
        if abs(heading_error) > 0.05:
            angular = 0.8 * heading_error
            angular = max(min(angular, 0.4), -0.5)
            self.publish_cmd(0.0, angular)
            return

        # THEN DRIVE FORWARD
        linear = 1.5 * distance
        linear = max(min(linear, 1.2), 0.05)

        self.publish_cmd(linear, 0.0)
    
    def normalize_angle(self, angle):
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle
        
    
def main(args=None):
    rclpy.init(args=args)
    node = WaypointController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

