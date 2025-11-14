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
        self.connect_interval = 0.5  # 减少最小连接间隔到0.5秒
        self.send_lock = threading.Lock()  # 添加发送锁
        self.last_receive_time = time.time()  # 最后接收数据的时间
        self.send_interval = 0.02  # 发送间隔20ms (对应115200波特率)

    def connect(self):
        """改进的连接方法"""
        # 检查连接间隔
        current_time = time.time()
        if current_time - self.last_connect_time < self.connect_interval:
            wait_time = self.connect_interval - (current_time - self.last_connect_time)
            print(f"连接过于频繁，等待 {wait_time:.1f} 秒...")
            time.sleep(wait_time)

        try:
            # 关闭旧连接
            self.close()
            time.sleep(0.2)  # 等待端口释放

            print(f"正在连接 {self.server_address}:{self.server_port}")

            # 创建新socket
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.client_socket.settimeout(5.0)  # 增加超时到5秒

            # 绑定本地端口（可选，让系统自动分配）
            # self.client_socket.bind(('0.0.0.0', 0))

            # 直接标记为连接（UDP是无连接协议）
            self.connected = True
            self.last_connect_time = time.time()
            self.last_receive_time = time.time()

            print(f"✓ UDP连接已建立")
            return True

        except Exception as e:
            print(f"✗ 连接失败: {e}")
            self.connected = False
            return False

    def send_message(self, id, cmd, body1, body2, msg_type):
        """发送消息 - 增加发送间隔控制和重试机制"""
        if not self.connected:
            print("✗ 未连接，无法发送消息")
            return False

        with self.send_lock:
            max_retries = 3  # 增加重试次数到3次
            retry_delays = [0.05, 0.1, 0.2]  # 递增的重试延迟

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

                    # 发送间隔控制
                    time.sleep(self.send_interval)
                    return True

                except socket.timeout:
                    print(f"发送超时 (尝试 {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delays[attempt])

                except Exception as e:
                    print(f"发送失败 (尝试 {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delays[attempt])

            # 所有重试都失败了，但不立即断开连接
            print(f"发送消息最终失败,但保持连接")
            return False

    def receive_messages(self):
        """接收消息线程"""
        print("✓ 接收线程启动")
        if not self.connected:
            return

        consecutive_timeouts = 0
        max_consecutive_timeouts = 10

        while not self._stop_receive:
            try:
                data, addr = self.client_socket.recvfrom(1024)
                if data:
                    consecutive_timeouts = 0  # 重置超时计数
                    self.last_receive_time = time.time()
                    hex_data = ' '.join(f'{b:02X}' for b in data)

                    if self.callback:
                        self.callback(hex_data)

            except socket.timeout:
                consecutive_timeouts += 1
                if consecutive_timeouts >= max_consecutive_timeouts:
                    # 长时间没有收到数据，但不断开连接
                    consecutive_timeouts = 0
                continue

            except Exception as e:
                if not self._stop_receive:
                    print(f"✗ 接收错误: {e}")
                    break

        print("接收线程停止")

    def start_receive_thread(self):
        """启动接收线程"""
        if self.connected and not self._stop_receive:
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            print("✓ 接收线程已启动")

    def register_callback(self, callback):
        """注册消息接收回调函数"""
        self.callback = callback
        print("✓ 回调函数已注册")

    def unregister_callback(self):
        """注销消息接收回调函数"""
        self.callback = None
        print("✓ 回调函数已注销")

    def is_healthy(self):
        """检查连接健康状态"""
        if not self.connected:
            return False
        # 检查是否长时间没有收到数据（超过30秒）
        time_since_last_receive = time.time() - self.last_receive_time
        return time_since_last_receive < 30.0

    def close(self):
        """关闭连接"""
        print("正在关闭连接...")
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

        print("✓ 连接已关闭")