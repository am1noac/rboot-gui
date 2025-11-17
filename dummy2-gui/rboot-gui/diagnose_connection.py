#!/usr/bin/env python3
"""
UDP连接诊断工具
用于诊断rboot-gui与电机控制器之间的UDP通信问题
"""
import socket
import time
import struct
import threading


def test_udp_echo(host='192.168.0.88', port=9999, timeout=5):
    """测试UDP连接并尝试发送CAN命令"""
    print(f"\n{'='*60}")
    print(f"测试UDP连接: {host}:{port}")
    print(f"{'='*60}\n")

    try:
        # 创建UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', 0))  # 绑定到任意本地端口
        local_port = sock.getsockname()[1]
        print(f"✓ Socket创建成功")
        print(f"  本地绑定端口: {local_port}")

        sock.settimeout(timeout)

        # 启动接收线程
        received_data = []
        stop_flag = threading.Event()

        def receive_thread():
            while not stop_flag.is_set():
                try:
                    data, addr = sock.recvfrom(1024)
                    hex_data = ' '.join(f'{b:02X}' for b in data)
                    received_data.append((addr, hex_data, time.time()))
                    print(f"\n✓ 收到来自 {addr} 的数据: {hex_data}")
                except socket.timeout:
                    continue
                except Exception as e:
                    if not stop_flag.is_set():
                        print(f"\n接收错误: {e}")
                    break

        receiver = threading.Thread(target=receive_thread, daemon=True)
        receiver.start()
        print(f"✓ 接收线程已启动\n")

        # 测试1: 发送Get_Encoder_Estimates (CMD 9) 到电机1
        print("测试1: 查询电机1位置 (Get_Encoder_Estimates)")
        message = bytearray(12)
        message[0] = 0xBB  # Header
        message[1] = 0x01  # Motor ID = 1
        message[2] = 0x09  # CMD = Get_Encoder_Estimates
        message[11] = 0x00  # Checksum

        hex_msg = ' '.join(f'{b:02X}' for b in message)
        print(f"  发送: [{hex_msg}]")
        sock.sendto(message, (host, port))
        print(f"  ✓ 发送成功")
        time.sleep(2)

        # 测试2: 发送Heartbeat请求
        print("\n测试2: 发送Heartbeat请求到电机1")
        message[2] = 0x01  # CMD = Heartbeat
        hex_msg = ' '.join(f'{b:02X}' for b in message)
        print(f"  发送: [{hex_msg}]")
        sock.sendto(message, (host, port))
        print(f"  ✓ 发送成功")
        time.sleep(2)

        # 测试3: 查询电机2
        print("\n测试3: 查询电机2位置")
        message[1] = 0x02  # Motor ID = 2
        message[2] = 0x09  # CMD = Get_Encoder_Estimates
        hex_msg = ' '.join(f'{b:02X}' for b in message)
        print(f"  发送: [{hex_msg}]")
        sock.sendto(message, (host, port))
        print(f"  ✓ 发送成功")
        time.sleep(2)

        # 停止接收线程
        stop_flag.set()
        receiver.join(timeout=1)

        # 总结
        print(f"\n{'='*60}")
        print("测试结果:")
        print(f"{'='*60}")
        print(f"发送的命令数: 3")
        print(f"收到的响应数: {len(received_data)}")

        if received_data:
            print("\n✓ 成功接收到数据！")
            print("\n详细信息:")
            for addr, hex_data, timestamp in received_data:
                print(f"  时间: {time.strftime('%H:%M:%S', time.localtime(timestamp))}")
                print(f"  来源: {addr}")
                print(f"  数据: {hex_data}")
            return True
        else:
            print("\n❌ 未收到任何响应数据")
            print("\n可能的原因:")
            print("  1. 设备未配置为UDP响应模式")
            print("  2. 设备的IP地址或端口不正确")
            print("  3. 防火墙阻止了UDP通信")
            print("  4. 设备需要先发送特殊的初始化命令")
            print("  5. UDP-CAN转换器配置问题")
            print("\n建议检查:")
            print("  - 确认设备IP: 192.168.0.88")
            print("  - 确认设备端口: 9999")
            print("  - 检查Windows防火墙设置")
            print("  - 查看设备配置文档")
            return False

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass


def test_network_connectivity(host='192.168.0.88'):
    """测试基本网络连通性"""
    import platform
    import subprocess

    print(f"\n{'='*60}")
    print(f"测试网络连通性: {host}")
    print(f"{'='*60}\n")

    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "3", host]

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ Ping成功！设备在线")
            return True
        else:
            print("❌ Ping失败！设备可能离线或IP地址错误")
            print(result.stdout)
            return False
    except subprocess.TimeoutExpired:
        print("❌ Ping超时")
        return False
    except Exception as e:
        print(f"❌ Ping测试错误: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Rboot-GUI UDP连接诊断工具")
    print("="*60)

    # 设备配置（根据你的实际情况修改）
    DEVICE_IP = '192.168.0.88'
    DEVICE_PORT = 9999

    print(f"\n目标设备: {DEVICE_IP}:{DEVICE_PORT}")
    print("按 Ctrl+C 可以随时停止测试\n")

    try:
        # 步骤1: 测试网络连通性
        ping_ok = test_network_connectivity(DEVICE_IP)

        if not ping_ok:
            print("\n⚠️  警告: Ping失败，但继续测试UDP（某些设备可能禁用了ICMP）")

        # 步骤2: 测试UDP通信
        udp_ok = test_udp_echo(DEVICE_IP, DEVICE_PORT)

        # 最终结论
        print(f"\n{'='*60}")
        print("最终诊断结果:")
        print(f"{'='*60}")

        if udp_ok:
            print("✓ UDP通信正常！")
            print("  你的程序应该能够接收到电机数据")
        else:
            print("❌ UDP通信异常")
            print("  需要检查设备配置或网络设置")

    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n\n未预期的错误: {e}")
