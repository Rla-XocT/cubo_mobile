import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped

class CentralControlNode(Node):
    def __init__(self):
        super().__init__('multi_nav_node')
        # Action clients for robots
        self.robot1_client = ActionClient(self, NavigateToPose, '/robot1/navigate_to_pose')
        self.robot2_client = ActionClient(self, NavigateToPose, '/robot2/navigate_to_pose')
        
        # Subscriber for pallet info
        self.pallet_sub = self.create_subscription(String, '/pallet_info', self.pallet_info_callback, 10)
        
        # Pallet locations and destinations
        self.pallet_locations = {
            'D': (-6.11, 3.97, 0.0),  # 팔레트 1 위치
            'E': (-13, 1.59, 0.0)     # 팔레트 2 위치
        }
        self.destinations = {
            'DO1': (-4.9, 2.87, 0.0),  # 도킹스테이션 1
            'DO2': (-4.87, 3.77, 0.0)  # 도킹스테이션 2
        }
        
        self.get_logger().info("Central Control Node Started")

    def pallet_info_callback(self, msg):
        location, destination, weight = msg.data.split(',')
        weight = int(weight)
        
        if weight >= 50:  # 팔레트 무게 임계값: 50kg
            self.get_logger().info(f"Pallet weight: {weight} kg. Calling robots for transport.")
            self.coordinate_pallet_transport(location, destination)

    def coordinate_pallet_transport(self, location, destination):
        # Move robots to pallet location
        self.move_robots_to_pallet(location)
        
        # Lift pallet and move to destination
        self.move_robots_with_pallet(destination)

    def move_robots_to_pallet(self, location):
        # 팔레트 위치를 기준으로 로봇의 위치를 조정
        pallet_x, pallet_y, _ = self.pallet_locations[location]
        robot1_x, robot1_y = pallet_x - 0.5, pallet_y  # 로봇 1 위치 조정
        robot2_x, robot2_y = pallet_x + 0.5, pallet_y  # 로봇 2 위치 조정
        
        # Move robot 1 to adjusted position
        self.send_goal(self.robot1_client, (robot1_x, robot1_y, 0.0))
        
        # Move robot 2 to adjusted position
        self.send_goal(self.robot2_client, (robot2_x, robot2_y, 0.0))
        
        self.get_logger().info(f"Robots are moving to pallet at {location}.")

    def move_robots_with_pallet(self, destination):
        # Lift pallet
        self.get_logger().info("Robots are lifting the pallet.")
        
        # 로봇과 팔레트를 하나의 몸체로 움직이기
        dest_x, dest_y, _ = self.destinations[destination]
        robot1_x, robot1_y = dest_x - 0.5, dest_y  # 로봇 1 목표 위치 조정
        robot2_x, robot2_y = dest_x + 0.5, dest_y  # 로봇 2 목표 위치 조정
        
        # Move robot 1 to adjusted destination
        self.send_goal(self.robot1_client, (robot1_x, robot1_y, 0.0))
        
        # Move robot 2 to adjusted destination
        self.send_goal(self.robot2_client, (robot2_x, robot2_y, 0.0))
        
        self.get_logger().info(f"Robots are transporting pallet to {destination}.")

    def send_goal(self, robot_client, target):
        x, y, _ = target
        goal_msg = PoseStamped()
        goal_msg.header.frame_id = 'map'
        goal_msg.pose.position.x = x
        goal_msg.pose.position.y = y
        goal_msg.pose.orientation.w = 1.0
        robot_client.wait_for_server()
        robot_client.send_goal_async(goal_msg)

def main(args=None):
    rclpy.init(args=args)
    node = CentralControlNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()