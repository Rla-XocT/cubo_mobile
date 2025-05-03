from launch import LaunchDescription
from launch_ros.substitutions import FindPackageShare
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, LogInfo
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

def generate_launch_description():
    is_sim = DeclareLaunchArgument("is_sim", default_value="true")
    namespace = DeclareLaunchArgument("namespace", default_value="")
    world = DeclareLaunchArgument("world", default_value="office_building.sdf")

    upload_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            get_package_share_directory('cubo_description'),
            '/launch/upload_robot.launch.py']
        ),
        launch_arguments = {
            'is_sim' : LaunchConfiguration('is_sim'),
            'namespace': LaunchConfiguration('namespace'),
        }.items()
    )

    bringup_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            get_package_share_directory('cubo_gazebo'),
            '/launch/bringup_gazebo.launch.py']
        ),
        launch_arguments = {
            'world_name' : LaunchConfiguration('world')
        }.items()
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        namespace=LaunchConfiguration('namespace'),
        output='both',
        arguments=[
            '-name', LaunchConfiguration('namespace'),
            '-topic', 'robot_description',
            '-allow_renaming', 'true'
            '-x', '1.0',
            '-y', '1.0',
            '-z', '0.2',
        ],
        parameters=[{
            "use_sim_time": LaunchConfiguration('is_sim')
        }],
    )

    load_joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        output='screen',
        namespace=LaunchConfiguration('namespace'),
        arguments=["joint_state_broadcaster", "--controller-manager", "controller_manager"],
    )

    load_base_controller = Node(
        package="controller_manager",
        executable="spawner",
        namespace=LaunchConfiguration('namespace'),
        arguments=["base_controller", "--controller-manager", "controller_manager"],
    )

    load_lift_controller = Node(
        package="controller_manager",
        executable="spawner",
        namespace=LaunchConfiguration('namespace'),
        arguments=["lift_controller", "--controller-manager", "controller_manager"],
    )

    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        name="ros_gz_bridge_sensors",
        executable='parameter_bridge',
        arguments=[
            '/lidar/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
            '/cmd_vel@geometry_msgs/msg/Twist@ignition.msgs.Twist',
            '/imu@sensor_msgs/msg/Imu@ignition.msgs.IMU'
        ],
        output='screen'
    )

    static_lidar_tf1 = Node(
        package='tf2_ros',
        name="static_lidar_tf_pub",
        executable='static_transform_publisher',
        arguments=[
            '--x', '0.0',
            '--y', '0.0',
            '--z', '0.0',
            '--roll', '0.0',
            '--pitch', '0.0',
            '--yaw', '0.0',
            '--frame-id', 'lidar',
            '--child-frame-id', 'cubo/fixed_base/lidar'
        ],
        output='screen'
    )

    return LaunchDescription([
        is_sim,
        namespace,
        world,
        upload_robot,
        bringup_gazebo,
        spawn_robot,
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_robot,
                on_exit=[load_joint_state_broadcaster]
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=load_joint_state_broadcaster,
                on_exit=[
                    LogInfo(msg='joint state broadcaster spawned, spawn base_controller'),
                    load_base_controller,
                    load_lift_controller,
                ]
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=load_base_controller,
                on_exit=[
                    LogInfo(msg='base_controller spawned, spawn gz_bridge and static transforms'),
                    ros_gz_bridge,
                    static_lidar_tf1,  # 라이다 정적 트랜스폼 노드 추가
                ]
            )
        ),
    ])

###로봇 구동 커맨드
# ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/base_controller/cmd_vel_unstamped
