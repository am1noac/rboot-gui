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
        status_label = ui.label('已连接 - 设备已初始化 (!START, !HOME 已发送)')
        status_label.style('color: #03fc1c; font-weight: bold')

        ui.label('提示: 此设备使用文本协议，!START 后电机使能（锁定），无法手动移动')

    # 设备控制按钮
    with ui.card().classes('w-full'):
        ui.markdown('### 设备控制')

        def send_home():
            """发送HOME命令"""
            if client.send_text_command("!HOME"):
                ui.notify('已发送 !HOME 命令', type='info')
                status_label.set_text('状态: HOME - 机械臂展开')
            else:
                ui.notify('发送失败', type='negative')

        def send_start():
            """发送START命令"""
            if client.send_text_command("!START"):
                ui.notify('已发送 !START 命令 - 机械臂已使能', type='positive')
                status_label.set_text('状态: 已使能 - 可以接收位置命令')
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
            ui.button('发送 !HOME', on_click=send_home, icon='home') \
                .tooltip('展开机械臂（可能取消使能）')
            ui.button('发送 !START', on_click=send_start, icon='play_arrow') \
                .tooltip('使能机械臂（电机锁定）')

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
        ui.markdown('### 示教模式（自动记录）')

        teaching_status = ui.label('示教模式: 未启用')
        teaching_status.style('color: #fc0320; font-weight: bold')

        ui.markdown('''
**使用说明：**
1. 点击"启用示教模式"（发送 !DISABLE 失能电机）
2. 手动移动机械臂到目标位置
3. 点击"读取并记录位置"（自动发送 #GETJPOS 读取）
4. 重复步骤 2-3 记录多个位置
5. 点击"播放动作序列"执行
        ''')

        def enable_teaching():
            """启用示教模式 - 失能电机"""
            if client.disable_motors():  # 发送 !DISABLE
                teaching_status.set_text('示教模式: 已启用 - 可以手动移动机械臂')
                teaching_status.style('color: #03fc1c; font-weight: bold')
                ui.notify('示教模式已启用！现在可以手动移动机械臂', type='positive')
            else:
                ui.notify('启用失败', type='negative')

        def disable_teaching():
            """禁用示教模式 - 重新使能电机"""
            if client.send_text_command("!START"):
                teaching_status.set_text('示教模式: 未启用')
                teaching_status.style('color: #fc0320; font-weight: bold')
                ui.notify('示教模式已禁用，电机已使能', type='warning')
            else:
                ui.notify('禁用失败', type='negative')

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
                update_positions_list()
            else:
                ui.notify('读取位置失败', type='negative')

        with ui.row().classes('w-full'):
            ui.button('启用示教模式', on_click=enable_teaching, icon='pan_tool', color='positive') \
                .tooltip('发送 !DISABLE - 失能电机，可手动移动')
            ui.button('禁用示教模式', on_click=disable_teaching, icon='lock', color='warning') \
                .tooltip('发送 !START - 重新使能电机')
            ui.button('读取并记录位置', on_click=read_and_record, icon='add_location', color='primary') \
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
