# hzgt
[![img](https://img.shields.io/badge/license-MIT-blue.svg)](https://gitee.com/HZGT/hzgt/tree/master/LICENSE) [![PyPI version](https://img.shields.io/pypi/v/hzgt.svg)](https://pypi.python.org/pypi/hzgt/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/HZGT/hzgt)

# 目录 DIRECTORY
* [简介](#introduction)
* [运行环境 Operating environment](#operating-environment)
* [安装方式 Installation](#installation)
* [API封装 API encapsulation](#api-encapsulation)
  * 类[MQTT](#class-mqtt)
  * 类[MYSQL](#class-mysql)
  * 类[Ftpserver](#class-ftpserver)
  * 类[Smtpop](#class-smtpop)
  * 类[AutoConfig](#AutoConfig)
  
  * 函数[Fileserver](#func-fileserver)
  * 函数[readini](#func-readini)
  * 函数[saveini](#func-saveini)
  * 函数[getip](#func-getip)
  * 函数[pic](#func-pic)
  * 函数[restrop](#func-restrop)
  * 函数[set_log](#func-set_log)

  * 装饰器[vargs](#decorator-vargs)

------------------------------------------------------
### Introduction
### 简介
**包含 `MQTT` / `MYSQL` / `FTP` / `INI` 封装和其它小工具的工具箱**

**A toolbox that includes `MQTT` `MYSQL` `FTP` `INI` encapsulation, and other gadgets**

```text
主要封装 Primary package: 
    [class]:
        Mqttop():
            封装 MQTT 类, 支持 发送信息 和 接收信息
            Encapsulates MQTT classes that support sending and receiving information
        Mysqlop():
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
        vargs():
            一个装饰器, 根据提供的有效参数集合来验证函数的参数
            A decorator that verifies the parameters of a function against a set of valid arguments provided
            
    [cmdline]:
        hzgt fs:
            快速文件服务器(局域网内文件传输)
            Quick file server (file transfer within the local network)
        hzgt ftps:
            在本地局域网内快速创建FTP服务端
            Create an FTP server quickly within the local network
        hzgt ips:
            输出本地局域网内的IP地址列表
            Output a list of IP addresses within the local network
            
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

### Operating environment
### 运行环境

---
- 可行版本[Feasible version]: >= `3.8`
- 建议版本[Suggested version]: == `3.11`
---

### Installation
`安装方式 Installation`

---
使用 `pip install hzgt` 安装 `hzgt` 库

use `pip install hzgt` to install the python library called hzgt

```commandline
pip install hzgt
```
---

### API encapsulation
### API封装

## class MQTT

`类[class]: Mqttop()`

`Mqttop` 是一个用于简化 `MQTT通信` 的 Python 类, 它封装了 `MQTT` 客户端的基本功能, 包括 **连接**、**发布**、**订阅**和**断开连接**等操作.以下将介绍 `Mqttop` 类的使用方法和内部机制.

`Mqttop` is a Python class for simplifying `MQTT communication`, which encapsulates the basic functionality of an `MQTT` client, including operations such as **connecting**, **publishing**, **subscribing**, and **disconnecting**. The following describes in detail how to use the `Mqttop` class and how it works.

详见 [MQTT.md](doc/MQTT.md)

## class MYSQL

`类[class]: Mysqldbop()`

`Mysqlop` 类提供了一系列操作 `MySQL` 数据库的方法, 包括**连接管理**、**数据读写**、**数据库和表管理**、**权限管理**等.

The `Mysqlop` class provides a series of methods for manipulating `MySQL` databases, including **connection management**, **data reading** and **writing**, **database and table management**, **rights management**, etc.

详见 [MYSQL.md](doc/MYSQL.md)

## class Ftpserver

`类[class]: Ftpserver()`

`Ftpserver` 类提供了 `FTP服务端` 的操作API.

The `Ftpserver` class provides the API of the `FTP server`.

详见 [FTPS.md](doc/FTPS.md)

## class Smtpop

`类[class]: Smtpop()`

`Smtpop` 类提供了便捷发送邮件的功能.

The `Smtpop` class provides a convenient function for sending emails.

详见 [SMTP.md](doc/SMTP.md)

## class AutoConfig

`类[class]: AutoConfig()`

`AutoConfig` 类提供了自动获取配置的功能.

The `AutoConfig` class provides the ability to automatically obtain configuration.

详见 [AutoConfig.md](doc/AutoConfig.md)

## func Fileserver

`函数[func]: Fileserver()`

`Fileserver` 函数提供了快速在局域网内构建文件服务器的功能.

The `Fileserver` function provides the ability to quickly build a file server within the local network.

参数:
- `path`: 文件服务器的根目录
- `host`: 服务器的主机地址 默认为 **WIFI 局域网 IP 地址**
- `port`: 服务器的端口号 默认为 **5001**
- `bool_https`: 是否使用 HTTPS 协议
- `certfile`: 证书文件名
- `keyfile`: 密钥文件名

示例:
```python
from hzgt.tools import Fileserver, getip

Fileserver(path="./", host=getip(-1), port=5001, 
           bool_https=False, 
           certfile="", keyfile="")
```

## func readini

`函数[func]: readini()`

`readini` 函数用于读取ini文件并返回嵌套字典.

The `readini` function is used to read the ini file and return the nested dictionary.

参数:
- `path`: ini文件的路径
- `encoding`: ini文件的编码格式 默认为 **utf-8**

返回:
- `dict`: 嵌套字典

示例:
```python
from hzgt.tools import readini

config = readini("cfg.ini", encoding="utf-8")
print(config)
```

## func saveini

`函数[func]: saveini()`

`saveini` 函数用于保存嵌套字典为ini文件.

The `saveini` function is used to save the nested dictionary as an ini file.

参数:
- `savename`: ini文件的保存路径
- `iniconfig`: 嵌套字典
- `section_prefix`: ini文件的section前缀 默认为 **空字符串**
- `bool_space`: 是否添加空格 默认为 **True**
- `encoding`: ini文件的编码格式 默认为 **utf-8**

示例:
```python
from hzgt.tools import saveini

saveini("cfg.ini", 
        {
          "section1": 
            {
              "key1": "value1", 
              "key2": "value2"
            }, 
          "section2": 
            {
              "key3": "value3", 
              "key4": "value4"
            }
        }, section_prefix="[", bool_space=True, encoding="utf-8")
```

## func getip

`函数[func]: getip()`

`getip` 函数用于获取本地主机的IP地址.

The `getip` function is used to get the IP address of the local host.

参数:
- `index`: 获取的IP地址的索引 默认为 **-1**
- `ipv6`: 是否获取IPv6地址 默认为 **True**

返回:
- `list` | `str`: **IP地址列表** 或者 **IP地址字符串**

示例:
```python
from hzgt.tools import getip

print(getip(-1))
print(getip(ipv6=True))
print(getip())
```

## func pic

`函数[func]: pic()`

`pic` 函数用于获取变量名的**名称** / **类型** / **值**, **[该函数占用必须一行, 即一行写完]**.

The `pic` function is used to get the **name** / **type** / **value** of the variable name, **[this function must occupy one line, that is, write one line]**

参数:
- `*args`: 需要获取变量名的变量, 可传入多个变量 **[该函数占用必须一行, 即一行写完]**
- `bool_header`: 是否打印列名 默认为 **True**
- `bool_show`: 是否直接打印(仍然有返回值) 默认为 **False**

返回:
- `list`: list[tuple[Any, str, Any]] (变量名, 变量类型, 值) 不定数量

示例:
```python
from hzgt import pic
a = 5
b = 3.5
c = "hello"
pic(a, b, c)
```

## func restrop
`函数[func]: restrop()`

`restrop` 函数用于字符串颜色配置

The `restrop` function is used to configure string color

参数:
- `text`: 需要配置颜色的字符串
- `m`: 字体模式
- `f`: 字体颜色
- `b`: 背景颜色
- `frgb`: 字体颜色 RGB 值 当f=8时有效
- `brgb`: 背景颜色 RGB 值 当b=8时有效

参数可取值:

m 取值表

| m[mode] 模式 |            说明            |
|:----------:|:------------------------:|
|     0      |            默认            |
|     1      |           粗体高亮           |
|     2      |           暗色弱化           |
|     3      |       斜体 (部分终端支持)        |
|     4      |           下划线            |
|     5      |   缓慢闪烁 (未广泛支持，shell有效)   |
|     6      |   快速闪烁 (未广泛支持，shell有效)   |
|     7      |            反色            |
|     8      |  前景隐藏文本 (未广泛支持，shell有效)  |
|     9      |           删除线            |
|     21     |      双下划线 (部分终端支持)       |
|     52     | 外边框 [颜色随字体颜色变化] (部分终端支持) |
|     53     |       上划线 (部分终端支持)       |


f / b 取值表

|      f[fore] / b[back]  前景颜色 / 背景颜色       |   说明   |
|:-----------------------------------------:|:------:|
|                     0                     |   黑色   |
|                     1                     |   红色   |
|                     2                     |   绿色   |
|                     3                     |   黄色   |
|                     4                     |   蓝色   |
|                     5                     |   紫色   |
|                     6                     |   青色   |
|                     7                     |   灰色   |
|                     8                     | 设置颜色功能 |
|                     9                     |   默认   |

frgb / brgb 取值表

| frgb[fore RGB] / brgb[back RGB]  前景 RGB / 背景 RGB |         说明         |
|:------------------------------------------------:|:------------------:|
|       (0 ~ 255, 0 ~ 255, 0 ~ 255) RGB颜色元组        | 前景色或背景色为RGB元组对应的颜色 |

返回:
- `str`: 配置后的字符串

示例:
```python
from hzgt import restrop

print(restrop("Hello World!", m=0, f=2, b=3))  # 绿色前景 黄色背景
print(restrop("Hello World!", m=52, f=8, frgb=(255, 0, 0)))  # 输出带外边框的"Hello World!"
```

结果: [pycharm 2023.2.8 版本终端输出]

![](doc/image/restrop_utest.png)

## func set_log

`函数[func]: set_log()`

`set_log` 函数用于胚配置日志记录器

The `set_log` function is used to configure the log recorder

参数:
- `name`: 日志记录器的名称
- `logfilename`: 日志文件名 格式为 **"\*.log"**
- `level`: 日志记录器的等级 默认为 **2**
- `print_prefix`: 日志记录器在终端的输出格式 默认为 ```f'{restrop("[%(name)s %(asctime)s]", f=3)} {restrop("[%(levelname)s]", f=5)}\t{restrop("%(message)s")}'```
- `file_prefix`: 日志记录器在日志文件中的输出格式 默认为 ```"[%(name)s %(asctime)s] \[%(levelname)s]\t%(message)s"```
- `datefmt`: 日志记录器在终端和日志文件中的输出时间格式 默认为 **%Y-%m-%d %H:%M:%S**
- `maxBytes`: 日志文件最大字节数 默认为 **2 * 1024 * 1024**
- `backupCount`: 日志文件备份数量 默认为 **3**
- `encoding`: 日志文件编码格式 默认为 **utf-8**

返回:
- `logging.Logger`: 日志记录器

示例:
```python
from hzgt import set_log
logger = set_log("test", "test.log", level=2)
logger.info("INFO!")
logger.error("ERROR!")
```

## decorator vargs

`装饰器[decorator]: vargs()`

装饰器 `vargs` 根据其有效集合验证函数参数.

The `vargs` decorator verifies the function parameters based on its effective set.

参数:
- `valid_params`: `dict` {参数名: 有效集合}

示例:
```python
from hzgt import vargs

@vargs({"a": [1, 2, 3], "b": [4, 5, 6]})
def test(a, b):
    print(a, b)
    
test(1, 4)
test(4, 5)
test(1, 7)
test(2, 4)
```
