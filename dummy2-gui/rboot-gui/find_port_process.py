#!/usr/bin/env python3
"""
查找占用串口的进程
"""

import subprocess
import sys

def find_port_process(port='COM7'):
    """查找占用指定串口的进程"""
    print(f"=" * 60)
    print(f"查找占用 {port} 的进程...")
    print(f"=" * 60)

    try:
        # 使用 handle.exe (Sysinternals) 如果可用
        # 或者使用 wmic 命令

        print(f"\n方法 1: 使用 PowerShell 查找...")
        ps_cmd = f'Get-Process | Where-Object {{$_.Modules.FileName -like "*{port}*"}}'

        # 简单方法：列出所有 Python 进程
        print(f"\n当前运行的 Python 进程:")
        print(f"-" * 60)

        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'TABLE'],
            capture_output=True,
            text=True,
            encoding='gbk'
        )

        if result.returncode == 0:
            print(result.stdout)

        result2 = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq pythonw.exe', '/FO', 'TABLE'],
            capture_output=True,
            text=True,
            encoding='gbk'
        )

        if result2.returncode == 0:
            print(result2.stdout)

        print(f"\n提示:")
        print(f"  1. 如果看到多个 python.exe 进程，其中一个可能占用了 {port}")
        print(f"  2. 关闭所有不需要的 Python 程序（包括 PyCharm 中的运行脚本）")
        print(f"  3. 或者直接重新插拔 USB 线（最简单有效）")

    except Exception as e:
        print(f"\n✗ 查找失败: {e}")
        print(f"\n建议:")
        print(f"  1. 打开任务管理器 (Ctrl+Shift+Esc)")
        print(f"  2. 切换到 '详细信息' 选项卡")
        print(f"  3. 查找所有 python.exe 和 pythonw.exe 进程")
        print(f"  4. 结束不需要的进程")

if __name__ == "__main__":
    print("\n这个工具会列出所有 Python 进程")
    print("占用 COM7 的进程很可能是其中之一\n")

    input("按回车键开始...")

    find_port_process('COM7')

    print(f"\n" + "=" * 60)
    print(f"最简单的解决方法：")
    print(f"  1. 重新插拔 USB 线")
    print(f"  2. 或者在任务管理器中结束所有 python.exe 进程")
    print(f"  3. 然后重新运行 main.py")
    print(f"=" * 60)

    input(f"\n按回车键退出...")
