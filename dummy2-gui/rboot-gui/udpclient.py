import socket
import threading
import time
import struct


class UDPClient:
    def __init__(self, server_address, server_port=3333):
        self.server_address = server_address
        self.server_port = server_port
        self.client_socket = None
        self.connected = False
        self._stop_receive = False
        self.receive_thread = None
        self.callback = None
        self.last_connect_time = 0
        self.connect_interval = 2.0  # 最小连接间隔

    def connect(self):
        """改进的连接方法"""
        # 检查连接间隔
        current_time = time.time()
        if current_time - self.last_connect_time < self.connect_interval:
            print("连接过于频繁，等待...")
            time.sleep(self.connect_interval)

        try:
            # 关闭旧连接
            self.close()

            # 创建新socket
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.client_socket.settimeout(3.0)

            print(f"尝试连接 {self.server_address}:{self.server_port}")

            # 不发送测试消息，直接标记为连接
            # 很多设备在收到不符合协议的消息时会拒绝连接
            self.connected = True
            self.last_connect_time = time.time()

            print("连接状态设置为就绪")
            return True

        except Exception as e:
            print(f"连接失败: {e}")
            self.connected = False
            return False

    def send_message(self, id, cmd, body1, body2, msg_type):
        """发送消息 - 增加重试机制"""
        if not self.connected:
            print("未连接，无法发送消息")
            return False

        max_retries = 2
        for attempt in range(max_retries):
            try:
                # 构建消息
                if msg_type == 0:  # short message
                    message = bytearray(12)
                    message[0] = 0xbb
                    message[1] = id
                    message[2] = cmd

                    # 填充数据
                    if len(body1) >= 4:
                        message[3:7] = body1[:4]
                    if len(body2) >= 4:
                        message[7:11] = body2[:4]

                    # 计算校验和
                    checksum = 0
                    for byte in body1[:4]:
                        checksum ^= byte
                    message[11] = checksum

                # 发送消息
                self.client_socket.sendto(message, (self.server_address, self.server_port))
                print(f"消息发送成功 (尝试 {attempt + 1})")
                return True

            except Exception as e:
                print(f"发送失败 (尝试 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.1)  # 短暂延迟后重试
                else:
                    # 最后一次尝试失败，标记为断开连接
                    self.connected = False
                    return False

    def receive_messages(self):
        """接收消息线程"""
        print("接收线程启动")
        if not self.connected:
            return

        while not self._stop_receive:
            try:
                data, addr = self.client_socket.recvfrom(1024)
                if data:
                    hex_data = ' '.join(f'{b:02X}' for b in data)
                    print(f"收到: {hex_data}")

                    if self.callback:
                        self.callback(hex_data)

            except socket.timeout:
                continue  # 超时正常
            except Exception as e:
                if not self._stop_receive:
                    print(f"接收错误: {e}")
                    break

        print("接收线程停止")

    def start_receive_thread(self):
        """启动接收线程"""
        if self.connected and not self._stop_receive:
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            print("接收线程已启动")

    def register_callback(self, callback):
        """注册回调函数并启动接收线程"""
        self.callback = callback
        self._stop_receive = False
        self.start_receive_thread()
        print("回调已注册，接收线程已启动")

    def unregister_callback(self):
        """注销回调函数并停止接收线程"""
        print("注销回调")
        self._stop_receive = True
        self.callback = None
        if self.receive_thread:
            self.receive_thread.join(timeout=1.0)
        print("回调已注销，接收线程已停止")

    def close(self):
        """关闭连接"""
        print("关闭连接")
        self._stop_receive = True
        self.connected = False

        if self.receive_thread:
            self.receive_thread.join(timeout=1.0)

        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None