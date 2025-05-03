from launch import LaunchDescription
from launch_ros.substitutions import FindPackageShare
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, LogInfo, ExecuteProcess, TimerAction
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

def generate_launch_description():
    is_sim = DeclareLaunchArgument("is_sim", default_value="true")
    world = DeclareLaunchArgument("world", default_value="default.sdf")

    # 로봇 1 (cubo1) 네임스페이스 설정
    namespace1 = DeclareLaunchArgument("namespace1", default_value="cubo1")
    # 로봇 2 (cubo2) 네임스페이스 설정
    namespace2 = DeclareLaunchArgument("namespace2", default_value="cubo2")

    upload_robot1 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            get_package_share_directory('cubo_description'),
            '/launch/upload_robot.launch.py']
        ),
        launch_arguments = {
            'is_sim': LaunchConfiguration('is_sim'),
            'namespace': LaunchConfiguration('namespace1'),
        }.items()
    )

    upload_robot2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            get_package_share_directory('cubo_description'),
            '/launch/upload_robot.launch.py']
        ),
        launch_arguments = {
            'is_sim': LaunchConfiguration('is_sim'),
            'namespace': LaunchConfiguration('namespace2'),
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

    # 로봇 생성 노드 정의
    spawn_robot1 = Node(
        package='ros_gz_sim',
        executable='create',
        namespace=LaunchConfiguration('namespace1'),
        output='both',
        arguments=[
            '-name', LaunchConfiguration('namespace1'),
            '-topic', 'robot_description',
            '-allow_renaming', 'true',
            '-x', '1.0',
            '-y', '1.0',
            '-z', '0.1',
        ],
        parameters=[{
            "use_sim_time": LaunchConfiguration('is_sim')
        }],
    )

    spawn_robot2 = Node(
        package='ros_gz_sim',
        executable='create',
        namespace=LaunchConfiguration('namespace2'),
        output='both',
        arguments=[
            '-name', LaunchConfiguration('namespace2'),
            '-topic', 'robot_description',
            '-allow_renaming', 'true',
            '-x', '2.5',
            '-y', '1.0',
            '-z', '0.1',
        ],
        parameters=[{
            "use_sim_time": LaunchConfiguration('is_sim')
        }],
    )

    # Gazebo Sim 초기화 대기
    wait_for_gazebo = TimerAction(
        period=5.0,  # 5초 대기
        actions=[
            spawn_robot1,
            spawn_robot2,
        ]
    )

    load_joint_state_broadcaster1 = Node(
        package="controller_manager",
        executable="spawner",
        output='screen',
        namespace=LaunchConfiguration('namespace1'),
        arguments=["joint_state_broadcaster", "--controller-manager", "controller_manager"],
    )

    load_base_controller1 = Node(
        package="controller_manager",
        executable="spawner",
        namespace=LaunchConfiguration('namespace1'),
        arguments=["base_controller", "--controller-manager", "controller_manager"],
    )

    load_lift_controller1 = Node(
        package="controller_manager",
        executable="spawner",
        namespace=LaunchConfiguration('namespace1'),
        arguments=["lift_controller", "--controller-manager", "controller_manager"],
    )

    load_joint_state_broadcaster2 = Node(
        package="controller_manager",
        executable="spawner",
        output='screen',
        namespace=LaunchConfiguration('namespace2'),
        arguments=["joint_state_broadcaster", "--controller-manager", "controller_manager"],
    )

    load_base_controller2 = Node(
        package="controller_manager",
        executable="spawner",
        namespace=LaunchConfiguration('namespace2'),
        arguments=["base_controller", "--controller-manager", "controller_manager"],
    )

    load_lift_controller2 = Node(
        package="controller_manager",
        executable="spawner",
        namespace=LaunchConfiguration('namespace2'),
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
        name="static_lidar_tf_pub1",
        executable='static_transform_publisher',
        arguments=[
            '--x', '0.0',
            '--y', '0.0',
            '--z', '0.0',
            '--roll', '0.0',
            '--pitch', '0.0',
            '--yaw', '0.0',
            '--frame-id', 'lidar',
            '--child-frame-id', 'cubo1/fixed_base/lidar'
        ],
        output='screen'
    )

    static_lidar_tf2 = Node(
        package='tf2_ros',
        name="static_lidar_tf_pub2",
        executable='static_transform_publisher',
        arguments=[
            '--x', '0.0',
            '--y', '0.0',
            '--z', '0.0',
            '--roll', '0.0',
            '--pitch', '0.0',
            '--yaw', '0.0',
            '--frame-id', 'lidar',
            '--child-frame-id', 'cubo2/fixed_base/lidar'
        ],
        output='screen'
    )

    return LaunchDescription([
        is_sim,
        world,
        namespace1,
        namespace2,
        upload_robot1,
        upload_robot2,
        bringup_gazebo,
        wait_for_gazebo,
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_robot1,
                on_exit=[load_joint_state_broadcaster1]
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=load_joint_state_broadcaster1,
                on_exit=[
                    LogInfo(msg='joint state broadcaster for cubo1 spawned, spawn base_controller'),
                    load_base_controller1,
                    load_lift_controller1,
                ]
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=load_base_controller1,
                on_exit=[
                    LogInfo(msg='base_controller for cubo1 spawned, spawn static_lidar_tf and gz_bridge'),
                    ros_gz_bridge,
                    static_lidar_tf1,
                ]
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_robot2,
                on_exit=[load_joint_state_broadcaster2]
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=load_joint_state_broadcaster2,
                on_exit=[
                    LogInfo(msg='joint state broadcaster for cubo2 spawned, spawn base_controller'),
                    load_base_controller2,
                    load_lift_controller2,
                ]
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=load_base_controller2,
                on_exit=[
                    LogInfo(msg='base_controller for cubo2 spawned, spawn static_lidar_tf for cubo2'),
                    static_lidar_tf2,
                ]
            )
        ),
    ])