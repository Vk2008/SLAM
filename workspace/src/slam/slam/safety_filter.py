#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from geometry_msgs.msg import PoseStamped
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import sensor_msgs_py.point_cloud2 as pc2
import math

class DroneSafetyFilter(Node):
    def __init__(self):
        super().__init__('drone_safety_filter')
        
        # Define a QoS profile that matches MAVROS sensor/telemetry publishing
        mavros_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        # 1. Subscriptions (Adding the explicit QoS profile)
        self.pose_sub = self.create_subscription(
            PoseStamped,
            '/mavros/local_position/pose',
            self.pose_callback,
            mavros_qos  # <--- Crucial fix here
        )
        
        self.lidar_sub = self.create_subscription(
            PointCloud2,
            '/vessel/lidar/points',
            self.lidar_callback,
            10  # Standard reliable subscription works for ros_gz_bridge
        )
        
        # State tracking
        self.current_altitude = 0.0
        self.TAKEOFF_ALTITUDE_THRESHOLD = 0.5  
        
        # Cylinder Mask Dimensions 
        self.SELF_RADIUS = 0.55  
        self.SELF_HEIGHT_MIN = -0.25 
        self.SELF_HEIGHT_MAX = 0.35  
        
        self.WARNING_DISTANCE = 3.5  

        self.get_logger().info("=============================================")
        self.get_logger().info("  QoS-ALIGNED PROXIMITY NODE ACTIVE          ")
        self.get_logger().info("=============================================")

    def pose_callback(self, msg):
        self.current_altitude = msg.pose.position.z

    def lidar_callback(self, msg):
        # 1. Takeoff Gate Check
        if self.current_altitude < self.TAKEOFF_ALTITUDE_THRESHOLD:
            self.get_logger().info(
                f"[SAFETY] Masked (On Ground). Altitude: {self.current_altitude:.2f}m", 
                throttle_duration_sec=3.0
            )
            return

        # 2. Parse Points Explicitly
        points = pc2.read_points(msg, field_names=("x", "y", "z"), skip_nans=True)
        
        min_external_dist = float('inf')
        closest_point = None
        has_points = False

        for p in points:
            has_points = True
            x, y, z = p[0], p[1], p[2]
            
            radial_dist = math.sqrt(x**2 + y**2)
            
            # Drop structural drone components
            if radial_dist <= self.SELF_RADIUS and (self.SELF_HEIGHT_MIN <= z <= self.SELF_HEIGHT_MAX):
                continue 
                
            # Compute true 3D distance to valid obstacle
            three_d_dist = math.sqrt(x**2 + y**2 + z**2)
            
            if three_d_dist < min_external_dist:
                min_external_dist = three_d_dist
                closest_point = (x, y, z)

        if not has_points:
            return

        if min_external_dist <= self.WARNING_DISTANCE:
            self.get_logger().warn(
                f"!!! COLLISION WARNING !!! Object detected at {min_external_dist:.2f}m! "
                f"(Relative X: {closest_point[0]:.2f}m, Y: {closest_point[1]:.2f}m)",
                throttle_duration_sec=0.4
            )
        else:
            self.get_logger().info(
                f"[SAFETY] Air Clear. Nearest item at: {min_external_dist:.2f}m", 
                throttle_duration_sec=2.0
            )

def main(args=None):
    rclpy.init(args=args)
    node = DroneSafetyFilter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()