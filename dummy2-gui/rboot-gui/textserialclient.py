#!/usr/bin/env python3
"""
文本串口通信客户端
用于支持ASCII文本协议的机械臂设备
命令格式：!START, !HOME, &angle1,angle2,...
"""

import serial
import serial.tools.list_ports
import threading
import time


class TextSerialClient:
    def __init__(self, port=None, baudrate=9600):
        """
        初始化文本串口客户端

        Args:
            port: 串口名称（如'COM7'），None则自动检测
            baudrate: 波特率，默认9600
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.connected = False
        self._stop_receive = False
        self.receive_thread = None
        self.callback = None
        self.last_connect_time = 0
        self.connect_interval = 0.5
        self.send_lock = threading.Lock()
        self.initialized = False  # 是否已发送START和HOME

    def list_ports(self):
        """列出所有可用的串口"""
        ports = serial.tools.list_ports.comports()
        return [{'device': p.device, 'description': p.description, 'hwid': p.hwid} for p in ports]

    def auto_detect_port(self):
        """自动检测可用的串口"""
        ports = self.list_ports()
        if not ports:
            print("✗ 未找到任何串口设备")
            return None

        print(f"找到 {len(ports)} 个串口设备:")
        for i, port in enumerate(ports):
            print(f"  [{i+1}] {port['device']} - {port['description']}")

        # 优先选择USB串口
        for port in ports:
            if 'USB' in port['description'].upper() or 'CH340' in port['description'].upper():
                print(f"✓ 自动选择: {port['device']}")
                return port['device']

        if ports:
            print(f"✓ 自动选择: {ports[0]['device']}")
            return ports[0]['device']
        return None

    def connect(self):
        """连接串口"""
        current_time = time.time()
        if current_time - self.last_connect_time < self.connect_interval:
            wait_time = self.connect_interval - (current_time - self.last_connect_time)
            print(f"连接过于频繁，等待 {wait_time:.1f} 秒...")
            time.sleep(wait_time)

        try:
            self.close()
            time.sleep(0.2)

            if self.port is None:
                self.port = self.auto_detect_port()
                if self.port is None:
                    print("✗ 无法找到可用的串口")
                    return False

            print(f"正在打开串口: {self.port} (波特率: {self.baudrate})")

            # 打开串口 - 使用文本协议的配置
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
                write_timeout=10.0,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )

            # 清空缓冲区
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()
            time.sleep(0.2)

            self.connected = True
            self.last_connect_time = time.time()

            print(f"✓ 串口连接成功！")
            print(f"  端口: {self.port}")
            print(f"  波特率: {self.baudrate}")
            print(f"  协议: ASCII文本命令")

            # 自动发送初始化命令
            time.sleep(0.5)
            self.initialize_device()

            return True

        except Exception as e:
            print(f"✗ 串口连接失败: {e}")
            self.connected = False
            return False

    def initialize_device(self):
        """初始化设备 - 发送START和HOME命令"""
        if not self.connected or self.initialized:
            return

        print("\n初始化设备...")

        # 发送 !START
        if self.send_text_command("!START"):
            print("✓ START命令已发送，等待5秒...")
            time.sleep(5)
        else:
            print("✗ START命令发送失败")
            return

        # 发送 !HOME
        if self.send_text_command("!HOME"):
            print("✓ HOME命令已发送，等待10秒...")
            time.sleep(10)
            self.initialized = True
            print("✓ 设备初始化完成！")
        else:
            print("✗ HOME命令发送失败")

    def send_text_command(self, command):
        """
        发送文本命令

        Args:
            command: 文本命令（如 "!START", "!HOME"）

        Returns:
            bool: 发送是否成功
        """
        if not self.connected or self.serial_conn is None:
            print("✗ 未连接，无法发送命令")
            return False

        with self.send_lock:
            try:
                # 确保命令以\r\n结尾
                if not command.endswith('\r\n'):
                    command = command + '\r\n'

                bytes_written = self.serial_conn.write(command.encode('utf-8'))
                self.serial_conn.flush()

                print(f"✓ 发送文本命令: {command.strip()} ({bytes_written} 字节)")
                return True

            except Exception as e:
                print(f"✗ 发送失败: {e}")
                return False

    def send_position(self, angles):
        """
        发送位置命令

        Args:
            angles: 6个关节角度列表 [J1, J2, J3, J4, J5, J6]

        Returns:
            bool: 发送是否成功
        """
        if not self.connected or not self.initialized:
            print("✗ 设备未初始化，无法发送位置")
            return False

        if len(angles) != 6:
            print(f"✗ 角度数量错误: 需要6个，收到{len(angles)}个")
            return False

        with self.send_lock:
            try:
                # 格式: &angle1,angle2,angle3,angle4,angle5,angle6,\n
                command = f"&{angles[0]},{angles[1]},{angles[2]},{angles[3]},{angles[4]},{angles[5]},\n"

                bytes_written = self.serial_conn.write(command.encode('utf-8'))
                self.serial_conn.flush()

                print(f"✓ 发送位置: {command.strip()} ({bytes_written} 字节)")

                # 等待1秒接收响应
                time.sleep(1.0)
                return True

            except Exception as e:
                print(f"✗ 发送位置失败: {e}")
                return False

    def send_message(self, *args, **kwargs):
        """
        兼容接口 - 将CAN协议调用转换为文本命令
        这是为了兼容现有的GUI代码
        """
        # 暂时只返回True，避免GUI报错
        # 实际的位置控制通过send_position实现
        return True

    def receive_messages(self):
        """接收消息线程"""
        print("✓ 接收线程启动 (文本模式)")

        while not self._stop_receive and self.connected:
            try:
                if self.serial_conn.in_waiting > 0:
                    # 读取一行文本
                    line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        print(f"收到: {line}")

                        # 调用回调函数
                        if self.callback:
                            self.callback(line)

                time.sleep(0.05)

            except Exception as e:
                if not self._stop_receive:
                    print(f"接收错误: {e}")
                    break

        print("接收线程停止")

    def start_receive_thread(self):
        """启动接收线程"""
        if self.connected and not self._stop_receive:
            self._stop_receive = False
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()

    def register_callback(self, callback):
        """注册数据接收回调函数"""
        self.callback = callback
        print(f"✓ 回调函数已注册")

    def unregister_callback(self):
        """取消注册回调函数"""
        self.callback = None
        print("回调函数已取消")

    def close(self):
        """关闭连接"""
        print("正在关闭连接...")
        self._stop_receive = True
        self.connected = False
        self.initialized = False

        if self.receive_thread:
            self.receive_thread.join(timeout=1.0)

        if self.serial_conn:
            try:
                self.serial_conn.close()
            except:
                pass
            self.serial_conn = None

        print("✓ 连接已关闭")
