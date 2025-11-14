# USB串口通信故障排查指南

## 问题描述

运行程序时出现以下错误：
- "发送超时"
- "未连接,无法发送消息"
- 网页数据不更新

## 已修复的问题

### 1. 串口超时设置
- **问题**: 写入超时1秒太短
- **修复**: 增加到3秒
- **位置**: `serialclient.py:46`

### 2. 数据接收逻辑
- **问题**: 未处理分段接收的情况
- **修复**: 添加了缓冲区和消息头查找逻辑
- **位置**: `serialclient.py:140-199`

### 3. 连接稳定性
- **问题**: 发送失败后立即断开连接
- **修复**: 增加重试次数，失败后保持连接
- **位置**: `serialclient.py:86-138`

## 使用方法

### 1. 更新代码
```bash
cd /path/to/rboot-gui
git pull origin claude/fix-usb-arm-communication-01WGwxn1PfVKqVFUMoxqf6V4
```

### 2. 确认依赖
```bash
pip install pyserial
```

### 3. 运行程序
```bash
python dummy2-gui/rboot-gui/main.py
```

## 检查项目

### 1. 确认COM端口
在Windows设备管理器中确认机械臂连接的端口：
- 打开"设备管理器"
- 查看"端口(COM和LPT)"
- 找到机械臂对应的COM端口（如COM7、COM8等）

如果不是COM7，请修改 `main.py` 第36行：
```python
client_instance = SerialClient('COM7', 115200)
```
改为实际的端口号。

### 2. 检查串口波特率
确认机械臂的波特率设置：
- 默认：115200
- 如果机械臂使用其他波特率，修改 `main.py` 第36行：
```python
client_instance = SerialClient('COM7', 9600)  # 或其他波特率
```

### 3. 检查串口驱动
确保已安装正确的USB串口驱动：
- CH340/CH341驱动（常见）
- FTDI驱动
- CP210x驱动

### 4. 检查串口占用
确保COM端口没有被其他程序占用：
```bash
# Windows: 在设备管理器中查看端口状态
# 关闭可能占用端口的程序（如串口调试助手、Arduino IDE等）
```

## 调试方法

### 1. 启用详细日志
修改 `serialclient.py` 第113行：
```python
# 改为始终打印发送日志
hex_msg = ' '.join(f'{b:02X}' for b in message)
print(f"发送: {hex_msg}")
```

### 2. 测试串口连接
创建测试脚本 `test_serial.py`：
```python
import serial
import time

try:
    ser = serial.Serial('COM7', 115200, timeout=1)
    print(f"串口已打开: {ser.name}")
    print(f"波特率: {ser.baudrate}")

    # 发送测试数据
    test_data = b'\xbb\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    ser.write(test_data)
    print(f"已发送: {' '.join(f'{b:02X}' for b in test_data)}")

    # 等待响应
    time.sleep(0.5)
    if ser.in_waiting > 0:
        response = ser.read(ser.in_waiting)
        print(f"收到: {' '.join(f'{b:02X}' for b in response)}")
    else:
        print("未收到响应")

    ser.close()
except Exception as e:
    print(f"错误: {e}")
```

运行：
```bash
python test_serial.py
```

### 3. 检查机械臂状态
- 确认机械臂已上电
- 检查USB线缆连接是否良好
- 尝试更换USB端口
- 尝试更换USB线缆

## 常见错误及解决方法

### 错误1: "串口连接失败: could not open port 'COM7'"
**原因**: 端口不存在或被占用
**解决**:
1. 检查设备管理器中的实际端口号
2. 关闭占用端口的程序
3. 重新插拔USB线

### 错误2: "发送超时"
**原因**: 机械臂未响应或波特率不匹配
**解决**:
1. 确认波特率设置正确
2. 检查机械臂固件状态
3. 尝试降低通信频率

### 错误3: "未连接,无法发送消息"
**原因**: 连接状态异常
**解决**:
1. 点击"断开连接"后重新连接
2. 重启GUI程序
3. 重新插拔USB线

### 错误4: 数据不更新
**原因**: 机械臂未发送数据或数据格式不匹配
**解决**:
1. 检查是否收到数据（查看控制台"收到:"日志）
2. 确认消息格式正确（12字节，以0xbb开头）
3. 检查controls.py中的数据解析逻辑

## 获取支持

如果问题仍未解决：
1. 记录完整的错误日志
2. 检查机械臂的技术文档
3. 确认通信协议版本
4. 联系机械臂供应商获取技术支持

## 参考信息

- 消息格式: 12字节
- 消息头: 0xbb
- 默认波特率: 115200
- 数据位: 8
- 停止位: 1
- 校验位: 无
