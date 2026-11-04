"""Fast choreography preview: ideal position tracking, paced at ~real time.

Uses the installed simulator's 'none' backend. This previews choreography and
control sequencing; it does not simulate drone physics or tracking error.
"""
from pathlib import Path
import sys
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# ROS loads this file by absolute path rather than as a Python package.
PROJECT_ROOT=Path(__file__).resolve().parents[2]
CONFIG_DIR=PROJECT_ROOT/'simulation'/'config'


def setup(context):
    scene=LaunchConfiguration('scene').perform(context)
    if scene not in ('formations',):raise ValueError('Unknown preview scene')
    server={'formations':'preview_server'}[scene]
    share = Path(get_package_share_directory('crazyflie'))
    robot_file=LaunchConfiguration('crazyflies_yaml_file').perform(context)
    with open(robot_file) as source:
        robots = yaml.safe_load(source)
    with open(share / 'config' / 'server.yaml') as source:
        params = yaml.safe_load(source)['/crazyflie_server']['ros__parameters']
    description = Path(get_package_share_directory('crazyflie_description')) / 'urdf' / 'crazyflie_description.urdf'
    params['robot_description'] = description.read_text()
    params['sim'].update(backend='none', controller='none', max_dt=0.02)
    return [
        Node(executable=sys.executable, arguments=['-m','simulation.servers.'+server], cwd=str(PROJECT_ROOT),
             name='crazyflie_server', output='screen', parameters=[robots, params]),
        Node(package='rviz2', executable='rviz2', name='rviz2',
             condition=IfCondition(LaunchConfiguration('rviz')),
             arguments=['-d', LaunchConfiguration('rviz_config_file')],
             parameters=[{'use_sim_time': True}]),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('scene',default_value='formations'),
        DeclareLaunchArgument('crazyflies_yaml_file',
                              default_value=str(CONFIG_DIR / 'crazyflies.yaml')),
        DeclareLaunchArgument('rviz', default_value='True'),
        DeclareLaunchArgument('rviz_config_file',
                              default_value=str(CONFIG_DIR / 'swarmgesture.rviz')),
        OpaqueFunction(function=setup),
    ])
