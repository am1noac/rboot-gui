#!/usr/bin/env python3
import asyncio
import logging

import odrive
from nicegui import app, ui

from controls import controls

logging.getLogger('nicegui').setLevel(logging.ERROR)

ui.colors(primary='#6e93d6')

devices: dict[int, ui.element] = {}

ui.markdown('## Rdrive Motor Tuning GUI')
ui.markdown('Waiting for Rdrive devices to be connected...').bind_visibility_from(globals(), 'devices', lambda d: not d)
container = ui.row()

def check_devices() -> None:
    """定期检查设备连接状态"""
    try:
        # 尝试查找新连接的设备
        found_devices = []
        try:
            # 方法1: 使用find_any查找设备
            device = odrive.find_any(timeout=0.5)
            if device:
                found_devices.append(device)
        except:
            pass

        # 添加新设备到界面
        for device in found_devices:
            if hasattr(device, 'serial_number'):
                serial = device.serial_number
                if serial not in devices:
                    print(f'Adding Rdrive {serial:x}')
                    with container:
                        with ui.column() as devices[serial]:
                            controls(device)

        # 移除断开连接的设备
        for serial_number in list(devices):
            # 检查设备是否仍然连接
            still_connected = False
            for device in found_devices:
                if hasattr(device, 'serial_number') and device.serial_number == serial_number:
                    still_connected = True
                    break

            if not still_connected:
                print(f'Removing Rdrive {serial_number:x}')
                container.remove(devices.pop(serial_number))
    except Exception as e:
        print(f'Device discovery error: {e}')

# 启动设备发现
print("Starting ODrive device discovery...")
print("Waiting for ODrive devices to be connected via USB...")

# 使用定时器定期检查设备（每1秒检查一次）
ui.timer(1.0, check_devices)

ui.run(title='Rdrive Motor Tuning')
