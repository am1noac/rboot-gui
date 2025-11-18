#!/usr/bin/env python3
"""
快速测试 #GETJPOS 命令
"""

import serial
import time

port = "COM7"
baudrate = 9600

print("快速测试 #GETJPOS 命令\n")

try:
    ser = serial.Serial(port=port, baudrate=baudrate, timeout=2.0)
    print(f"✓ 已连接到 {port}")

    # 清空缓冲区
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    time.sleep(0.5)

    print("\n场景1: 直接发送 #GETJPOS (不使能)")
    print("-" * 40)
    ser.write("#GETJPOS\r\n".encode('utf-8'))
    ser.flush()
    time.sleep(1.0)

    if ser.in_waiting > 0:
        response = ser.readline().decode('utf-8', errors='ignore').strip()
        print(f"✓ 响应: {response}")
    else:
        print("✗ 无响应")

    time.sleep(1)

    print("\n场景2: 先发送 !START，再发送 #GETJPOS")
    print("-" * 40)

    # 发送 !START
    ser.reset_input_buffer()
    ser.write("!START\r\n".encode('utf-8'))
    ser.flush()
    print("已发送: !START")
    time.sleep(3.0)

    # 读取 !START 的响应
    if ser.in_waiting > 0:
        response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        print(f"!START 响应: {response}")

    # 发送 #GETJPOS
    ser.reset_input_buffer()
    ser.write("#GETJPOS\r\n".encode('utf-8'))
    ser.flush()
    print("已发送: #GETJPOS")
    time.sleep(1.0)

    if ser.in_waiting > 0:
        response = ser.readline().decode('utf-8', errors='ignore').strip()
        print(f"✓ #GETJPOS 响应: {response}")
    else:
        print("✗ 无响应")

    ser.close()
    print("\n测试完成")

except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n请将上面的输出发给我")
