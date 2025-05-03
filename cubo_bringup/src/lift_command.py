import rclpy
from rclpy.node import Node
from std_msgs.msg import String  
import os

class CanInterfaceNode(Node):

    def __init__(self):
        super().__init__('can_interface_node')
        self.subscription = self.create_subscription(
             String,
             'can_command',
             self.listener_callback,
             10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        command = msg.data
        self.send_can_command(command)

    def send_can_command(self, command):
        os.system(f'cansend can0 {command}')
        self.get_logger().info(f'Sent CAN command: {command}')

def main(args=None):
    rclpy.init(args=args)
    node = CanInterfaceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

#ros2 topic pub /can_command std_msgs/String "data: '607#2300270000F00000'"

#607#2300270C00000400 →  baudrate설정 (can2 : 04)

#607#2300270000F00000 → 리프트 업

#607#23002700000F0000 → 리프트 다운

#607#23002700000002CC →  리프트 초기화