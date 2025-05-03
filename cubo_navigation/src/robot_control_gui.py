import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
import tkinter as tk
from tkinter import ttk
import threading
import time

class RobotControlPanel(tk.Tk):
    def __init__(self, node):
        super().__init__()
        self.node = node
        self.title("ZooPang Control System")
        self.geometry("1000x600")

        self.publisher = node.create_publisher(PoseStamped, '/goal_pose', 10)
        self.goal_positions = {
            'A': (-1.89, 2.65, 0.0),  # 작업대 A
            'B': (1.52, 2.59, 0.0),   # 작업대 B
            'C': (2.26, 3.88, 0.0),   # 작업대 C
            'D': (-6.11, 3.97, 0.0),  # 팔레트 1 위치
            'E': (-13, 1.59, 0.0),    # 팔레트 2 위치
            'DO1': (-4.9, 2.87, 0.0), # 도킹스테이션 1
            'DO2': (-4.87, 3.77, 0.0) # 도킹스테이션 2
        }

        # 로봇 상태 변수
        self.robot_status = {
            "Robot 1": {"task": "Idle", "battery": 100},
            "Robot 2": {"task": "Idle", "battery": 100}
        }

        style = ttk.Style()
        style.theme_use("clam")
        style.configure('TButton', background='#4CAF50', foreground='white', padding=6)
        style.map('TButton', background=[('active', '#45A049')])
        style.configure('TLabel', background='lightgrey', foreground='black')

        title_label = ttk.Label(self, text="ZooPang Control System", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)

        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill=tk.BOTH)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=10)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.create_status_boxes(left_frame)
        self.create_movement_buttons(right_frame)
        self.create_pallet_control(right_frame)

    def create_status_boxes(self, frame):
        ttk.Label(frame, text="Robot Statuses:", font=("Helvetica", 12)).pack(pady=5)
        self.status_text_vars = {}
        self.battery_text_vars = {}
        for robot_name in self.robot_status:
            row_frame = ttk.Frame(frame)
            row_frame.pack(pady=5)
            ttk.Label(row_frame, text=robot_name, font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
            status_var = tk.StringVar(value="Idle")
            self.status_text_vars[robot_name] = status_var
            status_entry = ttk.Entry(row_frame, textvariable=status_var, font=("Helvetica", 12), width=20, state="readonly")
            status_entry.pack(side=tk.LEFT, padx=5)
            battery_var = tk.StringVar(value="100%")
            self.battery_text_vars[robot_name] = battery_var
            battery_entry = ttk.Entry(row_frame, textvariable=battery_var, font=("Helvetica", 12), width=10, state="readonly")
            battery_entry.pack(side=tk.LEFT, padx=5)

    def create_movement_buttons(self, frame):
        ttk.Label(frame, text="Move Robot:", font=("Helvetica", 12)).pack(pady=5)

        self.selected_robot = tk.StringVar()
        robot_buttons = ["Robot 1", "Robot 2"]
        for robot_name in robot_buttons:
            button = ttk.Radiobutton(frame, text=robot_name, variable=self.selected_robot, value=robot_name)
            button.pack(side=tk.TOP, padx=5)

        self.location_var = tk.StringVar()
        self.location_entry = ttk.Entry(frame, textvariable=self.location_var, width=10, state="readonly")
        self.location_entry.pack(pady=5)

        buttons_row_1 = ["A", "B", "C"]
        row_frame_1 = ttk.Frame(frame)
        row_frame_1.pack(pady=(0, 10))
        for loc in buttons_row_1:
            button = ttk.Button(row_frame_1, text=loc, command=lambda l=loc: self.set_location(l))
            button.pack(side=tk.LEFT, padx=5)

        buttons_row_2 = ["D", "E", "DO1", "DO2"]
        row_frame_2 = ttk.Frame(frame)
        row_frame_2.pack(pady=(0, 10))
        for loc in buttons_row_2:
            button = ttk.Button(row_frame_2, text=loc, command=lambda l=loc: self.set_location(l))
            button.pack(side=tk.LEFT, padx=5)

        input_button = ttk.Button(frame, text="Move Robot", command=self.execute_task)
        input_button.pack(pady=10)

    def create_pallet_control(self, frame):
        ttk.Label(frame, text="Pallet Control:", font=("Helvetica", 12)).pack(pady=5)

        # 팔레트 1 무게 설정
        pallet1_frame = ttk.Frame(frame)
        pallet1_frame.pack(pady=5)
        ttk.Label(pallet1_frame, text="Pallet 1 Weight (kg):", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.pallet1_weight_var = tk.IntVar(value=0)
        weight_entry1 = ttk.Entry(pallet1_frame, textvariable=self.pallet1_weight_var, width=10)
        weight_entry1.pack(side=tk.LEFT, padx=5)
        set_weight_button1 = ttk.Button(pallet1_frame, text="Set", command=lambda: self.set_pallet_weight(1))
        set_weight_button1.pack(side=tk.LEFT, padx=5)

        # 팔레트 2 무게 설정
        pallet2_frame = ttk.Frame(frame)
        pallet2_frame.pack(pady=5)
        ttk.Label(pallet2_frame, text="Pallet 2 Weight (kg):", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.pallet2_weight_var = tk.IntVar(value=0)
        weight_entry2 = ttk.Entry(pallet2_frame, textvariable=self.pallet2_weight_var, width=10)
        weight_entry2.pack(side=tk.LEFT, padx=5)
        set_weight_button2 = ttk.Button(pallet2_frame, text="Set", command=lambda: self.set_pallet_weight(2))
        set_weight_button2.pack(side=tk.LEFT, padx=5)

        # 로봇 호출 버튼
        call_robots_button = ttk.Button(frame, text="Call Robots for Pallet", command=self.call_robots_for_pallet)
        call_robots_button.pack(pady=10)

    def set_location(self, location):
        self.location_var.set(location)

    def set_pallet_weight(self, pallet_id):
        if pallet_id == 1:
            weight = self.pallet1_weight_var.get()
            print(f"Pallet 1 weight set to: {weight} kg")
        elif pallet_id == 2:
            weight = self.pallet2_weight_var.get()
            print(f"Pallet 2 weight set to: {weight} kg")

    def call_robots_for_pallet(self):
        pallet1_weight = self.pallet1_weight_var.get()
        pallet2_weight = self.pallet2_weight_var.get()

        if pallet1_weight >= 50:  # 팔레트 1 무게 임계값: 50kg
            self.update_status("Robot 1", "Moving to Pallet 1")
            self.update_status("Robot 2", "Moving to Pallet 1")
            self.move_to("D")  # 팔레트 1 위치로 이동
            time.sleep(2)
            self.update_status("Robot 1", "Transporting Pallet 1")
            self.update_status("Robot 2", "Transporting Pallet 1")
            self.move_to("DO1")  # 도킹스테이션 1로 이동
            time.sleep(2)
            self.update_status("Robot 1", "Idle")
            self.update_status("Robot 2", "Idle")
        elif pallet2_weight >= 50:  # 팔레트 2 무게 임계값: 50kg
            self.update_status("Robot 1", "Moving to Pallet 2")
            self.update_status("Robot 2", "Moving to Pallet 2")
            self.move_to("E")  # 팔레트 2 위치로 이동
            time.sleep(2)
            self.update_status("Robot 1", "Transporting Pallet 2")
            self.update_status("Robot 2", "Transporting Pallet 2")
            self.move_to("DO2")  # 도킹스테이션 2로 이동
            time.sleep(2)
            self.update_status("Robot 1", "Idle")
            self.update_status("Robot 2", "Idle")
        else:
            print("No pallet weight exceeds the threshold. No action taken.")

    def move_to(self, location):
        x, y, theta = self.goal_positions.get(location, (0.0, 0.0, 0.0))
        goal_msg = PoseStamped()
        goal_msg.header.frame_id = 'map'
        goal_msg.header.stamp = self.node.get_clock().now().to_msg()
        goal_msg.pose.position.x = x
        goal_msg.pose.position.y = y
        goal_msg.pose.orientation.z = 0.0
        goal_msg.pose.orientation.w = 1.0
        self.publisher.publish(goal_msg)
        print(f"목표 발행 중: {location} - x: {x}, y: {y}, theta: {theta}")

    def update_status(self, robot_name, message):
        self.robot_status[robot_name]["task"] = message
        self.status_text_vars[robot_name].set(message)

    def execute_task(self):
        robot_name = self.selected_robot.get()
        location = self.location_var.get().upper()
        if not robot_name:
            print("로봇을 선택해 주세요.")
            return
        if not location:
            print("위치를 선택해 주세요.")
            return

        self.update_status(robot_name, f"Moving to {location}")
        self.move_to(location)
        time.sleep(2)
        self.update_status(robot_name, "Idle")

def ros_spin(node):
    rclpy.spin(node)

def main(args=None):
    rclpy.init(args=args)
    node = Node('robot_control_node')
    app = RobotControlPanel(node)
    threading.Thread(target=ros_spin, args=(node,), daemon=True).start()
    app.mainloop()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()