#!/usr/bin/env python3
"""
文本协议命令测试工具
用于测试设备支持哪些命令
"""

import serial
import time
import sys

def test_command(ser, command):
    """发送命令并等待响应"""
    print(f"\n>>> 发送: {command}")

    try:
        # 发送命令
        if not command.endswith('\r\n'):
            command = command + '\r\n'

        ser.write(command.encode('utf-8'))
        ser.flush()
        print(f"✓ 命令已发送")

        # 等待响应
        time.sleep(0.5)

        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            print(f"<<< 收到响应: {response.strip()}")
            return response
        else:
            print("(没有响应)")
            return None

    except Exception as e:
        print(f"✗ 错误: {e}")
        return None

def main():
    port = 'COM7'
    baudrate = 9600

    print("=" * 60)
    print("文本协议命令测试工具")
    print("=" * 60)
    print(f"\n连接参数:")
    print(f"  端口: {port}")
    print(f"  波特率: {baudrate}")

    try:
        print(f"\n正在连接...")
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"✓ 连接成功！\n")

        # 清空缓冲区
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.2)

        print("=" * 60)
        print("常用命令测试")
        print("=" * 60)

        # 测试常用命令
        commands_to_test = [
            ("!DISABLE", "失能电机（允许手动移动）"),
            ("!ENABLE", "使能电机（进入控制模式）"),
            ("!STOP", "停止电机"),
            ("!IDLE", "空闲模式"),
            ("!UNLOCK", "解锁"),
            ("!LOCK", "锁定"),
            ("!FREE", "释放"),
        ]

        print("\n提示: 按回车键测试下一个命令，输入'skip'跳过，输入'quit'退出\n")

        for cmd, desc in commands_to_test:
            print(f"\n{'='*60}")
            print(f"测试命令: {cmd} - {desc}")
            print(f"{'='*60}")

            choice = input(f"按回车测试此命令，或输入'skip'跳过: ").strip().lower()

            if choice == 'quit':
                break
            elif choice == 'skip':
                print("跳过")
                continue

            test_command(ser, cmd)

        # 自定义命令测试
        print(f"\n{'='*60}")
        print("自定义命令测试")
        print(f"{'='*60}")
        print("你可以输入任何命令进行测试")
        print("输入 'quit' 退出\n")

        while True:
            custom_cmd = input("输入命令（如 !DISABLE）: ").strip()

            if custom_cmd.lower() == 'quit':
                break

            if not custom_cmd:
                continue

            test_command(ser, custom_cmd)

        print(f"\n正在关闭连接...")
        ser.close()
        print(f"✓ 连接已关闭")

    except serial.SerialException as e:
        print(f"\n✗ 串口错误: {e}")
        print(f"\n可能的原因:")
        print(f"  1. {port} 被其他程序占用")
        print(f"  2. 请先关闭 main.py")

    except KeyboardInterrupt:
        print(f"\n\n用户中止")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n{'='*60}")
    input("按回车键退出...")

if __name__ == "__main__":
    main()
