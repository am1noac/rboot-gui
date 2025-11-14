#!/usr/bin/env python3
"""
快速检查COM7端口状态
"""
import serial
import serial.tools.list_ports
import time

def check_port():
    print("=" * 60)
    print("COM端口快速检查工具")
    print("=" * 60)

    # 1. 列出所有端口
    print("\n1. 列出所有可用端口:")
    print("-" * 60)
    ports = serial.tools.list_ports.comports()

    if not ports:
        print("❌ 没有找到任何COM端口！")
        print("\n可能原因:")
        print("  - USB设备未连接")
        print("  - 驱动未安装")
        print("  - 设备未被识别")
        return

    com7_found = False
    for port in ports:
        is_com7 = port.device == 'COM7'
        marker = "👉" if is_com7 else "  "
        print(f"{marker} {port.device}")
        print(f"   描述: {port.description}")
        print(f"   硬件ID: {port.hwid}")
        print()
        if is_com7:
            com7_found = True

    if not com7_found:
        print("⚠️  未找到COM7端口！")
        print("\n请确认:")
        print("  1. 设备是否连接")
        print("  2. 实际的端口号是否是COM7")
        print("  3. 在设备管理器中查看实际端口号")
        return

    # 2. 尝试打开COM7
    print("\n2. 尝试打开COM7:")
    print("-" * 60)

    try:
        print("正在打开COM7...")
        ser = serial.Serial()
        ser.port = 'COM7'
        ser.baudrate = 115200
        ser.timeout = 1
        ser.write_timeout = 1

        print("调用serial.open()...")
        start_time = time.time()

        ser.open()

        elapsed = time.time() - start_time
        print(f"✓ 成功打开! 耗时: {elapsed:.3f}秒")

        # 3. 检查串口状态
        print("\n3. 串口状态:")
        print("-" * 60)
        print(f"端口: {ser.port}")
        print(f"波特率: {ser.baudrate}")
        print(f"已打开: {ser.is_open}")
        print(f"DTR: {ser.dtr}")
        print(f"RTS: {ser.rts}")
        print(f"CTS: {ser.cts}")
        print(f"DSR: {ser.dsr}")

        if not ser.cts:
            print("\n⚠️  CTS为False - 设备可能未准备好")

        # 4. 尝试写入测试
        print("\n4. 写入测试:")
        print("-" * 60)
        test_data = b'\xAA\x55'
        print(f"发送: {' '.join(f'{b:02X}' for b in test_data)}")

        try:
            start_time = time.time()
            ser.write(test_data)
            ser.flush()
            elapsed = time.time() - start_time
            print(f"✓ 写入成功! 耗时: {elapsed:.3f}秒")
        except serial.SerialTimeoutException:
            print("❌ 写入超时!")
            print("\n这说明设备没有从串口读取数据")
        except Exception as e:
            print(f"❌ 写入错误: {e}")

        ser.close()
        print("\n串口已关闭")

        print("\n" + "=" * 60)
        print("结论: COM7端口可以正常打开")
        print("如果GUI程序卡住，可能是其他原因")
        print("=" * 60)

    except serial.SerialException as e:
        print(f"❌ 无法打开COM7: {e}")
        print("\n可能原因:")
        print("  1. 端口被其他程序占用")
        print("     - 关闭串口调试助手")
        print("     - 关闭Arduino IDE")
        print("     - 关闭其他串口程序")
        print("  2. 权限不足")
        print("  3. 驱动问题")
        print("\n请在任务管理器中检查是否有其他程序占用COM7")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

if __name__ == "__main__":
    check_port()
    input("\n按回车键退出...")
