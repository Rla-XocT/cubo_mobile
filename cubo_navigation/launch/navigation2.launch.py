#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    map_dir = LaunchConfiguration(
        'map',
        default=os.path.join(
            get_package_share_directory('cubo_navigation'),
            'map','map.yaml')
    )

    param_file_name = 'navigation2.yaml'
    param_dir = LaunchConfiguration(
        'params_file',
        default=os.path.join(
            get_package_share_directory('cubo_navigation'),
            'config',
            param_file_name
        )
    )

    nav2_launch_file_dir = os.path.join(get_package_share_directory('nav2_bringup'), 'launch')

    nav_include = IncludeLaunchDescription(PythonLaunchDescriptionSource(nav2_launch_file_dir + '/bringup_launch.py'),
                                           launch_arguments={
                                               'map' : map_dir,
                                               'use_sim_time' : use_sim_time,
                                               'params_file' : param_dir}.items()
    )

    laser_node = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0", "0", "0", "0", "0", "0", "1", "map", "odom"]
    )

    # Add remappings for the controller server
    controller_node_remap = Node(
        package='nav2_controller',
        executable='controller_server',
        remappings=[
            ('/cmd_vel', '/base_controller/cmd_vel_unstamped')
        ],
        parameters=[param_dir],
        output='screen'
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value=map_dir,
            description='Full path to map file to load'
        ),

        DeclareLaunchArgument(
            'params_file',
            default_value=param_dir,
            description='Full path to parameter file to load'
        ),

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true'
        ),

        laser_node,
        nav_include,
        controller_node_remap  # Include the controller node with remap
    ])