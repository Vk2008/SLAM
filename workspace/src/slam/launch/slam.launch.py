from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    return LaunchDescription([
        
        # 1. Foxglove WebSocket Bridge
        # Streams ROS 2 data directly to your Mac's Foxglove Studio
        Node(
            package='foxglove_bridge',
            executable='foxglove_bridge',
            name='foxglove_bridge',
            parameters=[{'use_sim_time': True}], # <-- Added Sim Time
            output='screen',
        ),

        # 2. Gazebo to ROS 2 Parameter Bridge
        # Translates the Gazebo point cloud into a ROS 2 sensor_msgs/PointCloud2
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='lidar_bridge',
            parameters=[{'use_sim_time': True}], # <-- Added Sim Time
            arguments=[
                '/vessel/lidar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            ],
            output='screen'
        ),

        # 3. Static TF2 Publisher
        # Mounts the LiDAR 10cm below the drone's center of mass
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='lidar_tf_publisher',
            parameters=[{'use_sim_time': True}], # <-- Added Sim Time
            arguments=[
                '0', '0', '-0.1', '0', '0', '0', 
                'base_link', 'iris_with_gimbal/lidar_link/gpu_lidar'
            ],
            output='screen'
        ),

        # 4. Odom to TF Relay
        # Takes the MAVROS odometry and broadcasts it as a TF transform (odom -> base
        Node(
            package='slam',
            executable='odom_to_tf_relay',
            name='odom_to_tf_relay',
            parameters=[{'use_sim_time': True}], # <-- Added Sim Time
            output='screen'
        ),

        # 5. MAVROS
        # Connects ROS 2 to the flight controller (ArduPilot)
        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(
                os.path.join(get_package_share_directory('mavros'), 'launch', 'apm.launch')
            ),
            launch_arguments={
                'fcu_url': 'udp://127.0.0.1:14550@14555',
                'use_sim_time': 'true',          # <-- Added Sim Time for MAVROS
            }.items()
        ),
        # 5. Proximity Safety Filter Node
        Node(
            package='slam',
            executable='safety_filter',
            name='drone_safety_filter',
            output='screen'
        ),
    ])