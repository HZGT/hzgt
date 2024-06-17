# hzgt
[![PyPI version](https://img.shields.io/pypi/v/hzgt.svg)](https://pypi.python.org/pypi/hzgt/)

------------------------------------------------------
**包含 `MQTT` / `MYSQL` / `FTP` / `INI` 封装和其它小工具的工具箱**

**A toolbox that includes `MQTT` `MYSQL` `FTP` `INI` encapsulation, and other gadgets**

```
主要封装 Primary package: 
    [class] MQTT - Mqttop():
        封装 MQTT 类, 支持 发送信息 和 接收信息
        Encapsulates MQTT classes that support sending and receiving information
    [class] MYSQL - Mysqldbop():
        封装 MYSQL 类, 支持操作 MYSQL 数据库, 包括 [增/删/改/查]
        encapsulating MYSQL classes, supporting operations on MYSQL Database, including [ADD/DELETE/MODIFY/QUERY]
    [class] FTP - Ftpserver():
        创建 FTP 服务端
        Create an FTP server
    [class] FTP - Ftpclient():
        创建 FTP 客户端
        Create an FTP client
    [func] INI - readini():
        readini() 
            读取ini文件并返回嵌套字典
            Read the ini file and return the nested dictionary
    [func] INI - saveini():  
        saveini()
            保存嵌套字典为ini文件
            Save the nested dictionary as an ini file
        
其它小工具 Others are commonly used:
    [func] pic():
        获取变量名的名称 / 类型 / 值
        Get the name / type / value of the variable name
    [func] restrop(): 
        返回字符串的颜色字体[字体模式 / 字体颜色 / 字体背景], 可使用print()打印
        Returns the color font of the string [font mode / font color / font background], 
        which can be printed using print().
```
------------------------------------------------------


# 目录 DIRECTORY
* [运行环境 Operating environment](#operating-environment)
* [安装方式 Installation](#installation)
* [API封装 API encapsulation](#api-encapsulation)
  * [MQTT](#class-mqtt)
  * [MYSQL](#class-mysql)
* 
* 
* 


# Operating environment
`运行环境 [Operating environment]`

---
- 可行版本[Feasible version]: >= `3.8`
- 建议版本[Suggested version]: == `3.11`
---


# Installation
`安装方式 Installation`

---
使用 `pip` 安装 `hzgt` 库

use `pip` to install the python library called hzgt

```
$ pip install hzgt
```
---


# API encapsulation
`API封装 [API encapsulation]`

---
```
[class]
    MQTT
    MYSQL
    FTP
[func]    
    INI
```
---


## class MQTT

---
```
类名[class name]: Mqttop()
```
---

`Mqttop` 是一个用于简化 `MQTT通信` 的 Python 类, 它封装了 `MQTT` 客户端的基本功能, 包括 **连接**、**发布**、**订阅**和**断开连接**等操作。以下将介绍 `Mqttop` 类的使用方法和内部机制。

`Mqttop` is a Python class for simplifying `MQTT communication`, which encapsulates the basic functionality of an `MQTT` client, including operations such as **connecting**, **publishing**, **subscribing**, and **disconnecting**. The following describes in detail how to use the `Mqttop` class and how it works.

**构造函数参数[Constructor Parameters]**:
- mqtt_host: MQTT服务器IP地址[The IP address of the MQTT server]
- mqtt_port: MQTT服务器端口[MQTT server port]
- mqtt_clientid: **可选**, 客户端用户名, 为空将随机[**Optionally**, the client username, which is empty will be random]
- mqtt_subtopic: **可选**, 需要订阅的主题[**Optionally**, Topics that need to be subscribed to]
- user: **可选**, 账号[**Optionally**, Account number]
- pwd: **可选**, 密码[**Optionally**, Account password]
- bool_show: **可选**, 是否终端打印连接相关信息[**Optionally**, Whether the terminal prints connection-related information]
- bool_clean_session: **可选**, 断开连接时是否删除有关此客户端的所有信息[**Optionally**, Whether to delete all information about this client when disconnected]

**主要方法[Main methods]**: 
- set_will(will_topic, will_msg)
  - 设置遗嘱信息, 在连接前设置
  - Set up the will information, set it before connecting
- start()
  - 启动MQTT连接, 建议使用time.sleep(5)等待连接完成
  - To start an MQTT connection, we recommend that you use `time.sleep(5)` to wait for the connection to complete
- close()
  - 断开MQTT连接
  - Disconnect the MQTT connection
- publish(topic, msg, bool_show_tip=True)
  - 发布消息到指定主题
  - Publish a message to a specified topic
- retopic(new_topic)
  - 更换订阅的主题, 并自动尝试重连
  - Change the subscribed theme and automatically try to reconnect
- reconnect()
  - 尝试重连到MQTT服务器
  - Try to reconnect to the MQTT server

**注意事项[Precautions]**
- 在使用`Mqttop`类之前，请确保你已经了解了MQTT协议的基本概念和使用方法
- `Mqttop`类使用了线程来管理MQTT连接，这可能会涉及到多线程编程的相关知识
- 在使用`publish方法`时，如果发布失败，请检查网络连接和MQTT服务器的状态
- 更换订阅主题时，`retopic方法`会自动尝试重新连接MQTT服务器
- 发送信息间隔建议大于**0.3s**, 否则`self.got_datas`获取的信息会有丢失


- Before using the `Mqttop` class, make sure you understand the basic concepts and usage of the MQTT protocol
- The `Mqttop` class uses threads to manage MQTT connections, which may involve knowledge of multi-threaded programming
- When using the `publish` method, if the publish fails, check the network connection and the status of the MQTT server
- When you change the subscription topic, the `retopic` method will automatically try to reconnect to the MQTT server
- It is recommended that the message interval be greater than **0.3s**, otherwise the information obtained by the `self.got_datas` will be lost


以下为发布端和接收端的示例

The following is an example of the publisher and receiver

**信息发布端[Information publishing side]**
```python
# pub.py
import time
from hzgt import Mqttop

broker = "broker.emqx.io"  # 主机地址[host address]
port = 1883  # 端口[port]
client_id = "zxcv"  # 客户端ID名（不可重复）[Client ID Name (not repeatable)]

mops = Mqttop(broker, port, client_id)  # 创建类实例[Create a class instance]
mops.start()  # 开始连接[Start connecting]
time.sleep(3)  # 等待一段时间[Wait for a while]

while True:
    time.sleep(1)  # 每隔一段时间发布一次信息[Publish information at regular intervals]
    curtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())  # 获取当前时间[Get the current time]
    tempdict = {"time": curtime}  # 字典格式[Dictionary format]
    # mops.publish(topic="test", msg=f"{curtime}")  # 发布信息到指定主题[Publish information to a specified topic]
    mops.publish(topic="test", msg=f"{tempdict}")  # 发送字典格式[Send in dictionary format]

"""OUTPUT
MQTT服务器 连接成功!
发送成功 TOPIC[`test`]  MSG[`{'time': '2024-06-14 22:53:24'}`]
发送成功 TOPIC[`test`]  MSG[`{'time': '2024-06-14 22:53:25'}`]
发送成功 TOPIC[`test`]  MSG[`{'time': '2024-06-14 22:53:26'}`]
发送成功 TOPIC[`test`]  MSG[`{'time': '2024-06-14 22:53:27'}`]
发送成功 TOPIC[`test`]  MSG[`{'time': '2024-06-14 22:53:28'}`]
发送成功 TOPIC[`test`]  MSG[`{'time': '2024-06-14 22:53:29'}`]
...
"""
```

**信息接收端[The receiver of the message]**
```python
# sub.py
from hzgt import Mqttop
import time

broker = "broker.emqx.io"  # 主机地址[host address]
port = 1883  # 端口[port]
client_id = "qwer"  # 客户端ID名（不可重复）[Client ID Name (not repeatable)]
topic = "test"  # 订阅的主题[Subscribed to a topic]

mop = Mqttop(broker, port, client_id, topic)  # 创建类实例[Create a class instance]
mop.start()  # 开始连接[Start connecting]
time.sleep(3)  # 等待一段时间[Wait for a while]

num = 0
while True:
    time.sleep(1)
    _temp_data = mop.got_datas  # 通过self.got_datas获取数据[Get data through self.got_datas]
    print(num, "   ++>>   ", _temp_data)
    
"""OUTPUT
MQTT服务器 连接成功!
当前订阅的主题: `test`
b"{'time': '2024-06-14 22:53:25'}"
b"{'time': '2024-06-14 22:53:26'}"
b"{'time': '2024-06-14 22:53:27'}"
b"{'time': '2024-06-14 22:53:28'}"
b"{'time': '2024-06-14 22:53:29'}"
b"{'time': '2024-06-14 22:53:30'}"
...
"""
```


## class MYSQL

---
```
类名[class name]: Mysqldbop()
```
---


