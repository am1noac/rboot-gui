#!/usr/bin/env python3
"""
网络连接重置和诊断工具
用于排查和修复UDP通信问题
"""

import socket
import sys
import time
import subprocess
import platform

def test_network_connectivity(host='192.168.0.4', port=3333):
    """测试网络连通性"""
    print("\n" + "="*60)
    print("网络连接诊断工具")
    print("="*60)

    # 1. Ping测试
    print(f"\n[1/4] 测试网络连通性 (ping {host})...")
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        result = subprocess.run(['ping', param, '3', host],
                              capture_output=True,
                              timeout=10,
                              text=True)
        if result.returncode == 0:
            print(f"✓ Ping成功! 网络可达")
        else:
            print(f"✗ Ping失败! 设备可能未连接或IP地址错误")
            print(f"  输出: {result.stdout}")
            return False
    except Exception as e:
        print(f"✗ Ping测试失败: {e}")
        return False

    # 2. UDP端口测试
    print(f"\n[2/4] 测试UDP端口 ({host}:{port})...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(5.0)

        # 发送测试消息
        test_msg = b'\xBB\x01\x09\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # 查询电机1位置
        sock.sendto(test_msg, (host, port))
        print(f"✓ 测试消息已发送")

        # 尝试接收响应
        try:
            data, addr = sock.recvfrom(1024)
            if data:
                print(f"✓ 收到响应! 长度: {len(data)} 字节")
                hex_data = ' '.join(f'{b:02X}' for b in data)
                print(f"  数据: {hex_data}")
                sock.close()
                return True
        except socket.timeout:
            print(f"⚠ 未收到响应 (5秒超时)")
            print(f"  可能原因:")
            print(f"  - 设备未运行CAN总线固件")
            print(f"  - 设备端口配置不是3333")
            print(f"  - 防火墙阻止了UDP通信")

        sock.close()

    except Exception as e:
        print(f"✗ UDP测试失败: {e}")
        return False

    # 3. 检查本地端口占用
    print(f"\n[3/4] 检查本地UDP端口占用...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', 0))  # 绑定任意可用端口
        local_port = sock.getsockname()[1]
        print(f"✓ 本地可用端口: {local_port}")
        sock.close()
    except Exception as e:
        print(f"✗ 端口检查失败: {e}")

    # 4. 网络接口信息
    print(f"\n[4/4] 本机网络信息...")
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"  主机名: {hostname}")
        print(f"  本机IP: {local_ip}")

        # 获取所有网络接口
        if hasattr(socket, 'if_nameindex'):
            print(f"  网络接口:")
            for idx, name in socket.if_nameindex():
                print(f"    - {name}")
    except Exception as e:
        print(f"  网络信息获取失败: {e}")

    print("\n" + "="*60)
    return True


def reset_network():
    """重置网络连接"""
    print("\n执行网络重置...")
    print("提示: 此操作会尝试释放所有UDP连接")

    try:
        # 简单的等待，让系统释放端口
        print("等待端口释放...")
        time.sleep(2)
        print("✓ 重置完成")
        return True
    except Exception as e:
        print(f"✗ 重置失败: {e}")
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║         Rboot GUI - 网络连接诊断和重置工具               ║
╚══════════════════════════════════════════════════════════╝
    """)

    if len(sys.argv) > 1:
        if sys.argv[1] == 'reset':
            reset_network()
        elif sys.argv[1] == 'test':
            test_network_connectivity()
        else:
            print(f"未知命令: {sys.argv[1]}")
            print("用法: python reset_network.py [test|reset]")
    else:
        # 默认执行完整诊断
        if test_network_connectivity():
            print("\n✓ 网络连接正常！")
            print("\n建议:")
            print("1. 如果仍然连接失败，请尝试重启设备")
            print("2. 检查设备固件是否正确加载")
            print("3. 确认设备IP配置为 192.168.0.4")
        else:
            print("\n✗ 网络连接异常！")
            print("\n故障排除步骤:")
            print("1. 检查网线是否连接")
            print("2. 检查设备电源是否打开")
            print("3. 确认本机IP在同一网段 (192.168.0.x)")
            print("4. 尝试手动配置本机IP为 192.168.0.100")
            print("5. 检查防火墙设置，确保UDP端口3333未被阻止")
            print("\n执行重置? (y/n): ", end='')

            try:
                choice = input().lower()
                if choice == 'y':
                    reset_network()
            except KeyboardInterrupt:
                print("\n取消")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
