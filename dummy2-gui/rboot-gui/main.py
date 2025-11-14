#!/usr/bin/env python3
import logging
import struct
import socket
import time
from threading import Thread
from nicegui import ui

logging.getLogger('nicegui').setLevel(logging.ERROR)
ui.colors(primary='#6e93d6')

# 全局客户端实例
client_instance = None
scan_running = False


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
1. 点击下方 "🔍 自动扫描端口" 按钮自动查找
2. 查看设备文档或配置界面
3. 使用 Wireshark 抓包查看设备通信端口
4. 逐个点击上面的常用端口测试
        ''').classes('text-caption bg-blue-50 p-2 rounded')

    # 端口扫描结果容器
    scan_result_container = ui.column().classes('w-full')

    def scan_single_port(ip, port, timeout=1.5):
        """扫描单个端口"""
        result = {
            'port': port,
            'sent': False,
            'received': False,
            'error': None,
            'response_data': None,
            'error_code': None
        }

        try:
            # 创建测试消息 - Get_Encoder_Estimates命令
            message = bytearray(12)
            message[0] = 0xbb  # 发送消息头
            message[1] = 1     # 电机ID 1
            message[2] = 9     # Get_Encoder_Estimates命令
            message[3:7] = struct.pack('<I', 0)
            message[7:11] = struct.pack('<I', 0)
            checksum = 0
            for byte in message[3:7]:
                checksum ^= byte
            message[11] = checksum

            # 创建socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(timeout)
            sock.bind(('0.0.0.0', 0))

            # Windows优化
            try:
                import platform
                if platform.system() == 'Windows':
                    import ctypes
                    SIO_UDP_CONNRESET = 0x9800000C
                    sock.ioctl(SIO_UDP_CONNRESET, False)
            except:
                pass

            # 发送并接收
            sock.sendto(bytes(message), (ip, port))
            result['sent'] = True

            try:
                data, addr = sock.recvfrom(1024)
                result['received'] = True
                result['response_data'] = ' '.join(f'{b:02X}' for b in data)
            except socket.timeout:
                result['error'] = 'timeout'
            except OSError as e:
                error_code = getattr(e, 'winerror', None) or getattr(e, 'errno', None)
                result['error'] = 'os_error'
                result['error_code'] = error_code

            sock.close()

        except Exception as e:
            result['error'] = str(e)

        return result

    def auto_scan_ports():
        """自动扫描常用端口"""
        global scan_running

        if scan_running:
            ui.notify('扫描正在进行中...', type='warning')
            return

        scan_running = True
        ip = ip_input.value

        # 定义要扫描的端口
        ports_to_scan = [3333, 4444, 5000, 6000, 7000, 8080, 9000, 10000,
                        502, 1883, 2404, 3000, 4000, 5555, 6666, 8888, 9999]

        scan_result_container.clear()

        with scan_result_container:
            with ui.card().classes('w-full'):
                ui.label('端口扫描进度').classes('text-h6')
                progress_label = ui.label(f'准备扫描 {len(ports_to_scan)} 个端口...')
                progress_bar = ui.linear_progress(value=0).props('instant-feedback')

                result_card = ui.card().classes('w-full mt-4')

        def scan_thread():
            global scan_running
            responded = []
            timeout_ports = []
            rejected = []

            for i, port in enumerate(ports_to_scan):
                progress = (i + 1) / len(ports_to_scan)
                progress_bar.set_value(progress)
                progress_label.set_text(f'扫描中... [{i+1}/{len(ports_to_scan)}] 测试端口 {port}')

                result = scan_single_port(ip, port)

                if result['received']:
                    responded.append((port, result['response_data']))
                elif result['error'] == 'timeout':
                    timeout_ports.append(port)
                elif result['error'] == 'os_error' and result['error_code'] in (10054, 10040):
                    rejected.append(port)

                time.sleep(0.1)  # 短暂延迟

            # 显示结果
            scan_running = False
            progress_label.set_text('✅ 扫描完成！')

            with result_card:
                ui.label('扫描结果').classes('text-h6')

                if responded:
                    ui.markdown('### ✅ 收到响应的端口（推荐使用）:').classes('text-positive')
                    for port, data in responded:
                        with ui.row():
                            ui.label(f'端口 {port}:').classes('font-bold')
                            ui.label(data[:50] + '...' if len(data) > 50 else data).classes('text-caption')
                            ui.button('使用此端口', on_click=lambda p=port: [
                                port_input.set_value(p),
                                ui.notify(f'已设置端口为 {p}，请点击"连接设备"', type='positive')
                            ]).props('dense color=positive')

                if timeout_ports:
                    ui.markdown('### ⏱️ 超时的端口（可能需要尝试）:').classes('text-warning')
                    with ui.row():
                        for port in timeout_ports[:10]:
                            ui.button(str(port), on_click=lambda p=port: [
                                port_input.set_value(p),
                                ui.notify(f'已设置端口为 {p}，请点击"连接设备"测试', type='info')
                            ]).props('dense flat')

                if not responded and not timeout_ports:
                    ui.markdown('### ❌ 未找到有效端口').classes('text-negative')
                    ui.markdown('''
**建议：**
1. 检查设备IP地址是否正确
2. 确认设备已开机并联网
3. 查看设备文档获取正确端口
4. 使用Wireshark抓包分析
                    ''').classes('text-caption')

                if rejected:
                    with ui.expansion(f'被拒绝的端口 ({len(rejected)}个)', icon='block').classes('w-full'):
                        ui.label(', '.join(map(str, rejected[:20]))).classes('text-caption')

        # 在后台线程中运行扫描
        Thread(target=scan_thread, daemon=True).start()
        ui.notify(f'开始扫描 {ip} 的端口...', type='info')

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
        ui.separator().props('vertical')
        ui.button('🔍 自动扫描端口', on_click=auto_scan_ports, color='orange').props('outline')

    # 初始内容
    with container:
        ui.markdown('请点击"连接设备"按钮')


if __name__ == "__main__":
    create_ui()
    ui.run(title='Rboot GUI', reload=False, host='127.0.0.1', port=8080, show=True)