#!/usr/bin/env python3
"""
设备协议检测工具
测试设备响应CAN协议还是ODrive ASCII协议
"""

import serial
import serial.tools.list_ports
import time

def test_protocol(port, baudrate):
    """测试指定波特率下的协议响应"""
    print(f"\n{'='*60}")
    print(f"测试 {port} @ {baudrate} 波特率")
    print(f"{'='*60}")

    ser = None
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=1.0,
            write_timeout=None
        )

        time.sleep(0.2)  # 等待端口稳定
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        print(f"✓ 串口打开成功")

        # 测试1: CAN协议命令 (查询电机1)
        print(f"\n[测试1] 发送CAN协议命令...")
        can_cmd = bytearray([0xBB, 0x01, 0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        hex_str = ' '.join(f'{b:02X}' for b in can_cmd)
        print(f"  发送: {hex_str}")
        ser.write(can_cmd)
        time.sleep(0.5)

        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"  ✓ 收到响应: {len(response)} 字节")
            hex_resp = ' '.join(f'{b:02X}' for b in response[:min(32, len(response))])
            ascii_resp = ''.join(chr(b) if 32 <= b < 127 else '.' for b in response[:min(32, len(response))])
            print(f"    HEX: {hex_resp}")
            print(f"    ASCII: {ascii_resp}")
            print(f"  ✅ 设备响应CAN协议！")
            return "CAN"
        else:
            print(f"  ✗ 无响应")

        # 测试2: ODrive ASCII协议
        print(f"\n[测试2] 发送ODrive ASCII命令...")
        odrive_cmds = [
            b"r vbus_voltage\n",
            b"r axis0.error\n",
            b"i\n",
            b"?\n"
        ]

        for cmd in odrive_cmds:
            ser.reset_input_buffer()
            print(f"  发送: {cmd.decode('ascii').strip()}")
            ser.write(cmd)
            time.sleep(0.3)

            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                print(f"  ✓ 收到响应: {len(response)} 字节")
                try:
                    text = response.decode('ascii', errors='ignore')
                    print(f"    内容: {text[:100]}")
                except:
                    hex_resp = ' '.join(f'{b:02X}' for b in response[:min(32, len(response))])
                    print(f"    HEX: {hex_resp}")
                print(f"  ✅ 设备响应ODrive ASCII协议！")
                return "ODrive"
            else:
                print(f"  ✗ 无响应")

        # 测试3: 监听任何数据
        print(f"\n[测试3] 监听5秒，看是否有主动发送的数据...")
        print(f"  (请尝试移动机械臂或按下设备上的按钮)")
        start_time = time.time()
        while time.time() - start_time < 5:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                print(f"\n  ✓ 收到数据: {len(data)} 字节")
                hex_data = ' '.join(f'{b:02X}' for b in data[:min(32, len(data))])
                ascii_data = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[:min(32, len(data))])
                print(f"    HEX: {hex_data}")
                print(f"    ASCII: {ascii_data}")
                return "Unknown"
            time.sleep(0.1)

        print(f"  ✗ 5秒内无任何数据")
        return None

    except serial.SerialException as e:
        print(f"✗ 串口错误: {e}")
        return None
    except Exception as e:
        print(f"✗ 错误: {e}")
        return None
    finally:
        # 确保串口一定被关闭
        if ser and ser.is_open:
            try:
                ser.close()
                print(f"✓ 串口已关闭")
            except:
                pass

def main():
    print("=" * 60)
    print("设备协议自动检测工具")
    print("=" * 60)

    # 列出所有串口
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("✗ 未找到任何串口")
        return

    print(f"\n找到 {len(ports)} 个串口:")
    for i, port in enumerate(ports):
        print(f"  [{i+1}] {port.device} - {port.description}")

    # 选择USB串口
    usb_port = None
    for port in ports:
        desc_upper = port.description.upper()
        if any(kw in desc_upper for kw in ['USB', 'CH340', 'CH341']) and port.device not in ['COM1', 'COM2']:
            usb_port = port.device
            print(f"\n✓ 自动选择: {usb_port} - {port.description}")
            break

    if not usb_port:
        choice = input(f"\n请选择串口 [1-{len(ports)}]: ")
        try:
            usb_port = ports[int(choice)-1].device
        except:
            print("✗ 无效选择")
            return

    # 测试常用波特率 (9600优先，因为设备管理器显示9600)
    baudrates = [9600, 115200, 57600, 38400, 19200, 230400]

    results = {}
    for baudrate in baudrates:
        result = test_protocol(usb_port, baudrate)
        results[baudrate] = result
        if result in ["CAN", "ODrive"]:
            print(f"\n" + "="*60)
            print(f"✅ 找到工作协议！")
            print(f"  端口: {usb_port}")
            print(f"  波特率: {baudrate}")
            print(f"  协议: {result}")
            print(f"="*60)
            break

    # 总结
    print(f"\n" + "="*60)
    print("测试总结:")
    print(f"="*60)
    for baudrate, result in results.items():
        status = "✓" if result else "✗"
        result_str = result if result else "无响应"
        print(f"  {status} {baudrate:6d} 波特率: {result_str}")

    if not any(results.values()):
        print(f"\n⚠ 所有波特率都无响应")
        print(f"\n可能原因:")
        print(f"  1. 设备未上电或未连接")
        print(f"  2. 设备使用了未测试的波特率")
        print(f"  3. 设备需要特殊的初始化流程")
        print(f"  4. USB线缆问题")
        print(f"\n建议:")
        print(f"  - 检查设备指示灯是否亮起")
        print(f"  - 重新插拔USB线")
        print(f"  - 查阅设备说明书")

if __name__ == "__main__":
    main()
