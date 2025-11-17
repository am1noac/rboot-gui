#!/usr/bin/env python3
"""
UDP端口测试工具
测试Dummy v2在哪个端口响应
"""

import socket
import time
import sys

def test_udp_port(host, port, timeout=2):
    """测试指定UDP端口是否响应CAN命令"""
    print(f"\n{'='*60}")
    print(f"测试 {host}:{port}")
    print(f"{'='*60}")

    try:
        # 创建UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)

        # 绑定到本地端口
        sock.bind(('', 0))
        local_port = sock.getsockname()[1]
        print(f"本地端口: {local_port}")

        # 发送CAN查询命令（查询电机1）
        can_cmd = bytearray([0xBB, 0x01, 0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        hex_str = ' '.join(f'{b:02X}' for b in can_cmd)

        print(f"发送命令: {hex_str}")
        sock.sendto(can_cmd, (host, port))

        # 等待响应
        print(f"等待响应（超时{timeout}秒）...")

        try:
            data, addr = sock.recvfrom(1024)
            if data:
                hex_resp = ' '.join(f'{b:02X}' for b in data[:min(32, len(data))])
                print(f"✅ 收到响应: {len(data)} 字节")
                print(f"  来自: {addr}")
                print(f"  数据: {hex_resp}")
                sock.close()
                return True
        except socket.timeout:
            print(f"✗ 超时无响应")
            sock.close()
            return False

    except Exception as e:
        print(f"✗ 错误: {e}")
        return False

def main():
    print("=" * 60)
    print("Dummy v2 UDP端口扫描工具")
    print("=" * 60)

    host = '192.168.0.88'

    # 测试常用端口
    ports = [
        (9999, "原始main.py配置"),
        (3333, "rboot-gui默认配置"),
        (8888, "常用端口1"),
        (5555, "常用端口2"),
        (6666, "常用端口3"),
    ]

    print(f"\n目标设备: {host}")
    print(f"测试CAN协议命令: BB 01 09 ... (查询电机1)\n")

    results = {}

    for port, description in ports:
        result = test_udp_port(host, port, timeout=2)
        results[port] = result

        if result:
            print(f"\n" + "="*60)
            print(f"✅ 找到响应端口！")
            print(f"  IP: {host}")
            print(f"  端口: {port}")
            print(f"  描述: {description}")
            print(f"="*60)
            print(f"\n请在main.py中使用此配置:")
            print(f"  UDPClient('{host}', {port})")
            break

        time.sleep(0.5)  # 避免发送过快

    # 总结
    print(f"\n" + "="*60)
    print("测试总结:")
    print(f"="*60)

    for port, description in ports:
        if port in results:
            status = "✓ 响应" if results[port] else "✗ 无响应"
            print(f"  {status}  {port:5d} - {description}")

    if not any(results.values()):
        print(f"\n⚠ 所有端口都无响应\n")
        print(f"可能原因:")
        print(f"  1. 设备上的UDP服务未启动")
        print(f"  2. 防火墙阻止了UDP通信")
        print(f"  3. 设备IP地址不正确")
        print(f"  4. 设备需要特殊的初始化命令")
        print(f"\n建议:")
        print(f"  1. 检查设备是否正常开机")
        print(f"  2. 临时关闭Windows防火墙测试")
        print(f"  3. 查看设备说明书确认正确的IP和端口")
        print(f"  4. 检查设备上是否有网络指示灯闪烁")

if __name__ == "__main__":
    main()
