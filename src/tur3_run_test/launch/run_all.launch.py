import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory
import os
import launch.launch_description_sources
def generate_launch_description():
    multisim_launch_path = [get_package_share_directory('robocon2027_description'), '/launch/', 'test.launch.py']
    action_include_launch = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            multisim_launch_path,
        )
    )
    multisim_launch_path2 = [get_package_share_directory('tur3_run_test'), '/launch/', 'nav2.launch.py']
    action_include_launch2 = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            multisim_launch_path2,
        )
    )

    action1= launch_ros.actions.Node(
        package='tur3_run_test',
        executable='nav_to_pose',
        output='screen'
    )

    action2= launch_ros.actions.Node(
        package='tur3_run_test',
        executable='run_slope',
        output='screen'
    )

    action_group = launch.actions.GroupAction([
        # 动作5-定时器
        launch.actions.TimerAction(period=3.0, actions=[action_include_launch2]), #2秒后执行
        launch.actions.TimerAction(period=4.0, actions=[action1]), #4秒后执行
        launch.actions.TimerAction(period=4.0, actions=[action2]) #4秒后执行
    ])

    return launch.LaunchDescription([
        action_include_launch,
        # action_include_launch2,
        # action1,
        # action2,
        action_group,
    ])

# ros2 launch rc_run demo.launch.py 
# 感觉我的gazebo跟别人不一样，比如picture里的图片，不开碰撞体积只能看到墙，可能参数不对，
# 不会给turtlebot3_waffle加差速控制器，
# 用了鱼香ros chapt6的机器人，改了些参数
# 雷达扫图结果在map