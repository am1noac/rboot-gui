#!/usr/bin/env python3
import logging
from nicegui import ui

logging.getLogger('nicegui').setLevel(logging.ERROR)
ui.colors(primary='#6e93d6')

# 全局客户端实例
client_instance = None


def create_ui():
    ui.markdown('# Rboot GUI')

    status = ui.label('状态: 准备连接')
    container = ui.column()

    # 连接配置输入框
    with ui.card().classes('w-full'):
        ui.markdown('### 设备连接配置')
        with ui.row():
            ip_input = ui.input('设备IP地址', value='192.168.0.88', placeholder='192.168.0.88')
            port_input = ui.number('端口', value=9999, format='%d', min=1, max=65535)

    def connect_device():
        global client_instance

        try:
            from udpclient import UDPClient
            from controls import controls

            # 如果已有连接，先关闭
            if client_instance:
                try:
                    client_instance.close()
                except:
                    pass
                client_instance = None

            status.set_text('连接中...')

            # 使用用户输入的IP和端口
            target_ip = ip_input.value
            target_port = int(port_input.value)

            print("="*50)
            print("开始连接设备")
            print(f"连接模式: UDP网络")
            print(f"目标地址: {target_ip}:{target_port}")
            print("="*50)

            # 创建新连接
            client_instance = UDPClient(target_ip, target_port)

            if client_instance.connect():
                client_instance.start_receive_thread()
                status.set_text('已连接!')

                print("\n✓ 设备连接成功！")
                print("提示: 请点击界面上的 '连接CAN总线' 按钮\n")

                # 显示控制界面
                container.clear()
                with container:
                    controls(client_instance)

                ui.notify('设备连接成功!')
            else:
                status.set_text('连接失败')
                ui.notify('连接失败，请检查设备状态')
                client_instance = None

        except Exception as e:
            status.set_text(f'错误: {str(e)}')
            ui.notify(f'连接错误: {str(e)}')
            client_instance = None

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