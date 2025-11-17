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

        # 连接模式选择
        connection_mode = ui.select(
            label='连接模式',
            options=['UDP网络', 'USB串口(CAN协议)', 'USB串口(文本协议)'],
            value='USB串口(文本协议)',
            on_change=lambda: toggle_config()
        ).tooltip('文本协议适用于使用!START、&angle命令的设备')

        # 文本协议初始化模式选择
        init_mode_row = ui.row()
        with init_mode_row:
            init_mode = ui.select(
                label='初始化模式',
                options=['示教模式(仅HOME,可手动移动)', '正常模式(START+HOME,电机使能)'],
                value='示教模式(仅HOME,可手动移动)'
            ).tooltip('示教模式: 仅发送!HOME，电机失能，可手动移动\n正常模式: 发送!START+!HOME，电机使能，无法手动移动')

        # UDP配置
        udp_config = ui.row()
        with udp_config:
            ip_input = ui.input('设备IP地址', value='192.168.0.88', placeholder='192.168.0.88')
            port_input = ui.number('端口', value=9999, format='%d', min=1, max=65535)

        # 串口配置（默认显示）
        serial_config = ui.row()
        with serial_config:
            port_select = ui.select(
                label='串口',
                options=['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'COM10'],
                value='COM7'
            )
            baudrate_input = ui.number('波特率', value=9600, format='%d').tooltip('文本协议通常使用9600，CAN协议使用115200')

        # 模式切换逻辑
        def toggle_config():
            if connection_mode.value == 'UDP网络':
                udp_config.set_visibility(True)
                serial_config.set_visibility(False)
                init_mode_row.set_visibility(False)
            elif 'CAN协议' in connection_mode.value:
                udp_config.set_visibility(False)
                serial_config.set_visibility(True)
                init_mode_row.set_visibility(False)
                baudrate_input.set_value(115200)  # CAN协议使用115200
            else:  # 文本协议
                udp_config.set_visibility(False)
                serial_config.set_visibility(True)
                init_mode_row.set_visibility(True)  # 显示初始化模式选项
                baudrate_input.set_value(9600)  # 文本协议使用9600

        # 初始化时调用一次，设置正确的显示状态
        toggle_config()

    def connect_device():
        global client_instance

        try:
            # 如果已有连接，先关闭
            if client_instance:
                try:
                    client_instance.close()
                except:
                    pass
                client_instance = None

            status.set_text('连接中...')

            print("="*50)
            print("开始连接设备")

            # 根据选择的模式连接
            if connection_mode.value == 'UDP网络':
                from udpclient import UDPClient
                from controls import controls

                target_ip = ip_input.value
                target_port = int(port_input.value)

                print(f"连接模式: UDP网络")
                print(f"目标地址: {target_ip}:{target_port}")
                print("="*50)

                client_instance = UDPClient(target_ip, target_port)
                control_ui = controls

            elif 'CAN协议' in connection_mode.value:
                from serialclient import SerialClient
                from controls import controls

                target_port = port_select.value
                target_baudrate = int(baudrate_input.value)

                print(f"连接模式: USB串口 (CAN协议)")
                print(f"串口: {target_port}")
                print(f"波特率: {target_baudrate}")
                print("="*50)

                client_instance = SerialClient(port=target_port, baudrate=target_baudrate)
                control_ui = controls

            else:  # 文本协议模式
                from textserialclient import TextSerialClient
                from text_controls import text_controls

                target_port = port_select.value
                target_baudrate = int(baudrate_input.value)
                # 判断是否为示教模式
                is_teaching_mode = '示教模式' in init_mode.value

                print(f"连接模式: USB串口 (文本协议)")
                print(f"串口: {target_port}")
                print(f"波特率: {target_baudrate}")
                print(f"协议: ASCII文本 (!START, &angles)")
                print(f"初始化: {init_mode.value}")
                print("="*50)

                client_instance = TextSerialClient(
                    port=target_port,
                    baudrate=target_baudrate,
                    teaching_mode=is_teaching_mode
                )
                control_ui = text_controls

            # 连接设备
            if client_instance.connect():
                client_instance.start_receive_thread()
                status.set_text('已连接!')

                print("\n✓ 设备连接成功！")

                if connection_mode.value == 'USB串口(文本协议)':
                    print("提示: 文本协议设备已初始化 (!START, !HOME 已发送)\n")
                else:
                    print("提示: 请点击界面上的 '连接CAN总线' 按钮\n")

                # 显示对应的控制界面
                container.clear()
                with container:
                    control_ui(client_instance)

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