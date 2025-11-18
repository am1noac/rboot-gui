#!/usr/bin/env python3
"""
设备诊断脚本 - 测试设备是否响应各种命令
"""

import serial
import time

port = "COM7"
baudrate = 9600

print("=" * 60)
print("设备诊断工具")
print("=" * 60)

try:
    print(f"\n1. 正在打开串口 {port}...")
    ser = serial.Serial(port=port, baudrate=baudrate, timeout=2.0)
    print("✓ 串口已打开")

    # 清空缓冲区
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    time.sleep(0.5)

    print("\n2. 测试命令响应...")

    # 测试命令列表
    test_commands = [
        ("#GETJPOS\r\n", "查询位置"),
        ("!START\r\n", "使能电机"),
        ("!HOME\r\n", "回零"),
        ("#HELLO\r\n", "测试通信"),
    ]

    for cmd, desc in test_commands:
        print(f"\n{'=' * 60}")
        print(f"测试命令: {cmd.strip()} ({desc})")
        print(f"{'=' * 60}")

        # 清空缓冲区
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.2)

        # 发送命令
        print(f"发送: {cmd.strip()}")
        ser.write(cmd.encode('utf-8'))
        ser.flush()

        # 等待响应
        print("等待响应...")
        time.sleep(1.5)

        # 检查缓冲区
        waiting = ser.in_waiting
        print(f"缓冲区字节数: {waiting}")

        if waiting > 0:
            # 读取所有可用数据
            response = ser.read(waiting).decode('utf-8', errors='ignore')
            print(f"✓ 收到响应: '{response}'")
        else:
            print("✗ 无响应")

        time.sleep(0.5)

    print("\n" + "=" * 60)
    print("3. 持续监听5秒（看设备是否主动发送数据）...")
    print("=" * 60)

    ser.reset_input_buffer()
    start_time = time.time()

    while time.time() - start_time < 5:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            print(f"接收到数据: '{data}'")
        time.sleep(0.1)

    print("监听结束")

    ser.close()
    print("\n✓ 诊断完成")

except Exception as e:
    print(f"\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()
