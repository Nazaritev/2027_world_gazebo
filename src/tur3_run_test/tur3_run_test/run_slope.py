import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Twist
from tf_transformations import euler_from_quaternion  # 四元数转欧拉角函数
import time
from tur3_run_interfaces.srv import UseNavToPose
import threading
from tur3_run_interfaces.msg import Slope
# -0.162
# ros2 run tur3_run_test run_slope
class ImuYawListener(Node):
    def __init__(self):
        super().__init__('imu_yaw_listener')
        thread = threading.Thread(target=self.nav_service)
        thread.start()
        self.subscription = self.create_subscription(
            Imu,
            '/imu',
            self.imu_callback,
            10
        )
        self.continue_time = 0.2
        self.start = False
        self.pitch = 0
        self.bool_slope = 0
        self.get_logger().info('imu_yaw_listener started, waiting for /imu ...')
        self.start_time = time.time()
        self.out_time_slop = None
        self.start_time_slop = None
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 5)
        self.bool_pitch = self.create_timer(0.1,self.bool_pitch_callback)
        self.bool_stop = self.create_timer(0.1,self.bool_stop_callback)
        self.twist = Twist()
        self.twist.linear.x = 0.4

    def nav_service(self):
        self.service = self.create_subscription(Slope,'/slope',self.go_slope,5)
        self.pub = self.create_publisher(Slope,'/slope',5)


    def go_slope(self,msg):
        if msg.slope == 1:
            self.start = True
            self.continue_time = 0.6

        
    def bool_stop_callback(self):
        if self.start == False:
            return
        if self.bool_slope == 2:
            self.twist.linear.x = 0.2
            self.publisher.publish(self.twist)
            time.sleep(self.continue_time)
            self.publisher.publish(Twist())
            self.twist.linear.x = 0.2
            self.start = False
            sl = Slope()
            sl.slope = 2
            self.pub.publish(sl)
            # self.get_logger().info(f'1111111111111111')
            self.bool_slope = 0
            return
        self.publisher.publish(self.twist)
        
            


    def bool_pitch_callback(self):
        if self.start == False:
            return
        if self.start_time_slop != None and time.time() - self.start_time_slop > 0.5:
            self.bool_slope = 1
        if self.pitch < -0.15:
            if self.start_time_slop == None:
                self.start_time_slop = time.time()
        if self.bool_slope == 1 and self.pitch > -0.05:
            self.bool_slope = 2
        if self.start_time_slop != None and time.time() - self.start_time_slop > 7:
            self.twist.linear.x = 0.3
            self.publisher.publish(self.twist)
            


    def imu_callback(self, msg):
        q = msg.orientation

        # 四元数 -> 欧拉角 (roll, pitch, yaw)，单位：弧度
        rotation_euler = euler_from_quaternion([
            q.x,
            q.y,
            q.z,
            q.w,
        ])

        roll, pitch, yaw = rotation_euler
        self.pitch = pitch

        # self.get_logger().info(f'四元数: x={q.x:.4f}, y={q.y:.4f}, z={q.z:.4f}, w={q.w:.4f}')
        if time.time() - self.start_time > 0.2:
            # self.get_logger().info(f'rool={rotation_euler[0]:.3f},pithch={rotation_euler[1]:.3f},yaw={rotation_euler[2]:.3f}')
            self.start_time = time.time()
        # self.get_logger().info(f'Yaw: {yaw:.4f} rad ({yaw * 180.0 / 3.141592653589793:.2f} deg)')


def main():
    rclpy.init()
    node = ImuYawListener()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()