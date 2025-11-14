#!/usr/bin/env python3
import logging
from nicegui import ui

logging.getLogger('nicegui').setLevel(logging.ERROR)
ui.colors(primary='#6e93d6')

# 全局客户端实例
client_instance = None
connection_mode = {'type': 'serial'}  # 默认使用串口模式


def create_ui():
    ui.markdown('# Rboot GUI')

    status = ui.label('状态: 准备连接')

    # 连接模式选择
    with ui.row().classes('items-center'):
        ui.label('连接模式:')
        mode_toggle = ui.toggle(
            {'serial': '串口 (USB)', 'udp': '网络 (UDP)'},
            value='serial'
        ).bind_value(connection_mode, 'type')
        ui.label('').bind_text_from(
            connection_mode, 'type',
            backward=lambda x: f'当前: {"串口模式 (COM端口)" if x == "serial" else "网络模式 (192.168.0.4:3333)"}'
        )

    container = ui.column()

    def connect_device():
        global client_instance

        try:
            from controls import controls
            import time

            # 如果已有连接，先关闭
            if client_instance:
                try:
                    status.set_text('正在关闭旧连接...')
                    client_instance.close()
                    time.sleep(0.5)  # 等待完全关闭
                except Exception as e:
                    print(f"关闭旧连接时出错: {e}")
                finally:
                    client_instance = None

            status.set_text('正在连接设备...')
            print("\n" + "="*50)
            print("开始连接设备")

            # 根据连接模式选择客户端
            if connection_mode['type'] == 'serial':
                # 串口模式
                from serialclient import SerialClient
                print(f"连接模式: 串口 (USB)")
                print(f"波特率: 115200")
                print("="*50 + "\n")

                # 创建串口连接 (自动检测端口)
                client_instance = SerialClient(port=None, baudrate=115200)
                # 如果要指定端口，取消下面的注释：
                # client_instance = SerialClient(port='COM7', baudrate=115200)

            else:
                # UDP网络模式
                from udpclient import UDPClient
                print(f"连接模式: UDP网络")
                print(f"目标地址: 192.168.0.4:3333")
                print("="*50 + "\n")

                # 创建UDP连接
                client_instance = UDPClient('192.168.0.4', 3333)

            # 尝试连接
            if client_instance.connect():
                # 启动接收线程
                client_instance.start_receive_thread()
                time.sleep(0.3)  # 等待接收线程启动

                if connection_mode['type'] == 'serial':
                    status.set_text('✓ 串口已连接!')
                else:
                    status.set_text('✓ 网络已连接!')

                # 显示控制界面
                container.clear()
                with container:
                    controls(client_instance)

                ui.notify('设备连接成功! 请点击"连接CAN总线"按钮', type='positive')
                print("\n✓ 设备连接成功！")
                print("提示: 请点击界面上的 '连接CAN总线' 按钮\n")

            else:
                status.set_text('✗ 连接失败')

                if connection_mode['type'] == 'serial':
                    ui.notify('串口连接失败！请检查:\n1. USB线是否连接\n2. 设备驱动是否安装\n3. 端口是否被占用', type='negative')
                    print("\n✗ 连接失败！\n")
                    print("故障排除:")
                    print("1. 检查USB线是否连接")
                    print("2. 检查设备驱动是否正确安装")
                    print("3. 关闭其他可能占用串口的程序")
                    print("4. 尝试重新插拔USB线")
                    print("5. 运行: python serialclient.py 查看可用端口\n")
                else:
                    ui.notify('网络连接失败！请检查:\n1. 设备是否开机\n2. 网络线是否连接\n3. IP地址是否正确(192.168.0.4)', type='negative')
                    print("\n✗ 连接失败！\n")
                    print("故障排除:")
                    print("1. 检查设备是否开机")
                    print("2. 检查网络线是否连接")
                    print("3. 检查IP地址是否正确 (应该是 192.168.0.4)")
                    print("4. 尝试 ping 192.168.0.4 测试网络连通性\n")

                client_instance = None

        except ImportError as e:
            status.set_text(f'✗ 缺少依赖库')
            error_msg = str(e)
            if 'serial' in error_msg.lower():
                ui.notify('缺少pyserial库！请安装: pip install pyserial', type='negative')
                print("\n✗ 缺少pyserial库！")
                print("请运行: pip install pyserial\n")
            else:
                ui.notify(f'导入错误: {error_msg}', type='negative')
            client_instance = None

        except Exception as e:
            status.set_text(f'✗ 错误: {str(e)}')
            ui.notify(f'连接错误: {str(e)}', type='negative')
            client_instance = None
            print(f"\n✗ 连接错误: {e}\n")

    def disconnect_device():
        global client_instance
        if client_instance:
            client_instance.close()
            client_instance = None
            status.set_text('已断开连接')
            container.clear()
            with container:
                ui.markdown('连接已断开')
            ui.notify('设备已断开')

    # 连接管理按钮
    with ui.row():
        ui.button('连接设备', on_click=connect_device, icon='link')
        ui.button('断开连接', on_click=disconnect_device, icon='link_off')
        ui.button('重新连接', on_click=lambda: [disconnect_device(), connect_device()], icon='refresh')

    # 初始内容
    with container:
        ui.markdown('请点击"连接设备"按钮')


if __name__ == "__main__":
    create_ui()
    ui.run(title='Rboot GUI', reload=False, host='127.0.0.1', port=8080, show=True)