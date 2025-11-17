#!/usr/bin/env python3
"""
UDP监听测试工具
用于诊断设备是否在发送UDP数据
"""

import socket
import time
from datetime import datetime

def listen_udp(ip='0.0.0.0', port=9999, timeout=60):
    """
    监听UDP端口，打印收到的所有数据

    Args:
        ip: 监听IP (0.0.0.0表示监听所有网卡)
        port: 监听端口
        timeout: 超时时间（秒）
    """
    print("="*60)
    print("UDP 监听测试工具")
    print("="*60)
    print(f"监听地址: {ip}")
    print(f"监听端口: {port}")
    print(f"测试时长: {timeout}秒")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("\n等待接收数据...")
    print("(如果设备在发送数据，应该会在下方显示)\n")

    # 创建UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ip, port))
    sock.settimeout(1.0)

    receive_count = 0
    timeout_count = 0
    start_time = time.time()

    try:
        while time.time() - start_time < timeout:
            try:
                data, addr = sock.recvfrom(1024)
                if data:
                    receive_count += 1
                    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    hex_data = ' '.join(f'{b:02X}' for b in data)

                    print(f"\n[{timestamp}] 收到数据 #{receive_count}")
                    print(f"  来源地址: {addr[0]}:{addr[1]}")
                    print(f"  数据长度: {len(data)} 字节")
                    print(f"  HEX格式: {hex_data}")

                    # 尝试解析为字符串（如果可能）
                    try:
                        ascii_data = data.decode('ascii', errors='ignore')
                        if ascii_data.isprintable():
                            print(f"  ASCII: {ascii_data}")
                    except:
                        pass

            except socket.timeout:
                timeout_count += 1
                if timeout_count % 10 == 0:
                    elapsed = int(time.time() - start_time)
                    remaining = timeout - elapsed
                    print(f"[{elapsed}秒] 等待中... (已接收: {receive_count} 条, 剩余: {remaining}秒)")
                continue

    except KeyboardInterrupt:
        print("\n\n用户中止测试")

    finally:
        sock.close()

    print("\n" + "="*60)
    print("测试结束")
    print("="*60)
    print(f"总接收数据: {receive_count} 条")
    print(f"测试时长: {int(time.time() - start_time)} 秒")

    if receive_count == 0:
        print("\n⚠️  未收到任何数据！")
        print("\n可能原因：")
        print("  1. 设备未开机或未连接到网络")
        print("  2. 设备IP地址不正确")
        print("  3. 设备使用其他端口发送数据")
        print("  4. 设备需要先接收特定命令才开始发送")
        print("  5. 防火墙阻止了UDP数据包")
    else:
        print("\n✓ 成功接收到数据！")
        print("设备正在发送UDP数据包")

    print("="*60)


if __name__ == "__main__":
    import sys

    # 默认参数
    listen_ip = '0.0.0.0'
    listen_port = 9999
    test_timeout = 60

    # 命令行参数
    if len(sys.argv) > 1:
        listen_port = int(sys.argv[1])
    if len(sys.argv) > 2:
        test_timeout = int(sys.argv[2])

    print("\n提示: 运行前请确保：")
    print("  1. 设备已开机并连接到网络")
    print("  2. 已知设备的IP地址")
    print("  3. Windows防火墙允许Python接收UDP\n")

    input("按回车键开始测试...")

    listen_udp(listen_ip, listen_port, test_timeout)
