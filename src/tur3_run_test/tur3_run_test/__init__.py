from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.duration import Duration
import math
from tf_transformations import quaternion_from_euler, euler_from_quaternion
import threading
from geometry_msgs.msg import Twist
import time
from tur3_run_interfaces.srv import UseNavToPose, NavOnce
from tur3_run_interfaces.msg import Slope


class NavToPose(BasicNavigator):
    def __init__(self):
        super().__init__('nav_to_pose')
        self.yaw = 0
        self.bool_slope = False

        # ---- 发布者 ----
        self.slope_publisher = self.create_publisher(Slope, '/slope', 5)
        self.vw_publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        # ---- 服务客户端 ----
        self.nav_mode_client = self.create_client(UseNavToPose, '/nav_mode/slope')

        # ---- 订阅（在主线程创建） ----
        self.after_slop = self.create_subscription(Slope, '/slope', self.slope_callback, 5)
        self.get_pose = self.create_subscription(Odometry, '/odom', self.nav_pose_callback, 1)

        # ---- 任务序列放到独立线程执行 ----
        self.task_thread = threading.Thread(target=self.run_task, daemon=True)
        self.task_thread.start()

    # ------------------------------------------------------------------
    # 任务主流程
    # ------------------------------------------------------------------
    def run_task(self):
        self.pose_init(-4.55, -4.35, 0)
        self.nav_pose(3.98, -3.30, math.pi, True)

        # 通知 /slope 开始上坡
        sl = Slope()
        sl.slope = 1
        self.slope_publisher.publish(sl)

        # ★ 等待时手动 spin_once，让 /slope 回调能被处理
        while self.bool_slope != True:
            rclpy.spin_once(self, timeout_sec=0.1)

        time.sleep(1)
        self.nav_pose(-1.25, -2.74, -math.pi / 2, True)
        time.sleep(1)
        self.adj_angle(-math.pi / 2, -math.pi)
        self.nav_pose(-2.35, -2.65, math.pi, True)
        self.adj_angle(math.pi, -math.pi / 2)
        self.nav_pose(-1.35, -2.74, -math.pi / 2, True)
        self.adj_angle(-math.pi / 2, 0)
        time.sleep(1)
        self.nav_pose(2.3, -2.70, 0, True)
        self.adj_angle(0, math.pi)
        self.nav_pose(-1.35, -3.0, -math.pi / 2, True)
        self.get_logger().info('任务全部完成')

    # ------------------------------------------------------------------
    # 回调
    # ------------------------------------------------------------------
    def slope_callback(self, msg):
        self.get_logger().info(f'slope: {msg.slope}')
        if msg.slope == 2:
            self.bool_slope = True
            self.get_logger().info('收到上坡完成信号')

    def nav_pose_callback(self, msg):
        q = msg.pose.pose.orientation
        roll, pitch, self.yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])

    # ------------------------------------------------------------------
    # 基础动作
    # ------------------------------------------------------------------
    def back(self, vx, dis):
        msg = Twist()
        msg.linear.x = -vx
        self.vw_publisher.publish(msg)
        time.sleep(dis / vx)
        self.vw_publisher.publish(Twist())

    def pose_init(self, x, y, yaw):
        initial_pose = PoseStamped()
        initial_pose.header.frame_id = 'map'
        initial_pose.header.stamp = self.get_clock().now().to_msg()
        initial_pose.pose.position.x = x
        initial_pose.pose.position.y = y
        initial_pose.pose.position.z = 0.0
        initial_pose.pose.orientation.x = 0.0
        initial_pose.pose.orientation.y = 0.0
        initial_pose.pose.orientation.z = math.sin(yaw / 2.0)
        initial_pose.pose.orientation.w = math.cos(yaw / 2.0)
        self.setInitialPose(initial_pose)

    def adj_angle(self, yaw_now, yaw_goal):
        yaw = math.atan2(math.sin(yaw_goal - yaw_now), math.cos(yaw_goal - yaw_now))
        self.get_logger().info(f'修正角度{yaw}')
        twis = Twist()
        if yaw < 0:
            twis.angular.z = -1.0
        else:
            twis.angular.z = 1.0
        sleep_time = int(yaw / twis.angular.z * 10000) / 10000
        time.sleep(1.5)
        self.vw_publisher.publish(twis)
        self.get_logger().info(f'{sleep_time}')
        t = sleep_time - 0.0
        if t < 0:
            t = sleep_time
        time.sleep(t)
        self.vw_publisher.publish(Twist())
        self.get_logger().info('角度调节完成')
        time.sleep(0.5)

    def nav_pose(self, x, y, yaw_goal, adjust_angle):
        self.waitUntilNav2Active()

        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.header.stamp = self.get_clock().now().to_msg()
        goal_pose.pose.position.x = x
        goal_pose.pose.position.y = y
        yaw = yaw_goal
        goal_pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_pose.pose.orientation.w = math.cos(yaw / 2.0)

        self.goToPose(goal_pose)

        while not self.isTaskComplete():
            feedback = self.getFeedback()
            self.get_logger().info(
                f'预计: {Duration.from_msg(feedback.estimated_time_remaining).nanoseconds / 1e9} s 后到达')
            if Duration.from_msg(feedback.navigation_time) > Duration(seconds=600.0):
                self.cancelTask()

        result = self.getResult()
        if result == TaskResult.SUCCEEDED:
            self.get_logger().info('导航结果：成功')
        elif result == TaskResult.CANCELED:
            self.get_logger().warn('导航结果：被取消')
        elif result == TaskResult.FAILED:
            self.get_logger().error('导航结果：失败')
        else:
            self.get_logger().error('导航结果：返回状态无效')

        if adjust_angle == True and result == TaskResult.SUCCEEDED:
            yaw_now = self.yaw
            self.adj_angle(yaw_now, yaw_goal)


def main():
    rclpy.init()
    node = NavToPose()

    # ★ 等任务线程跑完，不再外部 spin
    node.task_thread.join()

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()