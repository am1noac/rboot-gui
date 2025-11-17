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
    for device in odrive.connected_devices:
        if device.serial_number not in devices:
            print(f'Adding Rdrive {device.serial_number:x}')
            with container:
                with ui.column() as devices[device.serial_number]:
                    controls(device)
    for serial_number in list(devices):
        if not any(d.serial_number == serial_number for d in odrive.connected_devices):
            print(f'Removing Rdrive {serial_number:x}')
            container.remove(devices.pop(serial_number))

# 启动设备发现
print("Starting ODrive device discovery...")
odrive.start_discovery(odrive.default_usb_search_path)

# 使用定时器定期检查设备（每1秒检查一次）
ui.timer(1.0, check_devices)

ui.run(title='Rdrive Motor Tuning')
