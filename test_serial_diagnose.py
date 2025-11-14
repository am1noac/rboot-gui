#!/usr/bin/env python3
"""
USB串口诊断工具
用于测试dummy机械臂的串口通信
"""
import serial
import serial.tools.list_ports
import time
import sys

def list_ports():
    """列出所有可用的串口"""
    print("\n=== 可用串口列表 ===")
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("未找到任何串口设备！")
        return []

    for port in ports:
        print(f"端口: {port.device}")
        print(f"  描述: {port.description}")
        print(f"  硬件ID: {port.hwid}")
        print()
    return [p.device for p in ports]

def test_port(port_name, baudrate=115200):
    """测试指定串口"""
    print(f"\n=== 测试串口 {port_name} ===")
    print(f"波特率: {baudrate}")

    try:
        # 尝试打开串口
        print("\n1. 打开串口...")
        ser = serial.Serial(
            port=port_name,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0,
            write_timeout=1.0,  # 测试时使用较短的超时
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
        print("✓ 串口打开成功")

        # 设置控制信号
        print("\n2. 设置控制信号...")
        ser.dtr = True
        ser.rts = True
        print(f"✓ DTR: {ser.dtr}, RTS: {ser.rts}")

        time.sleep(0.2)

        # 清空缓冲区
        print("\n3. 清空缓冲区...")
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print(f"✓ 输入缓冲区: {ser.in_waiting} 字节")
        print(f"✓ 输出缓冲区已清空")

        # 测试写入（发送简单的测试数据）
        print("\n4. 测试写入...")
        test_data = b'\xbb\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        hex_str = ' '.join(f'{b:02X}' for b in test_data)
        print(f"发送数据: {hex_str}")

        try:
            bytes_written = ser.write(test_data)
            ser.flush()
            print(f"✓ 成功写入 {bytes_written} 字节")
        except serial.SerialTimeoutException:
            print("✗ 写入超时！")
            print("  可能原因：")
            print("  - 机械臂没有从串口读取数据")
            print("  - 串口缓冲区已满")
            print("  - 流控信号配置错误")
            print("  - 机械臂可能未配置为串口模式")
        except Exception as e:
            print(f"✗ 写入失败: {e}")

        # 测试读取
        print("\n5. 测试读取（等待1秒）...")
        time.sleep(1.0)

        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            hex_str = ' '.join(f'{b:02X}' for b in data)
            print(f"✓ 收到 {len(data)} 字节: {hex_str}")
        else:
            print("✗ 未收到任何数据")
            print("  可能原因：")
            print("  - 机械臂未启动或未连接")
            print("  - 机械臂未配置为串口模式")
            print("  - 波特率不匹配")
            print("  - 机械臂未响应该命令")

        # 检查串口状态
        print("\n6. 串口状态检查...")
        print(f"  输入缓冲区: {ser.in_waiting} 字节")
        print(f"  CTS (Clear To Send): {ser.cts}")
        print(f"  DSR (Data Set Ready): {ser.dsr}")
        print(f"  RI (Ring Indicator): {ser.ri}")
        print(f"  CD (Carrier Detect): {ser.cd}")

        # 关闭串口
        print("\n7. 关闭串口...")
        ser.close()
        print("✓ 串口已关闭")

        return True

    except serial.SerialException as e:
        print(f"✗ 串口错误: {e}")
        print("\n可能的解决方法:")
        print("  1. 检查串口是否被其他程序占用")
        print("  2. 检查USB线是否连接正常")
        print("  3. 重新插拔USB线")
        print("  4. 检查设备驱动是否正确安装")
        return False
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        return False

def test_loopback(port_name, baudrate=115200):
    """环回测试（需要将TX和RX短接）"""
    print(f"\n=== 环回测试 {port_name} ===")
    print("注意：此测试需要将串口的TX和RX引脚短接！")
    response = input("是否继续？(y/n): ")
    if response.lower() != 'y':
        return

    try:
        ser = serial.Serial(port_name, baudrate, timeout=1.0, write_timeout=1.0)

        test_data = b'\xAA\x55\x01\x02\x03\x04'
        print(f"发送: {' '.join(f'{b:02X}' for b in test_data)}")

        ser.write(test_data)
        ser.flush()

        time.sleep(0.1)
        received = ser.read(len(test_data))
        print(f"接收: {' '.join(f'{b:02X}' for b in received)}")

        if received == test_data:
            print("✓ 环回测试成功！串口硬件正常")
        else:
            print("✗ 环回测试失败！")

        ser.close()

    except Exception as e:
        print(f"✗ 环回测试错误: {e}")

def main():
    print("=" * 60)
    print("USB串口诊断工具 - Dummy机械臂")
    print("=" * 60)

    # 列出所有串口
    available_ports = list_ports()

    if not available_ports:
        print("\n未找到任何串口！请检查：")
        print("1. USB线是否连接")
        print("2. 驱动是否安装")
        print("3. 设备管理器中是否识别到设备")
        return

    # 选择要测试的串口
    print("\n请选择要测试的串口：")
    for i, port in enumerate(available_ports, 1):
        print(f"{i}. {port}")
    print("0. 退出")

    try:
        choice = int(input("\n请输入选项 (默认1): ") or "1")
        if choice == 0:
            return
        if choice < 1 or choice > len(available_ports):
            print("无效选项！")
            return

        port_name = available_ports[choice - 1]

        # 选择波特率
        print("\n请选择波特率：")
        print("1. 115200 (默认)")
        print("2. 9600")
        print("3. 19200")
        print("4. 38400")
        print("5. 57600")
        print("6. 自定义")

        baud_choice = input("\n请输入选项 (默认1): ") or "1"
        baud_rates = {
            "1": 115200,
            "2": 9600,
            "3": 19200,
            "4": 38400,
            "5": 57600
        }

        if baud_choice == "6":
            baudrate = int(input("请输入波特率: "))
        else:
            baudrate = baud_rates.get(baud_choice, 115200)

        # 执行测试
        success = test_port(port_name, baudrate)

        if not success:
            print("\n基本测试失败！")

        # 询问是否进行环回测试
        if success:
            response = input("\n是否进行环回测试？(y/n): ")
            if response.lower() == 'y':
                test_loopback(port_name, baudrate)

    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")

    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
