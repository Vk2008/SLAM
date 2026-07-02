# SLAM

A 3D ROS 2 and Gazebo-based simulation pipeline featuring a drone equipped with a 3D LiDAR sensor, controlled via QGroundControl / keyboard teleoperation, with mapping powered by RTAB-Map.

---

## 🏗️ System Architecture & Features

- **Simulation (`world.sdf` & `drone.sdf`):** A custom house environment built in Gazebo Sim containing a 3D drone equipped with a 3D LiDAR sensor.
- **Flight Control:** Integrated with a flight stack linked to **QGroundControl**, permitting manual keyboard overrides using the `drone_teleop.py` node.
- **Perception & SLAM:** Streams 3D PointCloud data into **RTAB-Map** for high-fidelity 3D loop-closure, localization, and dense mapping of the entire Gazebo house.
- **Safety Node (`safety_filter.py`):** A custom safety monitoring node that dynamically calculates proximity distances to obstacles from the LiDAR point cloud, constantly prints the distance to the nearest object, and surfaces warnings in real time.
- **Visualization:** Integrated seamlessly with **Foxglove Studio** / RViz2 to track live trajectory data and point cloud registration.

---

## 📂 Repository Structure

*   `workspace/src/slam/` — Core ROS 2 Python package.
    *   `launch/slam.launch.py` — Central launch file combining the Gazebo environment, drone state estimators, and RTAB-Map.
    *   `slam/safety_filter.py` — Monitors LiDAR streams, calculates minimum distance, and handles proximity warnings.
    *   `slam/odom_to_tf.py` — Handles coordinate transforms mapping local odometry to world frames.
    *   `slam/drone_teleop.py` — Keyboard mapping script to manually navigate the UAV through the simulation.
*   `drone.sdf` / `world.sdf` — Model definitions and environmental layouts for Gazebo.
*   `Windows Installation.md` / `INSTALL.md` — OS-specific setup procedures.

---

## 🚀 Getting Started

### Prerequisites
- ROS 2 (Humble)
- Gazebo Sim
- RTAB-Map ROS packages
- QGroundControl
- Foxglove Studio (or RViz2, for visualization)

### Installation & Build

1. Clone the repository
2. Build the workspace and source the setup script:
```bash
cd ~/SLAM/workspace
colcon build
source install/setup.bash
echo "source ~/SLAM/workspace/install/setup.bash" >> ~/.bashrc
```
3. Launch Gazebo Server & Client
```bash
# Terminal 1: Run Gazebo Server
gz sim -s -v4 -r world.sdf

# Terminal 2: Run Gazebo GUI
gz sim -g
```
4. Launch ArduPilot SITL Flight Stack
```bash
# Terminal 3: ArduPilot SITL execution
sim_vehicle.py -v ArduCopter -f gazebo-iris --frame JSON --out=udp:127.0.0.1:14550
```
Open QGroundControl, and execute the further commands once it shows `Ready to Fly`

5. Launch ROS 2 Nodes
```bash
# Terminal 4: Launch main package configs
ros2 launch slam slam.launch.py
```
6. Keyboard Teleoperation
```bash
# Terminal 5: Keyboard Teleoperation
ros2 run slam drone_teleop
```
7. Initiate 3D RTAB-Map SLAM
```bash
ros2 run rtabmap_slam rtabmap \
  --delete_db_on_start \
  --ros-args \
  -p use_sim_time:=true \
  -p frame_id:=base_link \
  -p odom_frame_id:=odom \
  -p subscribe_depth:=false \
  -p subscribe_rgb:=false \
  -p subscribe_scan_cloud:=true \
  -p approx_sync:=true \
  -r odom:=/mavros/local_position/odom \
  -r scan_cloud:=/vessel/lidar/points
```
8. Open Foxglove Studio(or RViz2), hook into your running ROS network, and visualize `vessel/lidar/points` and `cloud_map`
9. Maneuver the drone through different rooms of the house using `W`, `A`, `S`, `D` keys.
`Remember to keep the teleop terminal active!`

---

## 📑 Attribution & Credits

This repository was developed as a Summer Project under AeroClub, IIT Delhi. The original work can be found at [AeroClub-SLAM](https://github.com/abhishekjain1612006/AeroClub-SLAM).
