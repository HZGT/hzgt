# hzgt 工具库

## 项目介绍

hzgt 是一个功能丰富的 Python 工具库，提供了多种实用工具和功能模块，包括数据库操作、网络通信、文件处理、日志管理等。

## 项目结构

```
hzgt/
├── __init__.py              # 主包初始化文件
├── __version/               # 版本信息
│   ├── __init__.py
│   └── version.txt
├── core/                    # 核心功能模块
│   ├── CONST.py             # 常量定义
│   ├── Decorator.py         # 装饰器
│   ├── __init__.py
│   ├── autoconfig.py        # 自动配置
│   ├── sysutils.py          # 系统工具
│   ├── fileop.py            # 文件操作
│   ├── ipss.py              # IP地址工具
│   ├── log.py               # 日志管理
│   └── strop.py             # 字符串操作
├── tools/                   # 工具模块
│   ├── SQL/                 # SQL数据库操作
│   │   ├── sqlcore/         # SQL核心功能
│   │   ├── MYSQL.py         # MySQL操作
│   │   ├── SQLITE.py        # SQLite操作
│   │   ├── __init__.py
│   │   └── sqlhistory.py    # SQL历史记录
│   ├── SQLs/                # SQL脚本
│   ├── FTP.py               # FTP服务端和客户端
│   ├── FileServer.py        # 文件服务器
│   ├── INI.py               # INI文件操作
│   ├── MQTT.py              # MQTT通信
│   ├── REGISTER.py          # 函数和类注册器
│   ├── SMTP.py              # SMTP邮件发送
│   └── __init__.py
├── cmdline.py               # 命令行接口
└── LICENSE                  # 许可证
```

## 核心功能模块

### 1. 核心模块 (core)

- **字符串操作 (strop)**: 提供字符串处理函数，如变量信息获取、终端颜色字体设置
- **文件操作 (fileop)**: 提供文件操作函数，如字节转换、文件大小获取、文件名生成
- **装饰器 (Decorator)**: 提供实用装饰器，如函数执行时间统计、参数验证、双重参数支持
- **日志管理 (log)**: 提供日志配置功能
- **IP地址工具 (ipss)**: 提供IP地址获取和验证功能
- **自动配置 (autoconfig)**: 提供从环境变量自动配置的功能
- **系统工具 (sysutils)**: 提供系统相关功能，如管理员权限检查、命令执行

### 2. 工具模块 (tools)

- **MQTT通信 (MQTT)**: 提供MQTT消息发布和订阅功能
- **SQL数据库 (SQL)**: 提供MySQL和SQLite数据库操作功能
- **FTP服务 (FTP)**: 提供FTP服务端和客户端功能
- **文件服务器 (FileServer)**: 提供快速构建文件服务器的功能
- **INI文件操作 (INI)**: 提供INI文件读写功能
- **函数和类注册器 (REGISTER)**: 提供函数和类的注册功能
- **SMTP邮件发送 (SMTP)**: 提供邮件发送功能

## 安装方法


```bash
pip install hzgt
```

## 基本使用方法

### 1. 核心模块使用

```python
from hzgt import pic, restrop, set_log, getip

# 使用pic函数获取变量信息
x = 123
print(pic(x))

# 使用restrop函数设置终端颜色
print(restrop("Hello World", f=3, b=4))

# 配置日志
logger = set_log("myapp")
logger.info("Hello from logger")

# 获取本地IP地址
print(getip())
```

### 2. 工具模块使用

#### MQTT通信

```python
from hzgt.tools import Mqttop

# 初始化MQTT客户端
mqtt = Mqttop("broker.hivemq.com", 1883)

mqtt.start()
# 发布消息
mqtt.publish("test/topic", "Hello MQTT")

# 订阅消息
mqtt.subscribe("test/topic")
# 处理消息
while True:
    msg = mqtt.getdata()
    if msg:
        print(msg)
```

#### 数据库操作

```python
from hzgt.tools import Mysqlop, SQLiteop

# MySQL操作
mysql = Mysqlop(host="localhost", port=3306, user="root", passwd="password", database="test")
# 创建表（无需编写SQL语句）
mysql.create_table("users", {"id": "INT PRIMARY KEY", "name": "VARCHAR(255)"})
# 插入数据（无需编写SQL语句）
mysql.insert("users", {"id": 1, "name": "John"})
# 查询数据（无需编写SQL语句）
print(mysql.select("users"))
# 带条件查询（使用人类可读的条件运算符）
print(mysql.select("users", conditions={"id": {">": 0}}))

# SQLite操作
sqlite = SQLiteop("test.db")
# 创建表（无需编写SQL语句）
sqlite.create_table("users", {"id": "INTEGER PRIMARY KEY", "name": "TEXT"})
# 插入数据（无需编写SQL语句）
sqlite.insert("users", {"id": 1, "name": "John"})
# 查询数据（无需编写SQL语句）
print(sqlite.select("users"))
# 带条件查询（使用人类可读的条件运算符）
print(sqlite.select("users", conditions={"id": {">": 0}}))
```

#### FTP服务

```python
from hzgt.tools import Ftpserver, Ftpclient

# 创建FTP服务端
server = Ftpserver()
server.start()

# 创建FTP客户端
client = Ftpclient("127.0.0.1", 2121, "user", "pass")
client.upload("local.txt", "remote.txt")
client.getfile("remote.txt", "local_copy.txt")
```

#### 文件服务器

```python
from hzgt.tools import Fileserver

# 启动文件服务器
Fileserver("path/to/files", "0.0.0.0", 8000)
```

#### 邮件发送

```python
from hzgt.tools import Smtpop

# 发送邮件
with Smtpop("smtp.qq.com", 587, "your_email@qq.com", "your_authorization_code") as smtp:
    smtp.add_recipient("recipient@example.com")
    smtp.send("测试邮件", "这是一封测试邮件")
```

## 文档导航

### 核心模块文档

- [字符串操作 (strop.md)](docs/hzgt/core/strop.md)
- [文件操作 (fileop.md)](docs/hzgt/core/fileop.md)
- [装饰器 (Decorator.md)](docs/hzgt/core/Decorator.md)
- [日志管理 (log.md)](docs/hzgt/core/log.md)
- [IP地址工具 (ipss.md)](docs/hzgt/core/ipss.md)
- [自动配置 (autoconfig.md)](docs/hzgt/core/autoconfig.md)
- [系统工具 (sysutils.md)](docs/hzgt/core/sysutils.md)

### 工具模块文档

- [MQTT通信 (MQTT.md)](docs/hzgt/tools/MQTT.md)
- [FTP服务 (FTP.md)](docs/hzgt/tools/FTP.md)
- [文件服务器 (FileServer.md)](docs/hzgt/tools/FileServer.md)
- [INI文件操作 (INI.md)](docs/hzgt/tools/INI.md)
- [函数和类注册器 (REGISTER.md)](docs/hzgt/tools/REGISTER.md)
- [SMTP邮件发送 (SMTP.md)](docs/hzgt/tools/SMTP.md)
- SQL数据库操作
  - [MySQL操作 (MYSQL.md)](docs/hzgt/tools/SQL/MYSQL.md)
  - [SQLite操作 (SQLITE.md)](docs/hzgt/tools/SQL/SQLITE.md)
  - [SQL历史记录 (sqlhistory.md)](docs/hzgt/tools/SQL/sqlhistory.md)

## 命令行工具

hzgt 提供了命令行工具，可以通过以下命令使用：

```bash
# 快速文件服务器
hzgt fs

# 快速创建FTP服务端
hzgt ftps

# 输出本地局域网内的IP地址列表
hzgt ips
```

## 许可证

本项目采用 MIT 许可证，详情请查看 LICENSE 文件。