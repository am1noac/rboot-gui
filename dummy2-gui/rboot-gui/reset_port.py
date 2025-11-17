#!/usr/bin/env python3
"""
串口重置工具
用于解决串口被占用或状态异常的问题
"""

import serial
import serial.tools.list_ports
import time
import sys


def list_all_ports():
    """列出所有可用串口"""
    print("\n" + "="*60)
    print("扫描系统串口...")
    print("="*60)

    ports = serial.tools.list_ports.comports()

    if not ports:
        print("✗ 未找到任何串口设备")
        return []

    print(f"\n找到 {len(ports)} 个串口设备:\n")
    for i, port in enumerate(ports):
        print(f"[{i+1}] {port.device}")
        print(f"    描述: {port.description}")
        print(f"    硬件ID: {port.hwid}")
        print()

    return [p.device for p in ports]


def test_port_open_close(port_name, baudrate=115200):
    """测试端口打开和关闭"""
    print(f"\n尝试打开串口: {port_name} (波特率: {baudrate})")

    try:
        # 尝试打开串口
        ser = serial.Serial(
            port=port_name,
            baudrate=baudrate,
            timeout=1.0,
            write_timeout=2.0
        )

        print(f"✓ 串口打开成功")
        print(f"  端口状态: {'已打开' if ser.is_open else '已关闭'}")

        # 清空缓冲区
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print(f"✓ 缓冲区已清空")

        # 关闭串口
        ser.close()
        print(f"✓ 串口已关闭")

        time.sleep(0.5)
        return True

    except serial.SerialException as e:
        print(f"✗ 串口打开失败: {e}")
        print(f"\n可能原因:")
        print(f"  1. 端口被其他程序占用")
        print(f"  2. 驱动程序问题")
        print(f"  3. USB设备连接不稳定")
        return False
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        return False


def force_release_port(port_name):
    """尝试强制释放端口"""
    print(f"\n尝试强制释放端口: {port_name}")

    attempts = 3
    for attempt in range(1, attempts + 1):
        print(f"\n尝试 {attempt}/{attempts}...")

        try:
            # 短暂打开后立即关闭
            ser = serial.Serial(port_name, timeout=0.1)
            ser.close()
            time.sleep(0.2)

            # 再次尝试打开验证
            ser = serial.Serial(port_name, timeout=0.1)
            if ser.is_open:
                print(f"✓ 端口可以正常打开")
                ser.close()
                return True
            ser.close()

        except Exception as e:
            print(f"  失败: {e}")
            time.sleep(1)

    print(f"\n✗ 无法释放端口 {port_name}")
    print(f"\n建议:")
    print(f"  1. 关闭所有可能占用串口的程序")
    print(f"  2. 在设备管理器中禁用再启用该端口")
    print(f"  3. 重新插拔USB线")
    print(f"  4. 重启计算机")
    return False


def main():
    print("="*60)
    print("串口重置工具")
    print("="*60)

    # 列出所有串口
    ports = list_all_ports()

    if not ports:
        input("\n按回车键退出...")
        return

    # 选择端口
    print("\n请选择要重置的串口:")
    print("(直接输入端口名称，如 COM7，或输入序号)")

    user_input = input("\n请输入: ").strip().upper()

    # 解析输入
    target_port = None
    if user_input.startswith('COM'):
        target_port = user_input
    else:
        try:
            index = int(user_input) - 1
            if 0 <= index < len(ports):
                target_port = ports[index]
        except ValueError:
            pass

    if not target_port:
        print(f"\n✗ 无效的输入: {user_input}")
        input("\n按回车键退出...")
        return

    print(f"\n选择的端口: {target_port}")
    print("="*60)

    # 测试端口
    if test_port_open_close(target_port):
        print(f"\n✓ 端口 {target_port} 工作正常！")
    else:
        print(f"\n端口 {target_port} 无法正常打开，尝试强制释放...")
        force_release_port(target_port)

    print("\n" + "="*60)
    print("操作完成")
    print("="*60)

    input("\n按回车键退出...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中止操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
