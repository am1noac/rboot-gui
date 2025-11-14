#!/usr/bin/env python3
"""
9600波特率测试 - 找到最佳发送间隔
"""
import serial
import time

def test_9600_interval(interval=0.15):
    """
    在9600波特率下测试指定间隔
    """
    port = 'COM7'
    baudrate = 9600

    print(f"=" * 70)
    print(f"9600波特率发送测试")
    print(f"端口: {port}")
    print(f"波特率: {baudrate}")
    print(f"发送间隔: {interval*1000:.0f}ms")
    print(f"=" * 70)

    try:
        # 连接串口
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=0.5,
            write_timeout=2.0,  # 9600波特率下需要更长的写超时
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )

        ser.dtr = True
        ser.rts = True
        time.sleep(0.2)

        print(f"✓ 串口已连接")
        print(f"CTS: {ser.cts}, DSR: {ser.dsr}")
        print()

        # 清空缓冲区
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        # 测试消息
        test_message = bytearray(12)
        test_message[0] = 0xbb
        test_message[1] = 0x01  # 电机1
        test_message[2] = 0x09  # 查询编码器

        print(f"开始测试...")
        print(f"按Ctrl+C停止")
        print()

        success_count = 0
        timeout_count = 0
        cycle = 0

        while cycle < 20:  # 测试20个循环
            cycle += 1
            print(f"循环 {cycle}:")

            # 发送6条命令（模拟查询6个电机）
            for motor_id in range(1, 7):
                test_message[1] = motor_id
                hex_msg = ' '.join(f'{b:02X}' for b in test_message)

                try:
                    start = time.time()
                    ser.write(test_message)
                    ser.flush()
                    elapsed = time.time() - start

                    print(f"  电机{motor_id}: ✓ {elapsed:.3f}秒", end="")
                    success_count += 1

                    # 检查响应
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting)
                        print(f" (收到{len(data)}字节)", end="")

                    print()

                except serial.SerialTimeoutException:
                    print(f"  电机{motor_id}: ✗ 超时")
                    timeout_count += 1
                except Exception as e:
                    print(f"  电机{motor_id}: ✗ {e}")
                    timeout_count += 1

                # 间隔等待
                time.sleep(interval)

            # 显示统计
            total = success_count + timeout_count
            if total > 0:
                success_rate = success_count / total * 100
                print(f"\n  当前统计: 成功{success_count} 超时{timeout_count} 成功率{success_rate:.1f}%\n")

        ser.close()

        # 最终统计
        print(f"\n" + "=" * 70)
        print(f"测试完成！")
        print(f"=" * 70)
        total = success_count + timeout_count
        if total > 0:
            success_rate = success_count / total * 100
            print(f"发送间隔: {interval*1000:.0f}ms")
            print(f"总计: {total}条")
            print(f"成功: {success_count}条")
            print(f"超时: {timeout_count}条")
            print(f"成功率: {success_rate:.1f}%")
            print()

            if success_rate >= 95:
                print(f"✓ 优秀! {interval*1000:.0f}ms间隔工作良好")
            elif success_rate >= 80:
                print(f"⚠ 尚可，但建议增加间隔到{(interval*1.5)*1000:.0f}ms")
            else:
                print(f"✗ 不稳定! 建议增加间隔到{(interval*2)*1000:.0f}ms或更长")

    except KeyboardInterrupt:
        print("\n\n用户中断")
    except serial.SerialException as e:
        print(f"\n✗ 串口错误: {e}")
    except Exception as e:
        print(f"\n✗ 错误: {e}")

if __name__ == "__main__":
    print("\n9600波特率测试工具")
    print("-" * 70)
    print("此工具帮助找到9600波特率下的最佳发送间隔")
    print()

    # 测试不同间隔
    intervals_to_test = [
        (0.1, "100ms - 较快"),
        (0.15, "150ms - 推荐"),
        (0.2, "200ms - 保守"),
        (0.3, "300ms - 很慢")
    ]

    print("请选择要测试的间隔:")
    for i, (interval, desc) in enumerate(intervals_to_test, 1):
        print(f"{i}. {desc}")
    print("5. 全部测试（依次测试所有间隔）")

    choice = input("\n请选择 (默认2): ") or "2"

    if choice == "5":
        # 测试所有间隔
        print("\n将依次测试所有间隔...\n")
        for interval, desc in intervals_to_test:
            print(f"\n{'='*70}")
            print(f"开始测试: {desc}")
            print(f"{'='*70}\n")
            test_9600_interval(interval)
            if interval != intervals_to_test[-1][0]:
                input("\n按回车继续下一个测试...")
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(intervals_to_test):
                interval, desc = intervals_to_test[idx]
                test_9600_interval(interval)
            else:
                print("无效选择，使用默认150ms")
                test_9600_interval(0.15)
        except:
            print("无效选择，使用默认150ms")
            test_9600_interval(0.15)

    print("\n测试结束")
