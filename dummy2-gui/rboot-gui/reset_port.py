#!/usr/bin/env python3
"""
串口重置和诊断工具
用于排查和修复串口通信问题
"""

import sys
import time

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("✗ 缺少pyserial库！")
    print("请运行: pip install pyserial")
    sys.exit(1)


def list_all_ports():
    """列出所有可用的串口"""
    print("\n" + "="*60)
    print("串口设备检测")
    print("="*60)

    ports = serial.tools.list_ports.comports()

    if not ports:
        print("\n✗ 未找到任何串口设备")
        print("\n可能原因:")
        print("  - USB线未连接")
        print("  - 设备驱动未安装")
        print("  - 设备未上电")
        return []

    print(f"\n找到 {len(ports)} 个串口设备:\n")

    for i, port in enumerate(ports, 1):
        print(f"[{i}] {port.device}")
        print(f"    描述: {port.description}")
        print(f"    硬件ID: {port.hwid}")
        if port.manufacturer:
            print(f"    制造商: {port.manufacturer}")
        if port.product:
            print(f"    产品: {port.product}")
        if port.serial_number:
            print(f"    序列号: {port.serial_number}")
        print()

    return ports


def test_port(port_name, baudrate=115200):
    """测试指定串口"""
    print(f"\n测试串口: {port_name} (波特率: {baudrate})")
    print("-" * 60)

    try:
        print(f"[1/4] 尝试打开串口...")
        ser = serial.Serial(
            port=port_name,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0,
            write_timeout=2.0
        )

        print(f"✓ 串口打开成功")

        # 测试串口信息
        print(f"\n[2/4] 串口信息:")
        print(f"  端口名: {ser.port}")
        print(f"  波特率: {ser.baudrate}")
        print(f"  数据位: {ser.bytesize}")
        print(f"  校验位: {ser.parity}")
        print(f"  停止位: {ser.stopbits}")
        print(f"  是否打开: {ser.is_open}")

        # 清空缓冲区
        print(f"\n[3/4] 清空缓冲区...")
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print(f"✓ 缓冲区已清空")

        # 测试发送
        print(f"\n[4/4] 测试发送数据...")
        test_data = b'\xBB\x01\x09\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # 查询电机1
        bytes_written = ser.write(test_data)
        ser.flush()
        print(f"✓ 发送了 {bytes_written} 字节")

        # 尝试接收
        print(f"\n等待响应 (3秒)...")
        time.sleep(0.5)

        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"✓ 收到 {len(response)} 字节响应:")
            hex_data = ' '.join(f'{b:02X}' for b in response)
            print(f"  数据: {hex_data}")
        else:
            print(f"⚠ 未收到响应")
            print(f"  这可能是正常的，如果设备未运行CAN总线固件")

        ser.close()
        print(f"\n✓ 串口测试完成")
        return True

    except serial.SerialException as e:
        print(f"✗ 串口错误: {e}")
        print(f"\n可能原因:")
        print(f"  - 端口被其他程序占用")
        print(f"  - 权限不足 (Linux需要sudo或加入dialout组)")
        print(f"  - 设备驱动异常")
        return False

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def reset_port(port_name, baudrate=115200):
    """重置串口"""
    print(f"\n重置串口: {port_name}")
    print("-" * 60)

    try:
        # 打开并立即关闭，清空状态
        ser = serial.Serial(port_name, baudrate, timeout=0.5)
        print("✓ 串口已打开")

        # 清空缓冲区
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print("✓ 缓冲区已清空")

        # 设置DTR和RTS
        ser.setDTR(False)
        ser.setRTS(False)
        time.sleep(0.2)
        ser.setDTR(True)
        ser.setRTS(True)
        print("✓ DTR/RTS已重置")

        ser.close()
        time.sleep(0.5)
        print("✓ 串口已关闭")

        print("\n✓ 串口重置完成！")
        return True

    except Exception as e:
        print(f"✗ 重置失败: {e}")
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║         Rboot GUI - 串口诊断和重置工具                   ║
╚══════════════════════════════════════════════════════════╝
    """)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'list':
            list_all_ports()

        elif command == 'test':
            ports = list_all_ports()
            if not ports:
                return

            if len(sys.argv) > 2:
                port_name = sys.argv[2]
            else:
                print("\n请指定要测试的端口:")
                print("用法: python reset_port.py test COM7")
                return

            baudrate = int(sys.argv[3]) if len(sys.argv) > 3 else 115200
            test_port(port_name, baudrate)

        elif command == 'reset':
            if len(sys.argv) > 2:
                port_name = sys.argv[2]
            else:
                print("\n请指定要重置的端口:")
                print("用法: python reset_port.py reset COM7")
                return

            baudrate = int(sys.argv[3]) if len(sys.argv) > 3 else 115200
            reset_port(port_name, baudrate)

        else:
            print(f"未知命令: {command}")
            print("用法: python reset_port.py [list|test|reset] [端口] [波特率]")

    else:
        # 默认执行完整诊断
        ports = list_all_ports()

        if not ports:
            print("\n建议:")
            print("1. 检查USB线是否连接")
            print("2. 检查设备是否上电")
            print("3. 安装/更新设备驱动程序")
            print("4. 在Windows设备管理器中查看串口设备")
            return

        print("\n建议测试的端口:")
        for i, port in enumerate(ports, 1):
            if 'USB' in port.description.upper() or 'CH340' in port.description.upper():
                print(f"✓ [{i}] {port.device} - {port.description}")

        print("\n执行自动测试? (y/n): ", end='')
        try:
            choice = input().lower()
            if choice == 'y':
                for port in ports:
                    if 'USB' in port.description.upper() or 'CH340' in port.description.upper():
                        test_port(port.device, 115200)
                        print()
        except KeyboardInterrupt:
            print("\n取消")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
