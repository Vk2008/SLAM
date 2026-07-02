import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

# --- NEW IMPORTS FOR QoS ---
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

class OdomToTF(Node):
    def __init__(self):
        super().__init__('odom_to_tf_relay')
        self.set_parameters([rclpy.parameter.Parameter('use_sim_time', rclpy.Parameter.Type.BOOL, True)])
        
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # --- NEW QoS PROFILE ---
        # Match MAVROS's Best Effort policy so the nodes agree to talk
        best_effort_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.subscription = self.create_subscription(
            Odometry,
            '/mavros/local_position/odom',
            self.odom_callback,
            best_effort_qos # <-- Applied the QoS profile here
        )
        self.get_logger().info("✅ Duct tape applied: Forcing Odometry into the TF Tree (odom -> base_link)")

    def odom_callback(self, msg):
        t = TransformStamped()
        
        # Steal the exact Sim Time timestamp from the odometry message
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        
        # Copy the drone's position
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        
        # Copy the drone's rotation (quaternion)
        t.transform.rotation = msg.pose.pose.orientation
        
        # Broadcast it directly to the spatial tree
        self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = OdomToTF()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
