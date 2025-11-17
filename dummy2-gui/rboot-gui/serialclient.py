#!/usr/bin/env python3
"""
串口通信客户端
用于通过USB串口(如COM7)与机械臂设备通信
波特率: 115200
"""

import serial
import serial.tools.list_ports
import threading
import time
import struct


class SerialClient:
    def __init__(self, port=None, baudrate=115200):
        """
        初始化串口客户端

        Args:
            port: 串口名称（如'COM7'或'/dev/ttyUSB0'），None则自动检测
            baudrate: 波特率，默认115200
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.connected = False
        self._stop_receive = False
        self.receive_thread = None
        self.callback = None
        self.last_connect_time = 0
        self.connect_interval = 0.5  # 最小连接间隔0.5秒
        self.send_lock = threading.Lock()  # 发送锁
        self.last_receive_time = time.time()
        self.send_interval = 0.02  # 发送间隔20ms (适配115200波特率)

    def list_ports(self):
        """列出所有可用的串口"""
        ports = serial.tools.list_ports.comports()
        available_ports = []
        for port in ports:
            available_ports.append({
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid
            })
        return available_ports

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

        # 如果没有USB串口，返回第一个
        if ports:
            print(f"✓ 自动选择: {ports[0]['device']}")
            return ports[0]['device']

        return None

    def connect(self):
        """连接串口"""
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

            # 自动检测串口
            if self.port is None:
                self.port = self.auto_detect_port()
                if self.port is None:
                    print("✗ 无法找到可用的串口")
                    return False

            print(f"正在打开串口: {self.port} (波特率: {self.baudrate})")
            print("调用serial.open()...")

            # 打开串口
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,  # 读取超时1秒
                write_timeout=2.0,  # 写入超时2秒
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )

            # 清空缓冲区
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()
            time.sleep(0.1)

            self.connected = True
            self.last_connect_time = time.time()
            self.last_receive_time = time.time()

            print(f"✓ 串口连接成功！")
            print(f"  端口: {self.port}")
            print(f"  波特率: {self.baudrate}")
            print(f"  设置发送间隔: {int(self.send_interval * 1000)}ms (波特率: {self.baudrate})")
            print(f"  理论最大发送速率: {1.0 / self.send_interval:.1f}条/秒")

            return True

        except serial.SerialException as e:
            print(f"✗ serial.open()超时（5秒）")
            print(f"  详细错误: {e}")
            print(f"\n可能原因:")
            print(f"  - 端口被其他程序占用")
            print(f"  - 端口状态异常")
            print(f"  - 需要重新插拔USB线")
            print(f"\n解决方法:")
            print(f"  - 运行: python reset_port.py")
            print(f"  - 或重新插拔USB线")
            self.connected = False
            return False
        except Exception as e:
            print(f"✗ 串口连接失败: {e}")
            self.connected = False
            return False

    def send_message(self, id, cmd, body1, body2, msg_type):
        """
        发送CAN消息

        Args:
            id: CAN节点ID
            cmd: 命令类型
            body1: 数据体1 (4字节)
            body2: 数据体2 (4字节)
            msg_type: 消息类型 (0=short)

        Returns:
            bool: 发送是否成功
        """
        if not self.connected or self.serial_conn is None:
            print("✗ 未连接，无法发送消息")
            return False

        with self.send_lock:
            max_retries = 3
            retry_delays = [0.05, 0.1, 0.2]

            for attempt in range(max_retries):
                try:
                    # 构建消息 (与UDP版本相同的格式)
                    if msg_type == 0:  # short message
                        message = bytearray(12)
                        message[0] = 0xbb  # 消息头
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
                    bytes_written = self.serial_conn.write(message)
                    self.serial_conn.flush()  # 确保数据发送出去

                    if bytes_written != len(message):
                        raise serial.SerialException(f"只发送了 {bytes_written}/{len(message)} 字节")

                    # 发送间隔控制
                    time.sleep(self.send_interval)
                    return True

                except serial.SerialTimeoutException:
                    print(f"发送超时 (尝试 {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delays[attempt])

                except serial.SerialException as e:
                    print(f"串口错误 (尝试 {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delays[attempt])
                    else:
                        # 串口可能断开，标记为未连接
                        self.connected = False

                except Exception as e:
                    print(f"发送失败 (尝试 {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delays[attempt])

            print(f"发送消息最终失败,但保持连接")
            return False

    def receive_messages(self):
        """接收消息线程"""
        print("✓ 接收线程启动")
        if not self.connected or self.serial_conn is None:
            return

        consecutive_timeouts = 0
        max_consecutive_timeouts = 10
        buffer = bytearray()

        while not self._stop_receive:
            try:
                # 读取可用数据
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.read(self.serial_conn.in_waiting)
                    if data:
                        buffer.extend(data)
                        consecutive_timeouts = 0
                        self.last_receive_time = time.time()

                        # 解析完整的消息 (12字节)
                        while len(buffer) >= 12:
                            # 查找消息头 (0xBB)
                            header_index = buffer.find(0xBB)
                            if header_index == -1:
                                buffer.clear()
                                break

                            # 移除头部之前的数据
                            if header_index > 0:
                                buffer = buffer[header_index:]

                            # 检查是否有完整的消息
                            if len(buffer) >= 12:
                                message = buffer[:12]
                                buffer = buffer[12:]

                                # 转换为十六进制字符串
                                hex_data = ' '.join(f'{b:02X}' for b in message)

                                if self.callback:
                                    self.callback(hex_data)
                            else:
                                break
                else:
                    # 没有数据可读，短暂休眠
                    time.sleep(0.01)
                    consecutive_timeouts += 1
                    if consecutive_timeouts >= max_consecutive_timeouts:
                        consecutive_timeouts = 0

            except serial.SerialException as e:
                if not self._stop_receive:
                    print(f"✗ 串口接收错误: {e}")
                    self.connected = False
                    break

            except Exception as e:
                if not self._stop_receive:
                    print(f"✗ 接收错误: {e}")
                    break

        print("接收线程停止")

    def start_receive_thread(self):
        """启动接收线程"""
        if self.connected and not self._stop_receive:
            self._stop_receive = False
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
        if not self.connected or self.serial_conn is None:
            return False

        # 检查串口是否仍然打开
        if not self.serial_conn.is_open:
            return False

        # 检查是否长时间没有收到数据（超过30秒）
        time_since_last_receive = time.time() - self.last_receive_time
        return time_since_last_receive < 30.0

    def close(self):
        """关闭串口连接"""
        print("正在关闭连接...")
        self._stop_receive = True
        self.connected = False

        if self.receive_thread:
            self.receive_thread.join(timeout=1.0)

        if self.serial_conn:
            try:
                if self.serial_conn.is_open:
                    self.serial_conn.close()
            except Exception as e:
                print(f"关闭串口时出错: {e}")
            finally:
                self.serial_conn = None

        print("✓ 连接已关闭")


# 测试代码
if __name__ == "__main__":
    print("串口客户端测试")
    print("="*60)

    # 创建客户端（自动检测端口）
    client = SerialClient(port=None, baudrate=115200)

    # 或指定端口
    # client = SerialClient(port='COM7', baudrate=115200)

    if client.connect():
        print("\n连接成功！开始测试...")
        client.start_receive_thread()

        # 测试发送消息
        time.sleep(1)

        # 发送查询命令（查询电机1的位置）
        print("\n发送测试命令...")
        import can_data
        client.send_message(
            1,  # 电机ID
            can_data.command_id['Get_Encoder_Estimates'],
            struct.pack('<I', 0),
            struct.pack('<I', 0),
            0  # short message
        )

        # 等待响应
        time.sleep(2)

        client.close()
    else:
        print("\n连接失败！")
