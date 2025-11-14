# Rboot GUI 故障排除指南

## 连接模式说明

Rboot GUI支持两种连接模式:

1. **串口模式 (USB)** - 默认模式
   - 通过USB线直接连接设备
   - 使用COM端口通信 (如COM7, /dev/ttyUSB0)
   - 波特率: 115200
   - 适用于USB直连的dummy机械臂

2. **网络模式 (UDP)**
   - 通过以太网连接设备
   - 使用UDP协议通信
   - 默认地址: 192.168.0.4:3333
   - 适用于网络版控制器

---

## 问题1A: 串口连接超时 (USB模式)

### 症状
- 点击"连接设备"按钮后显示串口连接失败
- 控制台显示"serial.open()超时（5秒）"
- 需要反复重新插拔USB线

### 解决方案

#### 方案1: 运行串口诊断工具
```bash
cd dummy2-gui/rboot-gui

# 列出所有串口
python reset_port.py list

# 测试指定串口
python reset_port.py test COM7

# 重置串口
python reset_port.py reset COM7
```

#### 方案2: 检查串口占用
**Windows:**
- 打开设备管理器
- 展开"端口(COM和LPT)"
- 查看是否有黄色感叹号
- 确认COM端口号

**Linux:**
```bash
# 列出串口设备
ls -l /dev/ttyUSB* /dev/ttyACM*

# 检查权限
sudo usermod -a -G dialout $USER  # 添加用户到dialout组
# 需要重新登录生效

# 检查是否被占用
lsof /dev/ttyUSB0
```

#### 方案3: 安装/更新驱动
- **CH340/CH341**: 常见的USB转串口芯片
- **CP210x**: Silicon Labs USB转串口
- **FTDI**: FTDI USB转串口

下载对应驱动并安装

#### 方案4: 手动指定端口
在`main.py`中修改:
```python
# 第65行左右
client_instance = SerialClient(port='COM7', baudrate=115200)  # Windows
# 或
client_instance = SerialClient(port='/dev/ttyUSB0', baudrate=115200)  # Linux
```

---

## 问题1B: 网络连接超时 (UDP模式)

### 症状
- 点击"连接设备"按钮后显示连接失败
- 需要反复重新插拔USB线或网线
- 控制台显示连接超时错误

### 根本原因
这不是真正的串口连接问题，而是UDP网络连接问题。系统通过UDP协议(端口3333)与设备(IP: 192.168.0.4)通信。

### 解决方案

#### 方案1: 运行网络诊断工具
```bash
cd dummy2-gui/rboot-gui
python reset_network.py
```

这个工具会自动检测：
- 网络连通性 (ping测试)
- UDP端口通信
- 本地端口占用
- 网络接口配置

#### 方案2: 手动检查网络连接
1. **检查设备IP配置**
   ```bash
   ping 192.168.0.4
   ```
   如果ping不通，说明设备未连接或IP配置错误

2. **检查本机IP地址**
   确保本机IP在同一网段，建议配置为:
   - IP: 192.168.0.100
   - 子网掩码: 255.255.255.0
   - 网关: 192.168.0.1

3. **检查防火墙**
   确保UDP端口3333没有被防火墙阻止:
   ```bash
   # Linux
   sudo ufw allow 3333/udp

   # Windows (以管理员身份运行PowerShell)
   New-NetFirewallRule -DisplayName "Rboot UDP" -Direction Inbound -Protocol UDP -LocalPort 3333 -Action Allow
   ```

#### 方案3: 等待足够的时间
新的代码已经优化了连接流程:
- 连接超时从3秒增加到5秒
- 添加了0.5秒的连接间隔限制
- 关闭旧连接后等待0.5秒再重新连接

**建议**: 点击"连接设备"后耐心等待5-10秒，不要频繁点击。

---

## 问题2: CAN总线通信超时

### 症状
- 连接设备成功后，点击"连接CAN总线"按钮没反应
- 控制台重复显示:
  ```
  发送超时 (尝试 1)
  发送超时 (尝试 2)
  发送超时 (尝试 3)
  发送消息最终失败,但保持连接
  ```

### 根本原因
1. **发送间隔太短**: 原来的代码发送消息过快，设备来不及响应
2. **缺少轮询机制**: 没有定期查询电机状态
3. **回调注册时机**: 回调函数注册时机不当

### 已修复的问题

#### 1. 增加了发送间隔控制
```python
self.send_interval = 0.02  # 20ms发送间隔，适配115200波特率
```

#### 2. 添加了自动轮询机制
新的代码在点击"连接CAN总线"后会:
- 自动注册回调函数
- 等待0.5秒让连接稳定
- 测试查询电机1的状态
- 启动定时轮询(每0.5秒查询所有电机)

#### 3. 改进了重试机制
- 重试次数从2次增加到3次
- 使用递增的重试延迟 (50ms, 100ms, 200ms)
- 发送失败不会立即断开连接

### 使用建议

1. **正确的连接顺序**:
   ```
   步骤1: 点击"连接设备" → 等待5秒 → 看到"✓ 已连接到设备!"
   步骤2: 点击"连接CAN总线" → 等待2秒 → 看到"CAN BUS: Enabled"变绿
   步骤3: 开始控制电机
   ```

2. **如果CAN总线连接失败**:
   - 先点击"断开CAN总线"
   - 等待2秒
   - 再点击"连接CAN总线"

3. **检查设备端**:
   - 确认设备已加载CAN总线固件
   - 确认电机控制器已上电
   - 确认CAN总线波特率设置为115200

---

## 问题3: 发送命令无响应

### 症状
- CAN总线显示已连接
- 发送位置/速度命令后电机不动
- 没有错误提示

### 排查步骤

1. **检查电机状态**
   在"Status"模式下查看各个电机的:
   - Status: 应该是8 (CLOSED_LOOP_CONTROL)
   - Error: 应该是0
   - Voltage: 应该显示电源电压

2. **启用闭环控制**
   点击界面上的"Enable all joints to close loop mode"按钮

3. **检查减速比配置**
   在motors_cfg中检查reduction值是否正确:
   - M1-M3, M5-M6: reduction=50
   - M4: reduction=30

4. **检查发送间隔**
   如果仍然有问题，可以增加发送间隔:
   ```python
   # 在 udpclient.py 中修改
   self.send_interval = 0.05  # 增加到50ms
   ```

---

## 性能优化建议

### 波特率与发送间隔的关系

当前配置 (波特率115200):
- 发送间隔: 20ms
- 理论最大速率: 50条/秒
- 实际速率: ~40条/秒 (考虑网络延迟)

如果需要更快的响应:
1. 减少发送间隔到10ms (但可能导致丢包)
2. 增加设备端的波特率
3. 使用有线以太网而非USB转网络

### 减少轮询频率
如果不需要实时监控所有电机状态:
```python
# 在 controls.py 的 register_cb() 中修改
register_cb.polling_timer = ui.timer(1.0, lambda: poll_motors())  # 改为1秒轮询
```

---

## 诊断命令速查表

### 串口模式诊断
```bash
cd dummy2-gui/rboot-gui

# 列出所有串口
python reset_port.py list

# 测试串口连接
python reset_port.py test COM7 115200

# 重置串口
python reset_port.py reset COM7

# 运行完整串口诊断
python reset_port.py
```

### 网络模式诊断
```bash
cd dummy2-gui/rboot-gui

# 测试网络连通性
ping 192.168.0.4

# 运行完整网络诊断
python reset_network.py

# 仅测试连接
python reset_network.py test

# 重置网络
python reset_network.py reset
```

### 启动程序
```bash
cd dummy2-gui/rboot-gui
python main.py

# 安装依赖（首次运行）
pip install -r ../requirements.txt
```

---

## 常见错误代码

| 错误信息 | 原因 | 解决方法 |
|---------|------|---------|
| **串口模式** | | |
| `serial.open()超时` | 串口被占用或驱动异常 | 运行 reset_port.py，重新插拔USB |
| `Permission denied` | Linux权限不足 | sudo usermod -a -G dialout $USER |
| `Port not found` | 端口不存在 | 运行 reset_port.py list 查看可用端口 |
| `串口错误` | 设备断开或驱动问题 | 检查USB连接，重新安装驱动 |
| **网络模式** | | |
| `✗ 连接失败` | 设备未连接或IP错误 | ping 192.168.0.4 检查连通性 |
| `接收错误` | 网络异常或设备断开 | 检查网线，重启设备 |
| **通用** | | |
| `发送超时` | 发送过快或设备无响应 | 检查CAN总线是否启用 |
| `未连接，无法发送消息` | 连接断开 | 重新点击"连接设备" |
| `连接过于频繁` | 点击连接按钮太快 | 等待0.5秒后重试 |
| `缺少pyserial库` | 未安装串口库 | pip install pyserial |

---

## 联系支持

如果以上方法都无法解决问题，请提供以下信息:

1. 运行诊断工具的完整输出:
   ```bash
   python reset_network.py > diagnosis.txt 2>&1
   ```

2. GUI控制台的错误日志

3. 设备型号和固件版本

4. 网络配置 (IP地址、子网掩码等)
