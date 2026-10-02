#!/usr/bin/env python3

import sys
import termios
import tty

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


msg = """
Reading from the keyboard and publishing to /cmd_vel !

速度调节：
   w/e/r : 增加线速度(10%)
   z/x/c : 降低线速度(10%)

运动控制：
   i : 前进
   , : 后退
   m : 左移
   . : 右移
   j : 左转
   l : 右转
   k : 停止

CTRL-C to quit
"""


class TeleopTwistKeyboard(Node):
    def __init__(self):
        super().__init__('teleop_twist_keyboard')

        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)

        # teleop_twist_keyboard 默认速度
        self.speed = 0.5          # 线速度 m/s
        self.turn = 1.0           # 角速度 rad/s
        self.speed_limit = 4.0
        self.turn_limit = 4.0

        # 当前速度指令
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.th = 0.0

        self.settings = termios.tcgetattr(sys.stdin)

        self.print_msg()

    def print_msg(self):
        print(msg)
        print(f"当前速度：speed={self.speed:.2f}, turn={self.turn:.2f}\n")

    def get_key(self):
        tty.setraw(sys.stdin.fileno())
        key = sys.stdin.read(1)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def print_speed(self):
        print(f"当前速度：speed={self.speed:.2f}, turn={self.turn:.2f}")

    def publish_cmd(self):
        twist = Twist()
        twist.linear.x = self.x
        twist.linear.y = self.y
        twist.linear.z = self.z
        twist.angular.x = 0.0
        twist.angular.y = 0.0
        twist.angular.z = self.th
        self.publisher_.publish(twist)

    def process_key(self, key):
        # 速度调节：只改速度参数，不发布
        if key in ('w', 'e', 'r'):
            self.speed = min(self.speed * 1.1, self.speed_limit)
            self.turn = min(self.turn * 1.1, self.turn_limit)
            self.print_speed()
            return

        if key in ('z', 'x', 'c'):
            self.speed = max(self.speed * 0.9, 0.0)
            self.turn = max(self.turn * 0.9, 0.0)
            self.print_speed()
            return

        # 运动控制：每按一次，发一次
        if key == 'i':        # 前进
            self.x = self.speed
            self.y = 0.0
            self.th = 0.0
        elif key == ',':      # 后退
            self.x = -self.speed
            self.y = 0.0
            self.th = 0.0
        elif key == 'm':      # 左移
            self.x = 0.0
            self.y = self.speed
            self.th = 0.0
        elif key == '.':      # 右移
            self.x = 0.0
            self.y = -self.speed
            self.th = 0.0
        elif key == 'j':      # 左转
            self.x = 0.0
            self.y = 0.0
            self.th = self.turn
        elif key == 'l':      # 右转
            self.x = 0.0
            self.y = 0.0
            self.th = -self.turn
        elif key == 'k':      # 停止
            self.x = 0.0
            self.y = 0.0
            self.z = 0.0
            self.th = 0.0
        else:
            # 其他键不处理，也不发布
            return

        self.publish_cmd()

    def run(self):
        try:
            while rclpy.ok():
                key = self.get_key()
                if key == '\x03':  # Ctrl-C
                    break
                self.process_key(key)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
            # 退出前发一次停止指令，避免机器人一直动
            self.x = self.y = self.z = self.th = 0.0
            self.publish_cmd()


def main(args=None):
    rclpy.init(args=args)
    node = TeleopTwistKeyboard()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()