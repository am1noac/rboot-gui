#!/usr/bin/env python3
"""
UDP端口扫描工具 - 用于查找正确的设备通信端口
发送实际的CAN协议消息并监测响应
"""
import socket
import struct
import time
import sys
from threading import Thread, Event

class PortScanner:
    def __init__(self, target_ip):
        self.target_ip = target_ip
        self.results = {}
        self.stop_event = Event()

    def create_test_message(self):
        """创建一个实际的CAN协议测试消息 - Get_Encoder_Estimates命令"""
        message = bytearray(12)
        message[0] = 0xbb  # 发送消息头
        message[1] = 1     # 电机ID 1
        message[2] = 9     # Get_Encoder_Estimates命令
        message[3:7] = struct.pack('<I', 0)
        message[7:11] = struct.pack('<I', 0)

        # 计算校验和
        checksum = 0
        for byte in message[3:7]:
            checksum ^= byte
        message[11] = checksum

        return bytes(message)

    def test_single_port(self, port, timeout=2.0):
        """测试单个端口"""
        result = {
            'port': port,
            'sent': False,
            'received': False,
            'error': None,
            'response_data': None,
            'error_code': None
        }

        try:
            # 创建socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(timeout)

            # 绑定本地端口
            sock.bind(('0.0.0.0', 0))
            local_port = sock.getsockname()[1]

            # Windows优化
            try:
                import platform
                if platform.system() == 'Windows':
                    import ctypes
                    SIO_UDP_CONNRESET = 0x9800000C
                    sock.ioctl(SIO_UDP_CONNRESET, False)
            except:
                pass

            # 发送测试消息
            message = self.create_test_message()
            sock.sendto(message, (self.target_ip, port))
            result['sent'] = True

            # 尝试接收响应
            try:
                data, addr = sock.recvfrom(1024)
                result['received'] = True
                result['response_data'] = ' '.join(f'{b:02X}' for b in data)
            except socket.timeout:
                result['error'] = 'timeout'
            except OSError as e:
                error_code = getattr(e, 'winerror', None) or getattr(e, 'errno', None)
                result['error'] = 'os_error'
                result['error_code'] = error_code

            sock.close()

        except Exception as e:
            result['error'] = str(e)

        return result

    def scan_ports(self, port_list, progress_callback=None):
        """扫描端口列表"""
        total = len(port_list)

        for i, port in enumerate(port_list):
            if self.stop_event.is_set():
                break

            if progress_callback:
                progress_callback(port, i + 1, total)

            result = self.test_single_port(port)
            self.results[port] = result

            # 短暂延迟，避免发送过快
            time.sleep(0.1)

        return self.results

    def print_results(self):
        """打印扫描结果"""
        print("\n" + "="*70)
        print("端口扫描结果")
        print("="*70)

        # 分类结果
        responded = []
        no_error = []
        timeout = []
        rejected = []
        other_error = []

        for port, result in sorted(self.results.items()):
            if result['received']:
                responded.append((port, result))
            elif result['error'] == 'timeout':
                timeout.append(port)
            elif result['error'] == 'os_error' and result['error_code'] in (10054, 10040):
                rejected.append((port, result['error_code']))
            elif result['error']:
                other_error.append((port, result['error']))
            else:
                no_error.append(port)

        # 打印响应的端口（最有希望）
        if responded:
            print("\n✅ 收到响应的端口（很可能是正确端口）：")
            for port, result in responded:
                print(f"  端口 {port}: {result['response_data']}")

        # 打印超时的端口（可能是正确端口，但设备响应慢）
        if timeout:
            print("\n⏱️  超时的端口（设备可能在监听但不响应此消息）：")
            for port in timeout:
                print(f"  端口 {port}")

        # 打印没有错误的端口（发送成功但无响应）
        if no_error:
            print("\n❓ 发送成功但无响应的端口：")
            for port in no_error:
                print(f"  端口 {port}")

        # 打印被拒绝的端口
        if rejected:
            print(f"\n❌ 被拒绝的端口（错误 10054/10040）：")
            # 只显示前几个，避免刷屏
            for port, error_code in rejected[:5]:
                print(f"  端口 {port} (错误码 {error_code})")
            if len(rejected) > 5:
                print(f"  ... 还有 {len(rejected) - 5} 个端口")

        # 打印其他错误
        if other_error:
            print("\n⚠️  其他错误：")
            for port, error in other_error[:5]:
                print(f"  端口 {port}: {error}")
            if len(other_error) > 5:
                print(f"  ... 还有 {len(other_error) - 5} 个端口")

        print("\n" + "="*70)

        # 给出建议
        if responded:
            print("\n💡 建议：使用收到响应的端口进行连接！")
        elif timeout:
            print("\n💡 建议：尝试超时的端口，可能需要增加超时时间或调整消息格式")
        elif no_error:
            print("\n💡 建议：尝试无错误的端口，设备可能需要特定的初始化序列")
        else:
            print("\n💡 建议：")
            print("  1. 检查设备IP地址是否正确")
            print("  2. 确认设备是否需要特殊初始化")
            print("  3. 查看设备文档确认通信协议")
            print("  4. 尝试使用Wireshark捕获设备与其他软件的通信")

def main():
    print("="*70)
    print("UDP端口扫描工具 - Rboot设备")
    print("="*70)

    # 默认IP
    target_ip = '192.168.0.4'

    # 允许命令行指定IP
    if len(sys.argv) > 1:
        target_ip = sys.argv[1]

    print(f"\n目标IP: {target_ip}")

    # 定义要扫描的端口范围
    # 优先扫描常用端口
    common_ports = [3333, 4444, 5000, 6000, 8080, 9000, 1883, 502, 2404]

    # 再扫描一些其他常见范围
    extended_ports = list(range(3000, 3010)) + list(range(4000, 4010)) + \
                     list(range(5000, 5010)) + list(range(6000, 6010)) + \
                     list(range(8000, 8010)) + list(range(9000, 9010)) + \
                     list(range(10000, 10010))

    # 合并并去重
    port_list = sorted(set(common_ports + extended_ports))

    print(f"扫描端口数: {len(port_list)}")
    print(f"端口范围: {min(port_list)} - {max(port_list)}")
    print("\n开始扫描...")

    scanner = PortScanner(target_ip)

    def progress(port, current, total):
        percent = (current / total) * 100
        print(f"[{current}/{total}] 测试端口 {port}... ({percent:.1f}%)", end='\r')

    try:
        scanner.scan_ports(port_list, progress_callback=progress)
        print("\n扫描完成！")
        scanner.print_results()
    except KeyboardInterrupt:
        print("\n\n扫描被用户中断")
        scanner.stop_event.set()
        scanner.print_results()

if __name__ == "__main__":
    main()
