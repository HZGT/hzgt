# hzgt
[![img](https://img.shields.io/badge/license-MIT-blue.svg)](https://gitee.com/HZGT/hzgt/tree/master/LICENSE) [![PyPI version](https://img.shields.io/pypi/v/hzgt.svg)](https://pypi.python.org/pypi/hzgt/)


------------------------------------------------------
**包含 `MQTT` / `MYSQL` / `FTP` / `INI` 封装和其它小工具的工具箱**

**A toolbox that includes `MQTT` `MYSQL` `FTP` `INI` encapsulation, and other gadgets**

```text
主要封装 Primary package: 
    [class]:
        Mqttop():
            封装 MQTT 类, 支持 发送信息 和 接收信息
            Encapsulates MQTT classes that support sending and receiving information
        Mysqldbop():
            封装 MYSQL 类, 支持操作 MYSQL 数据库, 包括 [增/删/改/查]
            encapsulating MYSQL classes, supporting operations on MYSQL Database, including [ADD/DELETE/MODIFY/QUERY]
        Ftpserver():
            创建 FTP 服务端
            Create an FTP server
        Ftpclient():
            创建 FTP 客户端
            Create an FTP client
        
    [func]:
        readini() 
            读取ini文件并返回嵌套字典
            Read the ini file and return the nested dictionary
        saveini()
            保存嵌套字典为ini文件
            Save the nested dictionary as an ini file
            
        Fileserver()
            快速构建文件服务器
            Build file servers quickly
            
    [decorator]:
        gettime():
            一个装饰器, 获取函数执行的时间
            A decorator that gets the time when the function was executed
        log_func():
            一个日志装饰器, 为其他函数添加日志记录功能
            A log decorator that adds logging functionality to other functions
        vargs():
            一个装饰器, 根据提供的有效参数集合来验证函数的参数
            A decorator that verifies the parameters of a function against a set of valid arguments provided

        
其它小工具 Others are commonly used:
    [func] pic():
        获取变量名的名称 / 类型 / 值
        Get the name / type / value of the variable name
    [func] restrop(): 
        返回字符串的终端颜色字体[字体模式 / 字体颜色 / 字体背景], 可使用print()打印
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
使用 `pip install hzgt` 安装 `hzgt` 库

use `pip install hzgt` to install the python library called hzgt

```commandline
pip install hzgt
```
---


# API encapsulation
`API封装 [API encapsulation]`

---
## [class]
`类`
* **MQTT**
  - [Mqttop](#class-mqtt)

* **MTSQL**
  - [Mysqldbop](#class-mysql)

* **FTP**
  - Ftpserver
  - Ftpclient


## [func]
`函数`
* **INI**
  - readini
  - saveini

* **Other**
  - pic
  - restrop


## [Decorator]
`装饰器`
- gettime

---


## class MQTT

---
`类名[class name]: Mqttop()`
---

`Mqttop` 是一个用于简化 `MQTT通信` 的 Python 类, 它封装了 `MQTT` 客户端的基本功能, 包括 **连接**、**发布**、**订阅**和**断开连接**等操作。以下将介绍 `Mqttop` 类的使用方法和内部机制。

`Mqttop` is a Python class for simplifying `MQTT communication`, which encapsulates the basic functionality of an `MQTT` client, including operations such as **connecting**, **publishing**, **subscribing**, and **disconnecting**. The following describes in detail how to use the `Mqttop` class and how it works.

详见 [MQTT.md](doc/MQTT.md)


## class MYSQL

---
`类名[class name]: Mysqldbop()`
---

`Mysqlop` 类提供了一系列操作 `MySQL` 数据库的方法, 包括**连接管理**、**数据读写**、**数据库和表管理**、**权限管理**等.

The `Mysqlop` class provides a series of methods for manipulating `MySQL` databases, including **connection management**, **data reading** and **writing**, **database and table management**, **rights management**, etc.

详见 [MYSQL.md](doc/MYSQL.md)








