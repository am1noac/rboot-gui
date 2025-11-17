#!/usr/bin/env python3
"""
文本协议设备控制界面
专为使用 !START, !HOME, &angles 命令的设备设计
"""

from nicegui import ui
import json

# 全局变量
teaching_positions = []


def text_controls(client):
    """文本协议设备的控制界面"""

    ui.markdown('## 文本协议机械臂控制')

    # 状态显示
    with ui.card().classes('w-full'):
        ui.markdown('### 设备状态')

        # 根据实际初始化状态显示
        if client.initialized:
            status_label = ui.label('已连接 - 设备已初始化 (!START, !HOME 已发送)')
            status_label.style('color: #03fc1c; font-weight: bold')
        else:
            status_label = ui.label('已连接 - 手动模式（未初始化，可手动移动）')
            status_label.style('color: #FFA500; font-weight: bold')

        ui.label('提示: 手动模式下可以移动机械臂，点击"读取并记录位置"读取当前角度')

    # 设备控制按钮
    with ui.card().classes('w-full'):
        ui.markdown('### 设备控制')

        def init_device():
            """初始化设备 - 发送 !START + !HOME"""
            if client.initialize_device():
                ui.notify('✓ 设备初始化完成 (!START + !HOME)', type='positive')
                status_label.set_text('状态: 已初始化 - 电机使能，可接收命令')
                status_label.style('color: #03fc1c; font-weight: bold')
            else:
                ui.notify('初始化失败', type='negative')

        def send_home():
            """发送HOME命令"""
            if client.send_text_command("!HOME"):
                ui.notify('已发送 !HOME 命令', type='info')
            else:
                ui.notify('发送失败', type='negative')

        def send_start():
            """发送START命令"""
            if client.send_text_command("!START"):
                ui.notify('已发送 !START 命令 - 机械臂已使能', type='positive')
            else:
                ui.notify('发送失败', type='negative')

        def send_custom_command():
            """发送自定义命令"""
            custom_cmd = custom_input.value.strip()
            if not custom_cmd:
                ui.notify('请输入命令', type='warning')
                return

            if client.send_text_command(custom_cmd):
                ui.notify(f'已发送: {custom_cmd}', type='info')
            else:
                ui.notify('发送失败', type='negative')

        with ui.row().classes('w-full'):
            ui.button('初始化设备', on_click=init_device, icon='play_circle', color='primary') \
                .tooltip('发送 !START + !HOME (使能并展开)')
            ui.button('发送 !START', on_click=send_start, icon='play_arrow') \
                .tooltip('使能机械臂（电机锁定）')
            ui.button('发送 !HOME', on_click=send_home, icon='home') \
                .tooltip('展开机械臂')

        with ui.row().classes('w-full'):
            custom_input = ui.input('自定义命令', placeholder='例如: !STOP').classes('flex-grow')
            ui.button('发送', on_click=send_custom_command, icon='send')

    # 位置控制
    with ui.card().classes('w-full'):
        ui.markdown('### 位置控制')
        ui.label('设置关节角度并发送位置命令（格式：&J1,J2,J3,J4,J5,J6,）')

        # 6个关节角度输入
        angles = {}
        with ui.grid(columns=3).classes('w-full gap-4'):
            for i in range(1, 7):
                with ui.column():
                    angles[f'J{i}'] = ui.number(
                        f'J{i} (度)',
                        value=0,
                        format='%.2f',
                        min=-180,
                        max=180
                    )

        def send_position():
            """发送位置命令"""
            angle_values = [angles[f'J{i}'].value for i in range(1, 7)]

            if client.send_position(angle_values):
                ui.notify(f'位置已发送: {angle_values}', type='positive')
            else:
                ui.notify('发送失败', type='negative')

        def send_home_position():
            """发送零位"""
            for i in range(1, 7):
                angles[f'J{i}'].set_value(0)
            send_position()

        with ui.row().classes('w-full'):
            ui.button('发送位置', on_click=send_position, icon='send', color='primary')
            ui.button('归零', on_click=send_home_position, icon='home')

    # 示教功能
    with ui.card().classes('w-full'):
        ui.markdown('### 示教模式（位置记录）')

        teaching_status = ui.label('提示: 设备上电后默认可以手动移动')
        teaching_status.style('color: #888; font-weight: bold')

        # 实时位置显示
        position_display = ui.label('当前位置: (未读取)')
        position_display.style('color: #666; font-family: monospace')

        ui.markdown('''
**示教流程：**
1. **确保未发送初始化命令**（选择"手动模式"连接）
2. 点击"启动位置监控"开始实时显示位置
3. **手动移动**机械臂到目标位置（观察实时位置）
4. 点击"读取并记录位置"保存当前位置
5. 重复步骤 3-4 记录多个位置
6. 记录完成后，点击"初始化设备"按钮使能电机
7. 点击"播放动作序列"执行录制的动作

**注意：** 此设备不支持 !DISABLE 命令，无法在使能后再失能。
因此必须在连接时选择"手动模式"以保持可移动状态。
        ''')

        # 位置监控定时器
        position_timer = None
        monitoring = False

        def update_position_display():
            """更新位置显示"""
            current_pos = client.get_current_position()
            if current_pos:
                # 更新角度输入框
                for i in range(1, 7):
                    angles[f'J{i}'].set_value(current_pos[i-1])
                # 更新显示
                pos_str = f"当前位置: J1={current_pos[0]:.1f}° J2={current_pos[1]:.1f}° J3={current_pos[2]:.1f}° J4={current_pos[3]:.1f}° J5={current_pos[4]:.1f}° J6={current_pos[5]:.1f}°"
                position_display.set_text(pos_str)
                position_display.style('color: #03fc1c; font-family: monospace; font-weight: bold')

        def toggle_monitoring():
            """切换位置监控"""
            nonlocal position_timer, monitoring

            if not monitoring:
                # 启动监控
                position_timer = ui.timer(1.0, update_position_display)  # 每1秒更新
                monitoring = True
                monitor_btn.set_text('停止位置监控')
                monitor_btn.props('color=negative')
                teaching_status.set_text('位置监控: 已启动')
                teaching_status.style('color: #03fc1c; font-weight: bold')
                ui.notify('位置监控已启动，每秒自动读取位置', type='positive')
            else:
                # 停止监控
                if position_timer:
                    position_timer.cancel()
                    position_timer = None
                monitoring = False
                monitor_btn.set_text('启动位置监控')
                monitor_btn.props('color=primary')
                teaching_status.set_text('位置监控: 已停止')
                teaching_status.style('color: #888; font-weight: bold')
                ui.notify('位置监控已停止', type='info')

        def read_and_record():
            """读取当前位置并记录"""
            current_pos = client.get_current_position()  # 发送 #GETJPOS

            if current_pos:
                # 更新UI显示
                for i in range(1, 7):
                    angles[f'J{i}'].set_value(current_pos[i-1])

                # 记录位置
                teaching_positions.append(current_pos.copy())
                ui.notify(f'✓ 已记录位置 #{len(teaching_positions)}: J1={current_pos[0]:.1f}°, J2={current_pos[1]:.1f}°, J3={current_pos[2]:.1f}°', type='positive')
                teaching_status.set_text(f'已记录 {len(teaching_positions)} 个位置')
                teaching_status.style('color: #03fc1c; font-weight: bold')
                update_positions_list()
            else:
                ui.notify('读取位置失败', type='negative')

        with ui.row().classes('w-full'):
            monitor_btn = ui.button('启动位置监控', on_click=toggle_monitoring, icon='visibility', color='primary') \
                .tooltip('每秒自动读取并显示当前位置')
            ui.button('读取并记录位置', on_click=read_and_record, icon='add_location', color='positive') \
                .tooltip('发送 #GETJPOS 读取当前位置并保存')

        positions_container = ui.column().classes('w-full')

        def record_position():
            """手动记录当前位置（从输入框）"""
            angle_values = [angles[f'J{i}'].value for i in range(1, 7)]
            teaching_positions.append(angle_values.copy())
            ui.notify(f'已记录位置 #{len(teaching_positions)}: {angle_values}', type='positive')
            update_positions_list()

        def clear_positions():
            """清空所有位置"""
            teaching_positions.clear()
            ui.notify('已清空所有位置', type='info')
            update_positions_list()

        def play_sequence():
            """播放动作序列"""
            if not teaching_positions:
                ui.notify('没有记录的位置', type='warning')
                return

            # 先发送START确保使能
            client.send_text_command("!START")
            ui.notify(f'开始播放 {len(teaching_positions)} 个动作...', type='info')

            import time
            for i, pos in enumerate(teaching_positions):
                ui.notify(f'执行动作 {i+1}/{len(teaching_positions)}', type='info')
                client.send_position(pos)
                time.sleep(1.5)  # 等待动作完成

            ui.notify('动作序列播放完成', type='positive')

        def save_sequence():
            """保存动作序列到文件"""
            if not teaching_positions:
                ui.notify('没有可保存的位置', type='warning')
                return

            filename = 'teaching_sequence.json'
            with open(filename, 'w') as f:
                json.dump(teaching_positions, f, indent=2)
            ui.notify(f'已保存到 {filename}', type='positive')

        def load_sequence():
            """从文件加载动作序列"""
            try:
                filename = 'teaching_sequence.json'
                with open(filename, 'r') as f:
                    loaded = json.load(f)
                teaching_positions.clear()
                teaching_positions.extend(loaded)
                ui.notify(f'已加载 {len(teaching_positions)} 个位置', type='positive')
                update_positions_list()
            except FileNotFoundError:
                ui.notify('文件不存在', type='negative')
            except Exception as e:
                ui.notify(f'加载失败: {e}', type='negative')

        def update_positions_list():
            """更新位置列表显示"""
            positions_container.clear()
            with positions_container:
                if not teaching_positions:
                    ui.label('(暂无记录的位置)')
                else:
                    for i, pos in enumerate(teaching_positions):
                        with ui.card().classes('w-full'):
                            ui.label(f'位置 {i+1}: J1={pos[0]:.1f}°, J2={pos[1]:.1f}°, J3={pos[2]:.1f}°, J4={pos[3]:.1f}°, J5={pos[4]:.1f}°, J6={pos[5]:.1f}°')

        with ui.row().classes('w-full'):
            ui.button('记录当前位置', on_click=record_position, icon='add_location', color='positive')
            ui.button('清空位置', on_click=clear_positions, icon='delete', color='negative')

        with ui.row().classes('w-full'):
            ui.button('播放动作序列', on_click=play_sequence, icon='play_arrow', color='primary')
            ui.button('保存序列', on_click=save_sequence, icon='save')
            ui.button('加载序列', on_click=load_sequence, icon='folder_open')

        update_positions_list()

    # 调试信息
    with ui.card().classes('w-full'):
        ui.markdown('### 调试信息')
        ui.markdown('''
**文本协议说明：**
- `!HOME` - 展开机械臂（可能取消使能）
- `!START` - 使能机械臂（电机锁定，可接收命令）
- `&J1,J2,J3,J4,J5,J6,` - 发送位置命令

**示教流程：**
1. 如果需要手动移动，先测试发送 `!HOME` 看能否取消使能
2. 手动移动机械臂到位置，手动输入角度值
3. 记录多个位置
4. 播放时会自动发送 `!START` 然后执行序列
        ''')
