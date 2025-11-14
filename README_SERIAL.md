# Rboot GUI - 串口模式使用指南

## 概述

Rboot GUI现在支持两种连接模式:
- **串口模式 (USB)** - 通过USB直连dummy机械臂 ✨ 新增
- **网络模式 (UDP)** - 通过以太网连接

## 快速开始

### 1. 安装依赖

```bash
cd dummy2-gui
pip install -r requirements.txt
```

主要依赖:
- `pyserial>=3.5` - 串口通信库
- `nicegui>=1.3.13` - Web界面框架

### 2. 连接设备

#### 串口模式 (推荐用于USB直连)

```bash
cd rboot-gui
python main.py
```

1. 选择连接模式: **串口 (USB)**
2. 点击"连接设备"按钮
3. 程序会自动检测可用的串口并连接
4. 看到"✓ 串口已连接!"后，点击"连接CAN总线"按钮

#### 网络模式 (用于以太网连接)

1. 选择连接模式: **网络 (UDP)**
2. 点击"连接设备"按钮
3. 程序会连接到192.168.0.4:3333
4. 看到"✓ 网络已连接!"后，点击"连接CAN总线"按钮

### 3. 控制机械臂

连接成功后，您可以:
- 查看各关节状态 (位置、速度、电流等)
- 发送位置/速度命令
- 示教编程
- 运动序列控制

## 故障排除

### 串口连接失败

**症状**: 点击连接按钮后显示"serial.open()超时"

**解决方案**:

1. **运行诊断工具**
   ```bash
   python reset_port.py list  # 列出所有可用串口
   ```

2. **检查端口占用**
   - Windows: 打开设备管理器，查看"端口(COM和LPT)"
   - Linux: 运行 `ls -l /dev/ttyUSB*`

3. **Linux权限问题**
   ```bash
   sudo usermod -a -G dialout $USER
   # 需要重新登录
   ```

4. **重置串口**
   ```bash
   python reset_port.py reset COM7  # Windows
   python reset_port.py reset /dev/ttyUSB0  # Linux
   ```

5. **重新插拔USB线**

### CAN总线通信超时

**症状**: 连接成功但发送命令一直超时

**原因**: 发送速度过快，设备来不及响应

**已修复**: 程序已优化发送间隔为20ms，适配115200波特率

如果仍有问题，查看完整的故障排除指南:
```bash
cat ../TROUBLESHOOTING.md
```

## 技术细节

### 串口配置

| 参数 | 值 |
|------|-----|
| 波特率 | 115200 |
| 数据位 | 8 |
| 校验位 | 无 |
| 停止位 | 1 |
| 流控制 | 无 |

### 消息格式

串口和UDP使用相同的CAN消息格式:

```
消息结构 (12字节):
[0]    Header  (0xBB)
[1]    ID      (CAN节点ID)
[2]    CMD     (命令类型)
[3-6]  Body1   (数据1, 4字节)
[7-10] Body2   (数据2, 4字节)
[11]   Checksum (校验和)
```

### 发送速率控制

- **发送间隔**: 20ms
- **理论最大速率**: 50条/秒
- **实际速率**: ~40条/秒 (考虑延迟)
- **重试次数**: 3次
- **重试延迟**: 50ms, 100ms, 200ms (递增)

## 常用命令

### 诊断工具

```bash
# 串口诊断
python reset_port.py                    # 自动诊断
python reset_port.py list              # 列出所有串口
python reset_port.py test COM7         # 测试指定串口
python reset_port.py reset COM7        # 重置串口

# 网络诊断
python reset_network.py                # 自动诊断
ping 192.168.0.4                       # 测试网络连通性
```

### 手动指定串口

如果自动检测失败，可以手动指定端口。编辑`main.py`:

```python
# 第63行左右
client_instance = SerialClient(port='COM7', baudrate=115200)  # Windows

# 或
client_instance = SerialClient(port='/dev/ttyUSB0', baudrate=115200)  # Linux
```

## API参考

### SerialClient 类

```python
from serialclient import SerialClient

# 创建客户端
client = SerialClient(
    port='COM7',        # 串口名称，None则自动检测
    baudrate=115200     # 波特率
)

# 连接
if client.connect():
    # 启动接收线程
    client.start_receive_thread()

    # 注册回调函数
    client.register_callback(my_callback)

    # 发送消息
    client.send_message(id, cmd, body1, body2, msg_type)

    # 检查连接状态
    if client.is_healthy():
        print("连接正常")

    # 关闭连接
    client.close()
```

### UDPClient 类

```python
from udpclient import UDPClient

# 创建客户端
client = UDPClient('192.168.0.4', 3333)

# API与SerialClient相同
if client.connect():
    client.start_receive_thread()
    # ...
```

## 性能建议

1. **串口模式**
   - 优点: 连接稳定，延迟低
   - 缺点: 需要USB线，传输距离受限
   - 适用: 开发调试、近距离控制

2. **网络模式**
   - 优点: 无线传输，距离远
   - 缺点: 延迟高，易受网络影响
   - 适用: 远程控制、多机协同

## 开发说明

### 添加新的通信协议

如果需要支持其他通信方式(如蓝牙、CAN总线等)，只需实现以下接口:

```python
class MyClient:
    def connect(self) -> bool:
        """建立连接"""
        pass

    def send_message(self, id, cmd, body1, body2, msg_type) -> bool:
        """发送消息"""
        pass

    def register_callback(self, callback):
        """注册接收回调"""
        pass

    def start_receive_thread(self):
        """启动接收线程"""
        pass

    def close(self):
        """关闭连接"""
        pass
```

然后在`main.py`中添加模式选择。

## 更新日志

### 2024-11-14
- ✨ 新增串口通信模式
- ✨ 添加SerialClient类
- ✨ 创建串口诊断工具reset_port.py
- 🔧 优化UDP通信稳定性
- 🔧 改进CAN总线初始化流程
- 📝 更新故障排除文档

## 许可证

参见根目录的LICENSE文件

## 支持

- 问题反馈: https://github.com/your-repo/issues
- 文档: 查看TROUBLESHOOTING.md
