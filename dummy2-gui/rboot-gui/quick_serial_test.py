#!/usr/bin/env python3
"""
快速串口测试工具 - 诊断COM7连接问题
"""

import serial
import serial.tools.list_ports
import time
import sys

def test_quick_connection(port='COM7', baudrate=9600):
    """快速测试串口连接"""
    print(f"=" * 60)
    print(f"快速串口测试: {port} @ {baudrate}")
    print(f"=" * 60)

    # 1. 检查端口是否存在
    print("\n步骤 1: 检查端口是否存在...")
    ports = [p.device for p in serial.tools.list_ports.comports()]
    print(f"系统中的串口: {', '.join(ports)}")

    if port not in ports:
        print(f"✗ {port} 不存在！")
        return False
    print(f"✓ {port} 存在")

    # 2. 尝试快速打开/关闭
    print(f"\n步骤 2: 尝试打开串口...")
    print(f"如果这里卡住，说明端口被占用")

    start_time = time.time()
    try:
        print(f"  调用 serial.Serial('{port}', {baudrate})...")
        ser = serial.Serial(port, baudrate, timeout=1)
        elapsed = time.time() - start_time
        print(f"✓ 串口打开成功！耗时: {elapsed:.2f}秒")

        print(f"\n步骤 3: 测试串口属性...")
        print(f"  端口名: {ser.port}")
        print(f"  波特率: {ser.baudrate}")
        print(f"  是否打开: {ser.is_open}")

        print(f"\n步骤 4: 发送测试命令...")
        test_cmd = b'!START\r\n'
        ser.write(test_cmd)
        print(f"✓ 发送成功: {test_cmd}")

        print(f"\n步骤 5: 等待响应...")
        time.sleep(1)
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"收到响应: {response}")
        else:
            print(f"没有收到响应（这可能是正常的）")

        print(f"\n步骤 6: 关闭串口...")
        ser.close()
        print(f"✓ 串口已关闭")

        print(f"\n" + "=" * 60)
        print(f"✓ 测试成功！串口 {port} 工作正常")
        print(f"=" * 60)
        return True

    except serial.SerialException as e:
        elapsed = time.time() - start_time
        print(f"\n✗ 串口错误 (耗时: {elapsed:.2f}秒)")
        print(f"错误: {e}")
        print(f"\n可能原因:")
        print(f"  1. {port} 被其他程序占用")
        print(f"  2. 驱动程序问题")
        print(f"  3. 设备未正确连接")
        return False
    except KeyboardInterrupt:
        print(f"\n\n用户中止测试")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n✗ 未知错误 (耗时: {elapsed:.2f}秒)")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n这个工具会测试 COM7 是否可以正常打开")
    print("如果程序卡住超过5秒，请按 Ctrl+C 中止")
    print("然后关闭所有可能占用串口的程序\n")

    input("按回车键开始测试...")

    success = test_quick_connection('COM7', 9600)

    if not success:
        print(f"\n建议:")
        print(f"  1. 关闭所有串口调试工具、Arduino IDE 等")
        print(f"  2. 在任务管理器中查找占用串口的进程")
        print(f"  3. 重新插拔 USB 线")
        print(f"  4. 重启电脑")

    input(f"\n按回车键退出...")
