import serial
import threading
import time
import struct


class SerialClient:
    def __init__(self, port='COM7', baudrate=115200, write_timeout=None):
        """
        初始化串口客户端
        :param port: 串口端口号,默认COM7
        :param baudrate: 波特率,默认115200
        :param write_timeout: 写超时时间(秒),None表示无限等待
        """
        self.port = port
        self.baudrate = baudrate
        self.write_timeout = write_timeout  # None = 无限等待，可能更适合某些设备
        self.serial_port = None
        self.connected = False
        self._stop_receive = False
        self.receive_thread = None
        self.callback = None
        self.last_connect_time = 0
        self.connect_interval = 2.0  # 最小连接间隔

    def connect(self):
        """连接串口"""
        # 检查连接间隔
        current_time = time.time()
        if current_time - self.last_connect_time < self.connect_interval:
            print("连接过于频繁,等待...")
            time.sleep(self.connect_interval)

        try:
            # 关闭旧连接
            self.close()

            print(f"尝试连接串口 {self.port},波特率 {self.baudrate}")

            # 创建串口连接
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5,  # 读取超时
                write_timeout=self.write_timeout,  # 写入超时(None=无限等待)
                xonxoff=False,  # 禁用软件流控
                rtscts=False,  # 禁用硬件流控
                dsrdtr=False  # 禁用DTR/DSR流控
            )

            if self.serial_port.is_open:
                # 设置DTR和RTS信号
                self.serial_port.dtr = True
                self.serial_port.rts = True
                time.sleep(0.1)  # 等待信号稳定

                # 清空缓冲区
                self.serial_port.reset_input_buffer()
                self.serial_port.reset_output_buffer()

                self.connected = True
                self._stop_receive = False
                self.last_connect_time = time.time()
                print(f"成功连接到 {self.port}")
                print(f"DTR: {self.serial_port.dtr}, RTS: {self.serial_port.rts}")
                return True
            else:
                print("无法打开串口")
                self.connected = False
                return False

        except serial.SerialException as e:
            print(f"串口连接失败: {e}")
            self.connected = False
            return False
        except Exception as e:
            print(f"连接失败: {e}")
            self.connected = False
            return False

    def send_message(self, id, cmd, body1, body2, msg_type):
        """
        发送消息 - 增加重试机制
        :param id: 设备ID
        :param cmd: 命令
        :param body1: 消息体1 (bytes)
        :param body2: 消息体2 (bytes)
        :param msg_type: 消息类型
        """
        if not self.connected or not self.serial_port or not self.serial_port.is_open:
            print("未连接,无法发送消息")
            return False

        max_retries = 3
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
                bytes_written = self.serial_port.write(message)
                self.serial_port.flush()  # 确保数据发送完成

                # 打印调试信息(减少日志输出)
                if attempt > 0:  # 只在重试时打印
                    hex_msg = ' '.join(f'{b:02X}' for b in message)
                    print(f"发送: {hex_msg} (尝试 {attempt + 1})")
                return True

            except serial.SerialTimeoutException:
                print(f"发送超时 (尝试 {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(0.05)  # 短暂延迟
                    # 不要断开连接，继续重试
                else:
                    print(f"发送消息最终失败,但保持连接")
                    # 不断开连接，因为串口可能只是暂时繁忙
                    return False
            except Exception as e:
                print(f"发送失败 (尝试 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.05)
                else:
                    # 只有在严重错误时才断开连接
                    if "closed" in str(e).lower() or "not open" in str(e).lower():
                        print(f"串口已关闭，断开连接")
                        self.connected = False
                    return False

        return False

    def receive_messages(self):
        """接收消息线程 - 改进的数据接收逻辑"""
        print("接收线程启动")
        if not self.connected:
            return

        buffer = bytearray()  # 用于累积接收的数据
        message_length = 12  # 消息长度

        while not self._stop_receive:
            try:
                if self.serial_port and self.serial_port.is_open and self.serial_port.in_waiting > 0:
                    # 读取可用数据并添加到缓冲区
                    chunk = self.serial_port.read(self.serial_port.in_waiting)
                    buffer.extend(chunk)

                    # 查找消息头 0xbb
                    while len(buffer) >= message_length:
                        # 查找消息头
                        start_idx = buffer.find(0xbb)

                        if start_idx == -1:
                            # 没有找到消息头,清空缓冲区
                            buffer.clear()
                            break

                        # 移除消息头之前的数据
                        if start_idx > 0:
                            buffer = buffer[start_idx:]

                        # 检查是否有完整的消息
                        if len(buffer) >= message_length:
                            # 提取一个完整消息
                            message = buffer[:message_length]
                            buffer = buffer[message_length:]

                            # 将消息转换为十六进制字符串
                            hex_data = ' '.join(f'{b:02X}' for b in message)
                            print(f"收到: {hex_data}")

                            # 调用回调函数
                            if self.callback:
                                self.callback(hex_data)
                        else:
                            # 消息不完整,等待更多数据
                            break
                else:
                    time.sleep(0.005)  # 减少CPU占用

            except serial.SerialException as e:
                if not self._stop_receive:
                    print(f"串口读取错误: {e}")
                    self.connected = False
                    break
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
            print("接收线程已启动")

    def register_callback(self, callback):
        """注册数据接收回调函数"""
        self.callback = callback
        print("回调函数已注册")

    def unregister_callback(self):
        """取消注册回调函数"""
        self.callback = None
        print("回调函数已取消")

    def close(self):
        """关闭串口连接"""
        print("关闭串口连接")
        self._stop_receive = True
        self.connected = False

        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)

        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
                print("串口已关闭")
            except Exception as e:
                print(f"关闭串口时出错: {e}")
            finally:
                self.serial_port = None
