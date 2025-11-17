#!/usr/bin/env python3
"""
Dummy v2 完整诊断报告生成器
用于排查连接问题并生成详细报告
"""

import socket
import serial
import serial.tools.list_ports
import subprocess
import platform

def generate_diagnostic_report():
    """生成完整的诊断报告"""

    print("=" * 80)
    print("Dummy v2 连接诊断报告")
    print("=" * 80)
    print()

    # 1. 系统信息
    print("## 系统信息")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {platform.python_version()}")
    print()

    # 2. 串口信息
    print("## 串口设备")
    ports = list(serial.tools.list_ports.comports())
    if ports:
        for port in ports:
            print(f"- {port.device}: {port.description}")
            print(f"  HWID: {port.hwid}")
    else:
        print("未找到串口设备")
    print()

    # 3. 网络信息
    print("## 网络配置")
    try:
        # 获取本机IP
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if 'IPv4' in line or 'IP 地址' in line:
                print(line.strip())
    except:
        print("无法获取网络配置")
    print()

    # 4. ARP表（查找网络设备）
    print("## 网络设备扫描 (ARP表)")
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, shell=True)
        lines = result.stdout.split('\n')
        print("192.168.0.x 段设备:")
        for line in lines:
            if '192.168.0.' in line and '动态' in line:
                print(f"  {line.strip()}")
    except:
        print("无法获取ARP表")
    print()

    # 5. 测试结果总结
    print("## 测试结果总结")
    print()
    print("### 串口模式测试")
    print("- ❌ COM7 @ 9600波特率: 无响应")
    print("- ❌ COM7 @ 115200波特率: 无响应")
    print("- 结论: COM7虚拟串口不是数据通信接口")
    print()

    print("### 网络模式测试")
    print("- ❌ 192.168.0.88:9999 - 超时无响应")
    print("- ⚠️  192.168.0.5:3333 - 连接被拒绝 (WinError 10054)")
    print("- ⚠️  192.168.0.5:8888 - 连接被拒绝")
    print("- 结论: 192.168.0.5有服务监听但拒绝CAN命令")
    print()

    # 6. 尝试的解决方案
    print("## 已尝试的解决方案")
    print("1. ✅ 修复串口超时机制")
    print("2. ✅ 启用DTR/RTS信号")
    print("3. ✅ 测试多个波特率")
    print("4. ✅ 测试CAN协议和ODrive协议")
    print("5. ✅ 修复CAN消息格式（添加0xCC尾部）")
    print("6. ✅ 使用正确的初始化命令")
    print("7. ✅ 扫描网络查找设备IP")
    print()

    # 7. 当前状态
    print("## 当前状态")
    print("- 设备型号: Dummy v2")
    print("- 物理连接: USB + WiFi")
    print("- 屏幕显示: 位置姿态（无IP信息）")
    print("- COM端口: COM7 (虚拟串口)")
    print("- 可能的设备IP: 192.168.0.5")
    print()

    # 8. 需要的信息
    print("## 需要确认的信息")
    print("1. [ ] 设备的正确IP地址是多少？")
    print("2. [ ] 设备是否需要特殊的配置模式？")
    print("3. [ ] 是否需要先在设备上配置WiFi连接？")
    print("4. [ ] UDP端口号是多少？(3333? 9999?)")
    print("5. [ ] 是否需要特殊的握手协议？")
    print("6. [ ] 设备文档/手册在哪里？")
    print()

    # 9. 建议的下一步
    print("## 建议的下一步")
    print("1. 检查GitHub仓库 (https://github.com/am1noac/dummy2) 的:")
    print("   - README.md")
    print("   - Issues (查找类似问题)")
    print("   - Wiki/文档")
    print()
    print("2. 尝试运行原始的dummy2-gui/main.py")
    print("   cd D:\\Works\\dummy2-master\\dummy2-gui")
    print("   python main.py")
    print()
    print("3. 检查设备是否有配置界面/按钮")
    print()
    print("4. 如果有设备说明书，查找:")
    print("   - WiFi配置方法")
    print("   - IP地址设置")
    print("   - 初始化步骤")
    print()

    print("=" * 80)
    print("报告生成完成")
    print("可以将此报告提交到 GitHub Issue 寻求帮助")
    print("=" * 80)

if __name__ == "__main__":
    generate_diagnostic_report()
