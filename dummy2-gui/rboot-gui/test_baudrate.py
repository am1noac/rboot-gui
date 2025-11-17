#!/usr/bin/env python3
"""
自动波特率检测脚本
尝试不同波特率连接dummy v2机械臂
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


def test_baudrate(port, baudrate):
    """测试指定波特率"""
    print(f"\n{'='*60}")
    print(f"测试波特率: {baudrate}")
    print(f"{'='*60}")

    try:
        # 打开串口
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2.0,
            write_timeout=2.0
        )

        print(f"✓ 串口已打开 (波特率: {baudrate})")

        # 清空缓冲区
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.2)

        # 发送查询命令（查询电机1的位置）
        test_data = b'\xBB\x01\x09\x00\x00\x00\x00\x00\x00\x00\x00\x00'

        print(f"→ 发送查询命令: {' '.join(f'{b:02X}' for b in test_data)}")
        ser.write(test_data)
        ser.flush()

        # 等待响应
        print(f"⏳ 等待响应 (2秒)...")
        time.sleep(0.5)

        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"✓✓✓ 收到 {len(response)} 字节响应!")
            hex_data = ' '.join(f'{b:02X}' for b in response)
            print(f"← 数据: {hex_data}")
            ser.close()
            return True, baudrate
        else:
            print(f"✗ 无响应")
            ser.close()
            return False, baudrate

    except Exception as e:
        print(f"✗ 错误: {e}")
        return False, baudrate


def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════╗
║       Dummy v2 机械臂 - 自动波特率检测工具               ║
╚══════════════════════════════════════════════════════════╝
    """)

    # 获取端口
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        # 自动检测
        ports = serial.tools.list_ports.comports()
        if not ports:
            print("✗ 未找到任何串口设备")
            return

        print("找到以下串口设备:")
        for i, p in enumerate(ports, 1):
            print(f"  [{i}] {p.device} - {p.description}")

        # 选择USB串口
        for p in ports:
            if 'USB' in p.description.upper():
                port = p.device
                print(f"\n✓ 自动选择: {port}")
                break
        else:
            port = ports[0].device
            print(f"\n✓ 使用: {port}")

    print(f"\n目标端口: {port}")
    print(f"设备型号: Dummy v2")

    # 常见波特率列表（优先测试9600和115200）
    baudrates = [
        115200,  # 先测试当前使用的
        9600,    # Dummy v2常用波特率
        57600,
        38400,
        19200,
        230400,
    ]

    print(f"\n将测试以下波特率: {', '.join(map(str, baudrates))}")
    input("\n按回车键开始测试...")

    # 测试每个波特率
    successful_baudrate = None

    for baudrate in baudrates:
        success, tested_baudrate = test_baudrate(port, baudrate)

        if success:
            print(f"\n{'='*60}")
            print(f"🎉 成功! 正确的波特率是: {tested_baudrate}")
            print(f"{'='*60}")
            successful_baudrate = tested_baudrate
            break

        time.sleep(0.5)  # 间隔一下再测试下一个

    if successful_baudrate:
        print(f"\n✅ 检测完成！")
        print(f"\n下一步操作:")
        print(f"1. 修改 main.py 第63行:")
        print(f"   client_instance = SerialClient(port='{port}', baudrate={successful_baudrate})")
        print(f"\n2. 重新启动程序")
        print(f"\n3. 点击连接设备，应该可以正常连接了！")
    else:
        print(f"\n✗ 所有波特率都测试失败")
        print(f"\n可能原因:")
        print(f"  1. 设备固件未运行")
        print(f"  2. 设备协议不同")
        print(f"  3. 需要特殊的初始化命令")
        print(f"\n建议:")
        print(f"  1. 检查设备手册，确认正确的波特率和协议")
        print(f"  2. 尝试使用串口调试助手手动测试")
        print(f"  3. 联系设备厂商获取技术支持")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
