#!/usr/bin/env python3
"""
端口重置工具 - 解决serial.open()卡住的问题
"""
import serial
import serial.tools.list_ports
import time
import sys

def reset_port(port='COM7'):
    """尝试重置串口"""
    print(f"=" * 60)
    print(f"端口重置工具 - {port}")
    print(f"=" * 60)

    # 1. 检查端口是否存在
    print(f"\n1. 检查端口是否存在...")
    ports = serial.tools.list_ports.comports()
    port_found = False

    for p in ports:
        if p.device == port:
            port_found = True
            print(f"✓ 找到{port}")
            print(f"  描述: {p.description}")
            break

    if not port_found:
        print(f"✗ 未找到{port}！")
        print("\n可用端口:")
        for p in ports:
            print(f"  {p.device}: {p.description}")
        return False

    # 2. 尝试以各种方式打开和关闭端口
    print(f"\n2. 尝试重置端口...")

    try:
        # 方法1: 快速打开关闭
        print(f"  方法1: 快速打开关闭...")
        ser = serial.Serial(port, 9600, timeout=0.1)
        time.sleep(0.1)
        ser.close()
        print(f"  ✓ 完成")
        time.sleep(0.5)

        # 方法2: 设置DTR/RTS然后关闭
        print(f"  方法2: 重置控制信号...")
        ser = serial.Serial(port, 9600, timeout=0.1)
        ser.dtr = False
        ser.rts = False
        time.sleep(0.1)
        ser.dtr = True
        ser.rts = True
        time.sleep(0.1)
        ser.close()
        print(f"  ✓ 完成")
        time.sleep(0.5)

        # 方法3: 清空缓冲区
        print(f"  方法3: 清空缓冲区...")
        ser = serial.Serial(port, 9600, timeout=0.1)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.1)
        ser.close()
        print(f"  ✓ 完成")

        print(f"\n✓ 端口重置成功!")
        return True

    except serial.SerialException as e:
        print(f"\n✗ 无法重置: {e}")
        print(f"\n可能的原因:")
        print(f"  1. 端口被其他程序占用")
        print(f"  2. 需要管理员权限")
        print(f"  3. 驱动问题")
        return False
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return False

def main():
    print("此工具尝试重置COM7端口")
    print("用于解决serial.open()卡住的问题\n")

    success = reset_port('COM7')

    if success:
        print(f"\n" + "=" * 60)
        print(f"重置成功！")
        print(f"=" * 60)
        print(f"\n现在可以尝试运行GUI程序:")
        print(f"  python dummy2-gui/rboot-gui/main.py")
    else:
        print(f"\n" + "=" * 60)
        print(f"重置失败！")
        print(f"=" * 60)
        print(f"\n建议:")
        print(f"  1. 关闭所有Python程序")
        print(f"  2. 关闭串口调试工具")
        print(f"  3. 重新插拔USB线")
        print(f"  4. 重启电脑")

if __name__ == "__main__":
    main()
    input("\n按回车键退出...")
