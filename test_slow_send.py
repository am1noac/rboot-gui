#!/usr/bin/env python3
"""
慢速发送测试 - 测试不同的发送间隔
"""
import serial
import time
import struct

def test_slow_send(port='COM7', baudrate=115200, interval=0.1):
    """
    以指定间隔持续发送命令
    :param interval: 发送间隔（秒）
    """
    print(f"慢速发送测试")
    print(f"端口: {port}")
    print(f"波特率: {baudrate}")
    print(f"发送间隔: {interval}秒")
    print("-" * 60)

    try:
        # 连接串口
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.5,
            write_timeout=1.0,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )

        ser.dtr = True
        ser.rts = True
        time.sleep(0.1)

        print(f"✓ 串口已打开")
        print(f"DTR: {ser.dtr}, RTS: {ser.rts}")
        print()

        # 清空缓冲区
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        # 模拟查询6个电机
        motor_ids = [1, 2, 3, 4, 5, 6]

        print(f"开始持续发送命令...")
        print(f"按Ctrl+C停止")
        print()

        success_count = 0
        fail_count = 0
        cycle = 0

        while True:
            cycle += 1
            print(f"\n=== 循环 {cycle} ===")

            for motor_id in motor_ids:
                # 构建查询编码器命令
                message = bytearray(12)
                message[0] = 0xbb  # 消息头
                message[1] = motor_id  # 电机ID
                message[2] = 0x09  # 命令ID (Get_Encoder_Estimates)
                # 其余字节为0
                message[11] = 0x00  # 校验和

                hex_msg = ' '.join(f'{b:02X}' for b in message)

                try:
                    start = time.time()
                    ser.write(message)
                    ser.flush()
                    elapsed = time.time() - start

                    print(f"电机{motor_id}: ✓ 成功 ({elapsed:.3f}秒)", end="  ")
                    success_count += 1

                    # 检查响应
                    if ser.in_waiting > 0:
                        response = ser.read(ser.in_waiting)
                        print(f"收到{len(response)}字节", end="")

                    print()  # 换行

                except serial.SerialTimeoutException:
                    print(f"电机{motor_id}: ✗ 超时")
                    fail_count += 1
                except Exception as e:
                    print(f"电机{motor_id}: ✗ 错误: {e}")
                    fail_count += 1

                # 等待指定间隔
                time.sleep(interval)

            print(f"\n统计: 成功 {success_count}, 失败 {fail_count}")
            print(f"成功率: {success_count/(success_count+fail_count)*100:.1f}%")

    except KeyboardInterrupt:
        print("\n\n用户中断")
        print(f"\n最终统计:")
        print(f"  成功: {success_count}")
        print(f"  失败: {fail_count}")
        if success_count + fail_count > 0:
            print(f"  成功率: {success_count/(success_count+fail_count)*100:.1f}%")
    except Exception as e:
        print(f"\n错误: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("串口已关闭")

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("慢速发送测试工具")
    print("=" * 60)
    print()
    print("此工具会持续向6个电机发送查询命令")
    print("用于测试不同发送间隔的效果")
    print()

    # 让用户选择间隔
    print("请选择发送间隔:")
    print("1. 10ms  (100命令/秒) - 非常快")
    print("2. 20ms  (50命令/秒)  - 快")
    print("3. 50ms  (20命令/秒)  - 中等")
    print("4. 100ms (10命令/秒)  - 慢")
    print("5. 200ms (5命令/秒)   - 很慢")
    print("6. 自定义")

    choice = input("\n请选择 (默认3): ") or "3"

    intervals = {
        "1": 0.01,
        "2": 0.02,
        "3": 0.05,
        "4": 0.1,
        "5": 0.2
    }

    if choice == "6":
        interval = float(input("请输入间隔（秒）: "))
    else:
        interval = intervals.get(choice, 0.05)

    print()
    test_slow_send('COM7', 115200, interval)
