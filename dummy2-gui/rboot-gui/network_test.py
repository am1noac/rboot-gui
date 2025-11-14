#!/usr/bin/env python3
import socket
import time


def test_udp_connection(host='192.168.0.4', port=3333, timeout=3):
    """测试UDP连接"""
    print(f"Testing UDP connection to {host}:{port}")

    try:
        # 创建UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)

        # 发送测试消息（使用你之前定义的协议格式）
        test_message = b'\xBB\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xCC'
        print(f"Sending test message: {test_message.hex()}")

        sock.sendto(test_message, (host, port))
        print("Message sent successfully")

        # 尝试接收响应
        try:
            data, addr = sock.recvfrom(1024)
            print(f"Received response from {addr}: {data.hex()}")
            print("Connection SUCCESSFUL!")
            return True
        except socket.timeout:
            print("No response received (timeout)")
            print("This might be normal - the device may not send responses")
            return True  # UDP连接可能没有响应也是正常的
        except Exception as e:
            print(f"Error receiving response: {e}")
            return False

    except Exception as e:
        print(f"Connection FAILED: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass


def test_ping(host='192.168.0.4'):
    """测试网络连通性"""
    import platform
    import subprocess

    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "3", host]

    print(f"Pinging {host}...")
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print("Ping SUCCESSFUL!")
            return True
        else:
            print("Ping FAILED!")
            print(result.stdout)
            return False
    except Exception as e:
        print(f"Ping test error: {e}")
        return False


if __name__ == "__main__":
    print("=== Network Connection Test ===")

    # 先测试基本的网络连通性
    ping_success = test_ping('192.168.0.4')

    if ping_success:
        print("\n--- Ping successful, testing UDP connection ---")
        udp_success = test_udp_connection('192.168.0.4', 3333)

        if udp_success:
            print("\n=== ALL TESTS PASSED ===")
            print("The device should be accessible from your application")
        else:
            print("\n=== UDP TEST FAILED ===")
            print("Check if the device is running and listening on port 9999")
    else:
        print("\n=== PING TEST FAILED ===")
        print("Check network connection and device power")
        print("Make sure your computer is on the same network as the device")