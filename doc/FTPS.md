
---
`类[class]: Ftpserver()`
---

`Ftpserver` 类提供了 `FTP服务端` 的操作API.

The `Ftpserver` class provides the API of the `FTP server`.

---
- [构造函数参数](#constructor-parameters)
- [核心方法](#core-methods)
- [使用示例](#examples)
---

### constructor parameters
### 构造函数参数
无

### core methods
### 核心方法
1. `add_user(homedir: str, username: str = "anonymous", password: str = "", perm: str = "")`
- 功能: 添加用户
- 参数:
- `homedir`: 用户家目录
- `username`: 用户名 默认为 **anonymous**
- `password`: 用户密码 默认为 **空字符串**
- `perm`: [用户权限](#user-perm) 默认为 **空字符串**

2. `start(host_res: str = "127.0.0.1", port: int = 2121,
              passive_port_range: None = range(6000, 7000), read_limit: int = 300, write_limit: int = 300,
              max_cons: int = 30, max_cons_per_ip: int = 10)`
- 功能: 启动FTP服务 [阻塞运行]
- 参数:
- `host_res`: 服务器地址 默认为 **127.0.0.1**
- `port`: 服务器端口 默认为 **2121**
- `passive_port_range`: 被动端口范围 默认为 **6000-7000**
- `read_limit`: 读取限制 默认为 **300**
- `write_limit`: 写入限制 默认为 **300**
- `max_cons`: 最大连接数 默认为 **30**
- `max_cons_per_ip`: 每个IP的最大连接数 默认为 **10**

### examples
### 使用示例
```python
from hzgt.tools import Ftpserver

ftps = Ftpserver()
ftps.add_user(homedir=".", username="admin", password="123456", perm="elradfmwMT")
ftps.start()  # 阻塞运行

# 此时可以使用ftp客户端连接服务器
```

## userperm
## 用户权限
| 权限 | 描述                                           |
|----|----------------------------------------------|
| e  | 更改目录(CWD 命令)                                 |
| l  | 列出文件 (LIST、NLST、STAT、MLSD、MLST、SIZE、MDTM 命令) |
| r  | 从服务器检索文件 (RETR 命令)                           |
| a  | 将数据附加到现有文件 (APPE 命令)                         |
| d  | 删除文件或目录 (DELE、RMD 命令)                        |
| f  | 重命名文件或目录 (RNFR、RNTO 命令)                      |
| m  | 创建目录 (MKD 命令)                                |
| w  | 将文件存储到服务器 (STOR、STOU 命令)                     |
| M  | 更改文件模式 (SITE CHMOD 命令)                       |
| T  | 更新文件上次修改时间 (MFMT 命令)                         |
