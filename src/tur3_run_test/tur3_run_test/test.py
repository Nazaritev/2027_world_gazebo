#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from rclpy.duration import Duration

# ros2 run tur3_run_test nav2_rviz
class SideMove(Node):
    def __init__(self):
        super().__init__('side_move')

        # 与 teleop_twist_keyboard 默认话题一致
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)

        # 发布频率 10 Hz
        self.rate_hz = 10.0
        self.dt = 1.0 / self.rate_hz

        # 总时长 3 秒
        self.total_time = 0.2
        self.elapsed = 0.0

        self.timer = self.create_timer(self.dt, self.timer_callback)

        self.get_logger().info('side_move 启动：将发布 linear.y = 1.0，持续 3 秒...')

    def timer_callback(self):
        msg = Twist()
        if self.elapsed < self.total_time:
            msg.linear.x = 0.0
            msg.linear.y = 0.0     # 关键：横向速度
            msg.linear.z = 0.0
            msg.angular.x = 0.0
            msg.angular.y = 0.0
            msg.angular.z = 0.5
            self.pub.publish(msg)
            self.elapsed += self.dt
        else:
            # 时间到，发布一帧零速度让机器人停下，然后退出
            msg.linear.x = 0.0
            msg.linear.y = 0.0
            msg.angular.z = 0.0
            self.pub.publish(msg)
            self.get_logger().info('3 秒结束，发布停止指令，节点退出。')
            self.timer.cancel()
            raise SystemExit


def main(args=None):
    rclpy.init(args=args)
    node = SideMove()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()