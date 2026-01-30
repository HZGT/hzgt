# MQTT.py 文档

## 导航目录

- [Mqttop](#mqttop)
  - [set_will()](#set_will)
  - [start() / connect()](#start--connect)
  - [close() / disconnect()](#close--disconnect)
  - [subscribe()](#subscribe)
  - [unsubscribe()](#unsubscribe)
  - [publish()](#publish)
  - [reconnect()](#reconnect)
  - [getdata()](#getdata)

## 类说明

### Mqttop

**功能**：封装 MQTT 类，支持发送信息和接收信息，提供完整的 MQTT 客户端功能。

**构造方法参数**：
- `host`：MQTT服务器IP地址
- `port`：MQTT端口
- `user`：选填，账号
- `passwd`：选填，密码
- `clientid`：可选，"客户端"用户名，为空将随机生成
- `data_length`：缓存数据列表的长度，默认为100
- `transport`：传输协议，可选 "tcp", "websockets", "unix"，默认为 "tcp"
- `protocol`：MQTT协议版本，支持 3(v31) 4(v311) 5(v5)，默认为 3
- `logger`：日志记录器

**属性**：
- `bool_con_success`：是否连接成功

**方法**：

#### set_will()
**功能**：设置遗嘱，需要在连接前设置。

**参数**：
- `will_topic`：遗嘱主题
- `will_msg`：遗嘱信息
- `qos`：整数类型，代表消息的服务质量（Quality of Service）等级，可选值为 0, 1, 2
- `retain`：布尔类型，用于指定是否将此消息设置为保留消息

**使用示例**：
```python
mqtt_client.set_will("device/status", "offline", qos=1, retain=True)
```

#### start() / connect()
**功能**：启动MQTT连接，建议使用time.sleep(5)等待连接完成。

**使用示例**：
```python
mqtt_client.start()
import time
time.sleep(5)  # 等待连接完成
```

#### close() / disconnect()
**功能**：断开MQTT连接。

**使用示例**：
```python
mqtt_client.close()
```

#### subscribe()
**功能**：订阅信息。如果 func 为 None，则使用默认的回调函数，接收到的信息可通过self.getdata()获取。

**参数**：
- `subtopic`：主题
- `func`：主题接收到信息后的事件回调函数，函数参数定义为(client, userdata, msg)

**使用示例**：
```python
# 使用默认回调
mqtt_client.subscribe("sensors/temperature")

# 使用自定义回调
def on_message(client, userdata, msg):
    print(f"收到消息: {msg.topic} -> {msg.payload.decode()}")

mqtt_client.subscribe("sensors/humidity", func=on_message)
```

#### unsubscribe()
**功能**：取消订阅信息。

**参数**：
- `subtopic`：主题

**使用示例**：
```python
mqtt_client.unsubscribe("sensors/temperature")
```

#### publish()
**功能**：发布信息到指定的MQTT主题。

**参数**：
- `topic`：字符串类型，代表发布消息的主题
- `msg`：字符串类型，需要发布的消息内容
- `qos`：整数类型，代表消息的服务质量（Quality of Service）等级，可选值为 0, 1, 2
- `retain`：布尔类型，用于指定是否将此消息设置为保留消息
- `properties`：字典类型，可选参数，仅MQTT协议为MQTTv5[protocol=5]时可用
- `bool_log`：布尔类型，用于确定是否记录消息发布的日志

**使用示例**：
```python
# 发布普通消息
mqtt_client.publish("sensors/temperature", "25.5", qos=1)

# 发布保留消息
mqtt_client.publish("device/status", "online", retain=True)

# 使用MQTTv5的properties
if mqtt_client.protocol == 5:
    mqtt_client.publish(
        "sensors/temperature", 
        "25.5", 
        properties={"sensor_id": "temp1", "location": "living_room"}
    )
```

#### reconnect()
**功能**：尝试重连。

**使用示例**：
```python
mqtt_client.reconnect()
import time
time.sleep(5)  # 等待连接完成
```

#### getdata()
**功能**：获取接收到的数据。

**参数**：
- `topic`：要获取数据的主题，如果为None则获取所有主题的数据（如果适用）
- `index`：获取的数据的索引，默认为0
- `bool_del`：获取数据时是否删除数据
- `bool_all`：是否获取所有数据

**返回值**：list或bytes或dict：根据情况返回bytes类型的数据或者数据列表或者字典

**使用示例**：
```python
# 获取最新的一条数据
latest_data = mqtt_client.getdata("sensors/temperature")
print(latest_data)

# 获取所有数据但不删除
all_data = mqtt_client.getdata("sensors/temperature", bool_all=True, bool_del=False)
print(all_data)
```

**完整使用示例**：

```python
from hzgt.tools import Mqttop
import time

# 创建MQTT客户端实例
mqtt_client = Mqttop(
    host="192.168.1.100",
    port=1883,
    user="admin",
    passwd="password",
    clientid="my_client"
)

# 设置遗嘱
mqtt_client.set_will("device/status", "offline", qos=1, retain=True)

# 启动连接
try:
    mqtt_client.start()
    print("正在连接到MQTT服务器...")
    time.sleep(5)  # 等待连接完成
    
    if mqtt_client.bool_con_success:
        print("MQTT连接成功!")
        
        # 订阅主题
        mqtt_client.subscribe("sensors/temperature")
        mqtt_client.subscribe("sensors/humidity")
        
        # 发布消息
        mqtt_client.publish("device/status", "online", qos=1, retain=True)
        mqtt_client.publish("sensors/temperature", "25.5", qos=0)
        
        # 等待接收消息
        print("等待接收消息...")
        time.sleep(10)
        
        # 获取接收到的数据
        temp_data = mqtt_client.getdata("sensors/temperature")
        if temp_data:
            print(f"接收到温度数据: {temp_data}")
        
        hum_data = mqtt_client.getdata("sensors/humidity")
        if hum_data:
            print(f"接收到湿度数据: {hum_data}")
        
    else:
        print("MQTT连接失败!")
finally:
    # 断开连接
    mqtt_client.close()
    print("MQTT连接已关闭")
```