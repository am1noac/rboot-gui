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

    # 连接配置
    with ui.card():
        ui.label('设备连接配置').classes('text-h6')
        with ui.row():
            ip_input = ui.input('IP地址', value='192.168.0.4').props('dense')
            port_input = ui.number('端口', value=3333, format='%d', min=1, max=65535).props('dense')
        with ui.row():
            ui.label('提示: 常用端口 3333, 4444, 5000, 6000, 8080, 9000').classes('text-caption')
        with ui.row():
            def test_port(p):
                port_input.value = p
                ui.notify(f'端口已设置为 {p}，请点击"连接设备"测试', type='info')
            ui.button('3333', on_click=lambda: test_port(3333)).props('dense flat size=sm')
            ui.button('4444', on_click=lambda: test_port(4444)).props('dense flat size=sm color=primary')
            ui.button('5000', on_click=lambda: test_port(5000)).props('dense flat size=sm')
            ui.button('6000', on_click=lambda: test_port(6000)).props('dense flat size=sm')
            ui.button('8080', on_click=lambda: test_port(8080)).props('dense flat size=sm')
            ui.button('9000', on_click=lambda: test_port(9000)).props('dense flat size=sm')
        ui.markdown('''
**如何判断端口正确？**
- ❌ 错误端口：大量 "UDP接收警告 (错误码 10054)"
- ✅ 正确端口：出现 "收到: AA XX XX ..." 日志

**查找正确端口的方法：**
1. 查看设备文档或配置界面
2. 使用 Wireshark 抓包查看设备通信端口
3. 逐个测试上面的常用端口
        ''').classes('text-caption bg-blue-50 p-2 rounded')

    container = ui.column()

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

            # 获取用户输入的IP和端口
            ip = ip_input.value
            port = int(port_input.value)

            status.set_text(f'连接中... ({ip}:{port})')
            print(f"\n=== 尝试连接到 {ip}:{port} ===")

            # 创建新连接
            client_instance = UDPClient(ip, port)

            if client_instance.connect():
                client_instance.start_receive_thread()
                status.set_text(f'已连接! ({ip}:{port})')

                # 显示控制界面
                container.clear()
                with container:
                    controls(client_instance)

                ui.notify(f'设备连接成功! {ip}:{port}', type='positive')
            else:
                status.set_text('连接失败')
                ui.notify(f'连接失败，请检查IP({ip})和端口({port})是否正确', type='negative')
                client_instance = None

        except Exception as e:
            status.set_text(f'错误: {str(e)}')
            ui.notify(f'连接错误: {str(e)}', type='negative')
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