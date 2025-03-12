
---
`类[class]: Mqttop()`
---

`Mqttop` 是一个用于简化 `MQTT通信` 的 Python 类, 它封装了 `MQTT` 客户端的基本功能, 包括 **连接**、**发布**、**订阅**和**断开连接**等操作。以下将介绍 `Mqttop` 类的使用方法和内部机制。

`Mqttop` is a Python class for simplifying `MQTT communication`, which encapsulates the basic functionality of an `MQTT` client, including operations such as **connecting**, **publishing**, **subscribing**, and **disconnecting**. The following describes in detail how to use the `Mqttop` class and how it works.

---
- [构造函数参数](#constructor-parameters)
- [核心方法](#core-methods)
  - [遗嘱信息设置、连接与断开](#will-information-setting-connection-and-disconnection) 
  - [发布与订阅](#publish-and-subscribe)
  - [数据缓存管理](#data-cache-management)
- [使用示例](#examples)
- [注意事项](#important-notes)
- [错误码rc](#error-codes)
- [Qos代码](#qos-codes)
---

### constructor parameters
### 构造函数参数
- `host`: MQTT 服务器地址（必填），例如 "broker.emqx.io"
- `port`: MQTT 服务器端口（必填），例如 1883
- `user`: 可选，账号（默认为空）
- `passwd`: 可选，密码（默认为空）
- `clientid`: 可选，客户端标识符。若未提供，将自动生成随机 ID（格式：xxxx-xxxx-xxxx）
- `data_length`: 数据缓存队列的最大长度（默认 100），用于限制历史数据存储量
- `transport`: 可选，传输协议，支持 "tcp"、"websockets" 或 "unix"（默认 "tcp"）
- `protocol`: 可选，MQTT 协议版本，支持 3（MQTTv3.1）、4（MQTTv3.1.1）、5（MQTTv5）（默认 3）
- `logger`: 可选，自定义日志记录器。若未提供，将自动创建默认日志（保存至 logs/mqtt.log）

### Core Methods
### 核心方法
#### will information setting connection and disconnection
#### 遗嘱信息设置、连接与断开
1. `set_will(will_topic, will_msg, qos=0, retain=False)`
- 功能：设置遗嘱消息（需在连接前调用）
- 参数：
  - `will_topic`: 遗嘱主题
  - `will_msg`: 遗嘱消息内容
  - `qos`: [服务质量等级（0/1/2）](#qos-codes)
  - `retain`: 是否保留消息
- 示例：
  ```python
  from hzgt.tools import Mqttop
              
  # 创建实例并设置遗嘱消息
  mp = Mqttop(host="broker.emqx.io", port=1883, clientid="publisher-001", protocol=4)
  mp.set_will("status/device1", "offline", qos=1)
  mp.start()  # 连接
  ```
   
2. `start()` / `connect()`
- 功能：启动 MQTT 连接（非阻塞，建议后续等待 time.sleep(5)）
- 日志提示： 
  - `连接成功`：MQTT服务器 连接成功!
  - `连接失败`：根据[返回码](#error-codes)显示错误原因（如协议版本不匹配、认证失败等）

3. `close()` / `disconnect()`
- 功能：断开 MQTT 连接并清理资源
- 日志提示：
  - MQTT连接已关闭

#### publish and subscribe
#### 发布与订阅
1. `subscribe(subtopic, func=None)`
- 功能：订阅指定主题
- 参数：
  - `subtopic`: 订阅的主题（支持通配符） 
  - `func`: 自定义回调函数。若未提供，消息将存入缓存队列
- 示例：
  ```
  mp.subscribe("sensors/#")  # 默认存储至缓存
  mp.subscribe("alerts", custom_callback)  # 自定义处理
  ```      
  
2. `unsubscribe(subtopic)`
- 功能：取消订阅主题
- 日志提示：
  - 取消订阅主题: <subtopic>

3. `publish(topic, msg, qos=0, retain=False, properties=None, bool_log=True)`
- 功能：向指定主题发布消息
- 参数：
  - `topic`: 目标主题
  - `msg`: 消息内容（字符串或序列化数据）
  - `qos`: 服务质量等级
  - `retain`: 是否保留消息
  - `properties`: MQTTv5 专用，附加属性（字典格式）
  - `bool_log`: 是否记录发送日志
- 日志示例：
  - `成功`：发送成功 TOPIC[test] MSG[{"temp": 25}]
  - `失败`：发送失败 TOPIC[test] MSG[{"temp": 25}]

#### Data Cache Management
#### 数据缓存管理
1. `getdata(topic=None, index=0, bool_del=True, bool_all=False)`
- 功能：从缓存队列获取数据
- 参数：
  - `topic`: 指定主题（若未提供，返回全部数据）
  - `index`: 数据索引（默认最新一条）
  - `bool_del`: 是否删除已获取数据
  - `bool_all`: 是否获取所有数据
- 返回值：
  - `单条数据`：[payload, qos, retain, properties_dict]
  - `全部数据`：字典格式 {topic: [data_list]}

### Examples
### 使用示例
发布端（Publisher）
```python
# pub.py
import time
import random
from hzgt.tools import Mqttop

# 初始化连接参数
broker = "broker.emqx.io"
port = 1883
client_id = "publisher-001"

# 创建实例并连接
mqttop = Mqttop(host=broker, port=port, clientid=client_id, protocol=4)
mqttop.start()
time.sleep(3)  # 等待连接

# 周期性发布数据
while True:
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    payload = {"time": current_time, "value": random.randint(20, 30)}
    mqttop.publish(topic="sensors/temp", msg=str(payload), qos=1)
    time.sleep(1)
```

订阅端（Subscriber）
```python
# sub.py
import time
from hzgt.tools import Mqttop

# 初始化连接参数
broker = "broker.emqx.io"
port = 1883
client_id = "subscriber-001"

# 创建实例并连接
mqttop = Mqttop(host=broker, port=port, clientid=client_id)
mqttop.subscribe("sensors/#")  # 订阅所有传感器主题
mqttop.start()
time.sleep(3)  # 等待连接

# 轮询获取数据
while True:
    data = mqttop.getdata(topic="sensors/temp", bool_del=False)
    if data:
        print(f"Received: {data.decode()}")
    time.sleep(0.5)
```

### Important Notes
### 注意事项
- `协议版本兼容性`
MQTTv5 支持自定义属性（`properties` 参数），低版本需忽略此功能
连接失败时检查协议版本与服务器兼容性
- `线程安全`
使用独立线程管理连接（`start()` 内部启动线程），避免阻塞主程序
- `数据缓存限制`
默认缓存最近 100 条数据，超出后自动淘汰旧数据
- `重连机制`
网络异常后需手动调用 `reconnect()`，暂无自动重连逻辑
- `性能建议`
高频发布场景下，建议设置 **data_length** 避免内存溢出, 订阅回调函数应避免耗时操作，以免阻塞消息处理

### error-codes
### 错误代码

| 返回码rc |      描述       |
|:-----:|:-------------:|
|  0	   |     连接成功      |
|  1	   |    协议版本不支持    |  
|  2	   |   客户端标识符无效    |  
|  3	   |    服务器不可用     | 
|  4	   |   用户名/密码错误    | 
|  5	   |      未授权      |
| 6-255 | 其他错误（参考服务器文档） |     

### qos-codes
### 服务质量等级（QoS）代码

`0`:
  - **最多一次交付**：消息发布后，至多会被传递一次，但不保证被成功接收。
  - 无需确认或重传：不会花费额外的网络传输或处理开销。
  - 低延迟：由于没有确认和重传机制，消息传输速度更快。  

`1`:
  - **至少一次交付**：消息发布后，将确保至少被传递一次，但可能会多次传递。
  - 确认和重传：如果消息未能成功传递给订阅者，MQTT 客户端会进行确认和重传处理。
  - 可靠性较高：相对于 QoS 0，QoS 1 提供了更高的消息传输可靠性。

`2`:
  - **恰好一次交付**：消息发布后，将确保仅被传递一次，不会发生重复传递。
  - 确认和重传：如果消息未能成功传递给订阅者，MQTT 客户端会进行确认和重传处理，直到消息被接收为止。
  - 最高可靠性：相对于 QoS 0 和 QoS 1，QoS 2 提供了最高的消息传输可靠性。