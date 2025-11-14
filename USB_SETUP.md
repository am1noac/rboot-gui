# USB串口通信配置说明

## 修改内容

已将dummy机械臂的通信方式从UDP改为USB串口通信。

### 主要更改:

1. **新增文件**: `dummy2-gui/rboot-gui/serialclient.py`
   - 实现了SerialClient类,用于USB串口通信
   - 支持COM7端口,波特率115200
   - 实现了与原UDPClient相同的接口,保证兼容性

2. **修改文件**: `dummy2-gui/rboot-gui/main.py`
   - 将UDPClient替换为SerialClient
   - 配置为使用COM7端口
   - 更新了错误提示信息

## 配置参数

- **端口**: COM7
- **波特率**: 115200
- **数据位**: 8
- **停止位**: 1
- **校验位**: 无

## 依赖库

需要安装pyserial库:

```bash
pip install pyserial
```

## 使用方法

1. 确保dummy机械臂通过USB连接到计算机的COM7端口
2. 安装pyserial: `pip install pyserial`
3. 运行GUI程序: `python dummy2-gui/rboot-gui/main.py`
4. 点击"连接设备"按钮

## 修改端口或波特率

如果需要使用其他端口或波特率,请修改 `main.py` 第36行:

```python
client_instance = SerialClient('COM7', 115200)
```

改为:

```python
client_instance = SerialClient('COM8', 9600)  # 例如使用COM8端口,波特率9600
```

## 故障排查

如果连接失败,请检查:

1. 设备是否正确连接到COM7端口
2. COM7端口是否被其他程序占用
3. 是否已安装pyserial库
4. 设备驱动是否正确安装

可以使用设备管理器(Windows)或`ls /dev/tty*`(Linux)查看可用串口。
