#!/usr/bin/env python3
"""
快速测试串口写入 - 用于快速诊断写超时问题
"""
import serial
import time

def quick_test():
    port = 'COM7'
    baudrate = 115200

    print(f"快速测试: {port} @ {baudrate}")
    print("-" * 50)

    try:
        # 测试1: 短超时
        print("\n测试1: 使用1秒写超时")
        ser = serial.Serial(port, baudrate, timeout=1, write_timeout=1)
        ser.dtr = True
        ser.rts = True
        time.sleep(0.1)

        test_data = b'\xbb\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        print(f"发送: {' '.join(f'{b:02X}' for b in test_data)}")

        try:
            start = time.time()
            ser.write(test_data)
            ser.flush()
            elapsed = time.time() - start
            print(f"✓ 成功! 耗时: {elapsed:.3f}秒")
        except serial.SerialTimeoutException:
            print(f"✗ 写入超时!")
        except Exception as e:
            print(f"✗ 错误: {e}")

        ser.close()

        # 测试2: 无限超时
        print("\n测试2: 使用无限写超时")
        print("警告: 如果设备不接收数据，此测试会卡住!")
        print("如果卡住，请按Ctrl+C中断")

        ser = serial.Serial(port, baudrate, timeout=1, write_timeout=None)
        ser.dtr = True
        ser.rts = True
        time.sleep(0.1)

        print(f"发送: {' '.join(f'{b:02X}' for b in test_data)}")

        try:
            start = time.time()
            ser.write(test_data)
            ser.flush()
            elapsed = time.time() - start
            print(f"✓ 成功! 耗时: {elapsed:.3f}秒")

            # 尝试读取响应
            time.sleep(0.5)
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                print(f"收到响应: {' '.join(f'{b:02X}' for b in response)}")
            else:
                print("未收到响应")

        except KeyboardInterrupt:
            print("\n✗ 用户中断 - 这证明设备没有读取数据!")
            print("\n结论: 机械臂可能:")
            print("  1. 未配置为串口模式")
            print("  2. 未启动或未连接")
            print("  3. 使用不同的波特率")
        except Exception as e:
            print(f"✗ 错误: {e}")

        ser.close()

        # 测试3: 检查串口状态
        print("\n测试3: 串口状态信号")
        ser = serial.Serial(port, baudrate, timeout=1, write_timeout=1)
        ser.dtr = True
        ser.rts = True
        time.sleep(0.1)

        print(f"DTR: {ser.dtr}")
        print(f"RTS: {ser.rts}")
        print(f"CTS: {ser.cts}")
        print(f"DSR: {ser.dsr}")
        print(f"CD: {ser.cd}")
        print(f"RI: {ser.ri}")

        if not ser.cts:
            print("\n⚠ CTS为False - 设备可能未准备好接收数据!")

        ser.close()

    except serial.SerialException as e:
        print(f"\n✗ 串口错误: {e}")
        print("\n可能的原因:")
        print("  1. 端口不存在或被占用")
        print("  2. 驱动未安装")
        print("  3. 设备未连接")
    except Exception as e:
        print(f"\n✗ 未知错误: {e}")

    print("\n" + "-" * 50)
    print("测试完成")

if __name__ == "__main__":
    quick_test()
