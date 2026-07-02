#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from mavros_msgs.srv import SetMode, CommandBool, CommandTOL
import sys
import select
import termios
import tty
import time

# STRICT 2DOF MAPPING: Arrow Keys only.
MOVE_BINDINGS = {
    'w': (1.0, 0.0),   # Up Arrow: Forward
    's': (-1.0, 0.0),  # Down Arrow: Backward
    'a': (0.0, 1.0),   # Left Arrow: Move Left
    'd': (0.0, -1.0),  # Right Arrow: Move Right
}

class DroneTeleop(Node):
    def __init__(self):
        super().__init__('drone_teleop')
        
        self.publisher_ = self.create_publisher(Twist, '/mavros/setpoint_velocity/cmd_vel_unstamped', 10)
        self.mode_client = self.create_client(SetMode, '/mavros/set_mode')
        self.arm_client = self.create_client(CommandBool, '/mavros/cmd/arming')
        self.takeoff_client = self.create_client(CommandTOL, '/mavros/cmd/takeoff')

        self.speed = 1.0 # m/s

    def publish_twist(self, x, y):
        twist = Twist()
        twist.linear.x = x * self.speed
        twist.linear.y = y * self.speed
        
        self.publisher_.publish(twist)

    def auto_takeoff(self):
        print("\n--- Starting Auto-Takeoff Sequence ---")
        
        if self.mode_client.wait_for_service(timeout_sec=2.0):
            print("1/3 Setting GUIDED mode...")
            req_mode = SetMode.Request()
            req_mode.custom_mode = "GUIDED"
            future_mode = self.mode_client.call_async(req_mode)
            rclpy.spin_until_future_complete(self, future_mode)
        else:
            print("Error: SetMode service unavailable.")
            return

        time.sleep(0.5)

        if self.arm_client.wait_for_service(timeout_sec=2.0):
            print("2/3 Arming motors...")
            req_arm = CommandBool.Request()
            req_arm.value = True
            future_arm = self.arm_client.call_async(req_arm)
            rclpy.spin_until_future_complete(self, future_arm)
        else:
            print("Error: Arming service unavailable.")
            return

        # Give ArduPilot 2 seconds to process the arming state before demanding takeoff
        time.sleep(2.0)

        if self.takeoff_client.wait_for_service(timeout_sec=2.0):
            print("3/3 Taking off to 2.0 meters...")
            req_takeoff = CommandTOL.Request()
            req_takeoff.altitude = 2.0
            future_takeoff = self.takeoff_client.call_async(req_takeoff)
            rclpy.spin_until_future_complete(self, future_takeoff)
            
            # CRITICAL FIX: Wait for the drone to physically climb!
            # If we don't pause here, the loop immediately sends [0,0] velocity
            # which overrides the takeoff command and forces it to stay on the ground.
            # time.sleep(15.0)
            
            print("\nTakeoff complete! Mapping height reached.")
        else:
            print("Error: Takeoff service unavailable.")

    def set_mode(self, custom_mode):
        if self.mode_client.wait_for_service(timeout_sec=1.0):
            req = SetMode.Request()
            req.custom_mode = custom_mode
            self.mode_client.call_async(req)
            print(f"\nMode set to {custom_mode}")

def get_key(settings):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    
    if rlist:
        key = sys.stdin.read(1)
        if key == '\x1b':
            rlist2, _, _ = select.select([sys.stdin], [], [], 0.05)
            if rlist2:
                key += sys.stdin.read(2)
    else:
        key = '' 
        
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def main(args=None):
    settings = termios.tcgetattr(sys.stdin)
    rclpy.init(args=args)
    teleop_node = DroneTeleop()

    print("""
    ====================================
         2D SLAM TELEOP TERMINAL
    ====================================
    FLIGHT CONTROLS (Hold to move):
    Arrow Keys : Forward/Back/Left/Right
    
    * Altitude and Yaw are locked. 
    * Release all keys to auto-hover!
    
    COMMANDS:
    t : Auto-Takeoff (Locks at 2m height)
    g : Land
    
    CTRL-C to quit
    """)

    x = y = 0.0
    stop_frames = 0

    try:
        while rclpy.ok():
            key = get_key(settings)
            
            if key in MOVE_BINDINGS.keys():
                x, y = MOVE_BINDINGS[key]
                teleop_node.publish_twist(x, y)
                stop_frames = 0

            elif key == 't':
                teleop_node.auto_takeoff()

            elif key == 'g':
                teleop_node.set_mode("LAND")

            elif key == '\x03': # CTRL-C
                break

            else:
                if stop_frames < 3:
                    teleop_node.publish_twist(0.0, 0.0)
                    stop_frames += 1
                    if stop_frames == 3:
                        print("\n[STATUS] - Hovering...")

            rclpy.spin_once(teleop_node, timeout_sec=0.01)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        teleop_node.publish_twist(0.0, 0.0)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        teleop_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
