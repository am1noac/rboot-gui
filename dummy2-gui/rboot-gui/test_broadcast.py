#!/usr/bin/env python3
"""
测试UDP广播接收
用于检测设备是否通过广播方式发送CAN数据
"""
import socket
import time
import threading
import struct


def test_broadcast_receive(port=9999, duration=10):
    """
    测试接收UDP广播数据

    Args:
        port: 监听端口
        duration: 监听时长（秒）
    """
    print(f"\n{'='*60}")
    print(f"测试UDP广播接收")
    print(f"监听端口: {port}")
    print(f"监听时长: {duration}秒")
    print(f"{'='*60}\n")

    received_count = 0

    try:
        # 创建UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 允许接收广播
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # 绑定到所有接口的指定端口
        sock.bind(('', port))

        local_addr = sock.getsockname()
        print(f"✓ Socket绑定成功: 0.0.0.0:{local_addr[1]}")
        print(f"✓ 广播接收已启用")
        print(f"\n开始监听... (按Ctrl+C停止)\n")

        sock.settimeout(1.0)

        start_time = time.time()

        while (time.time() - start_time) < duration:
            try:
                data, addr = sock.recvfrom(1024)
                if data:
                    received_count += 1
                    hex_data = ' '.join(f'{b:02X}' for b in data)
                    timestamp = time.strftime('%H:%M:%S')

                    print(f"[{timestamp}] 收到来自 {addr}:")
                    print(f"  HEX: {hex_data}")
                    print(f"  长度: {len(data)} 字节")

                    # 尝试解析CAN消息
                    if len(data) == 12 and data[0] == 0xBB:
                        motor_id = data[1]
                        cmd_id = data[2]
                        body = data[3:11]
                        checksum = data[11]

                        print(f"  CAN解析:")
                        print(f"    电机ID: {motor_id}")
                        print(f"    命令ID: {cmd_id} (0x{cmd_id:02X})")

                        # 根据命令类型解析数据
                        if cmd_id == 0x09:  # Get_Encoder_Estimates
                            pos, vel = struct.unpack('<ff', body)
                            print(f"    位置: {pos:.6f}")
                            print(f"    速度: {vel:.6f}")
                        elif cmd_id == 0x01:  # Heartbeat
                            error, state, result, traj_done = struct.unpack('<IBBB', body[:7])
                            print(f"    错误码: {error}")
                            print(f"    状态: {state}")
                            print(f"    结果: {result}")

                    print()

            except socket.timeout:
                continue

        print(f"\n{'='*60}")
        print(f"监听完成")
        print(f"总共接收到 {received_count} 条消息")
        print(f"{'='*60}\n")

        return received_count > 0

    except PermissionError:
        print("\n❌ 权限错误: 需要管理员权限来绑定端口")
        print("   请以管理员身份运行此脚本")
        return False
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass


def test_any_port_receive(duration=10):
    """
    测试监听任意端口，看是否能收到设备的数据
    """
    print(f"\n{'='*60}")
    print(f"测试监听任意端口（让系统自动分配）")
    print(f"{'='*60}\n")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(('', 0))  # 让系统自动分配端口

        local_addr = sock.getsockname()
        print(f"✓ 监听端口: {local_addr[1]}")
        print(f"\n发送一个查询命令到设备，看是否有响应...")

        # 发送查询命令
        message = bytearray(12)
        message[0] = 0xBB
        message[1] = 0x01  # Motor 1
        message[2] = 0x09  # Get_Encoder_Estimates

        sock.sendto(message, ('192.168.0.88', 9999))
        hex_msg = ' '.join(f'{b:02X}' for b in message)
        print(f"发送: [{hex_msg}] -> 192.168.0.88:9999\n")

        sock.settimeout(5.0)

        try:
            data, addr = sock.recvfrom(1024)
            hex_data = ' '.join(f'{b:02X}' for b in data)
            print(f"✓ 收到响应来自 {addr}: {hex_data}")
            return True
        except socket.timeout:
            print("❌ 5秒内未收到响应")
            return False

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass


def send_commands_and_listen(target_host='192.168.0.88', target_port=9999, listen_port=None):
    """
    持续发送命令并监听响应

    Args:
        target_host: 目标设备IP
        target_port: 目标设备端口
        listen_port: 本地监听端口（None则自动分配）
    """
    print(f"\n{'='*60}")
    print(f"持续发送命令并监听")
    print(f"目标: {target_host}:{target_port}")
    if listen_port:
        print(f"本地端口: {listen_port}")
    else:
        print(f"本地端口: 自动分配")
    print(f"{'='*60}\n")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        if listen_port:
            sock.bind(('', listen_port))
        else:
            sock.bind(('', 0))

        local_addr = sock.getsockname()
        print(f"✓ 本地绑定: {local_addr}")

        sock.settimeout(0.5)

        received_any = False

        for i in range(20):  # 发送20次
            # 发送查询命令
            motor_id = (i % 2) + 1  # 交替查询电机1和2
            message = bytearray(12)
            message[0] = 0xBB
            message[1] = motor_id
            message[2] = 0x09  # Get_Encoder_Estimates

            sock.sendto(message, (target_host, target_port))
            print(f"[{i+1}/20] 发送查询命令到电机{motor_id}...", end=' ')

            # 尝试接收
            try:
                data, addr = sock.recvfrom(1024)
                hex_data = ' '.join(f'{b:02X}' for b in data)
                print(f"✓ 收到: {hex_data}")
                received_any = True
            except socket.timeout:
                print("(无响应)")

            time.sleep(0.5)

        print(f"\n{'='*60}")
        if received_any:
            print("✓ 接收到了响应数据！")
        else:
            print("❌ 未接收到任何响应")
        print(f"{'='*60}\n")

        return received_any

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass


if __name__ == "__main__":
    print("\n" + "="*60)
    print("UDP广播/多播接收测试")
    print("="*60)

    try:
        # 测试1: 监听9999端口的广播
        print("\n【测试1】监听端口9999（10秒）")
        test_broadcast_receive(port=9999, duration=10)

        # 测试2: 使用自动分配端口收发
        print("\n【测试2】自动端口测试")
        test_any_port_receive(duration=5)

        # 测试3: 持续发送并监听
        print("\n【测试3】持续发送命令并监听（10秒）")
        send_commands_and_listen()

        print("\n" + "="*60)
        print("所有测试完成")
        print("="*60 + "\n")

    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
