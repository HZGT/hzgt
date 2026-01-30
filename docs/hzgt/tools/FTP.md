# FTP.py 文档

## 导航目录

- [Ftpserver](#ftpserver)
  - [add_user()](#add_user)
  - [remove_user()](#remove_user)
  - [correct_user()](#correct_user)
  - [set_log()](#set_log)
  - [start()](#start)
  - [shutdown()](#shutdown)
- [Ftpclient](#ftpclient)
  - [dir()](#dir)
  - [pwd()](#pwd)
  - [quit()](#quit)
  - [getfile()](#getfile)
  - [upload()](#upload)
  - [size()](#size)
  - [list_show()](#list_show)
  - [nlst()](#nlst)
  - [rmd()](#rmd)
  - [delete()](#delete)
  - [rename()](#rename)
  - [cwd()](#cwd)
  - [mkd()](#mkd)

## 类说明

### Ftpserver

**功能**：创建 FTP 服务端，支持添加用户、设置权限和启动 FTP 服务。

**构造方法**：
```python
from hzgt.tools import Ftpserver

fs = Ftpserver()
```

**参数**：无

**说明**：Ftpserver 构造方法不需要任何参数，创建实例后通过调用其他方法来配置和启动 FTP 服务。

**方法**：

#### add_user()
**功能**：添加用户权限和路径，可以为不同的用户添加不同的目录和权限。如果 username 为空，则添加匿名用户 anonymous。

**参数**：
- `homedir`：目录路径
- `username`：用户名称，如果为空，则添加匿名用户 anonymous
- `password`：用户密码
- `perm`：权限组合体，"elradfmw" 表示对应的所有权限

**权限说明**：
- 读取权限:
  - "e" = 更改目录 (CWD 命令)
  - "l" = 列出文件 (LIST、NLST、STAT、MLSD、MLST、SIZE、MDTM 命令)
  - "r" = 从服务器检索文件 (RETR 命令)

- 写入权限:
  - "a" = 将数据附加到现有文件 (APPE 命令)
  - "d" = 删除文件或目录 (DELE、RMD 命令)
  - "f" = 重命名文件或目录 (RNFR、RNTO 命令)
  - "m" = 创建目录 (MKD 命令)
  - "w" = 将文件存储到服务器 (STOR、STOU 命令)
  - "M" = 更改文件模式 (SITE CHMOD 命令)
  - "T" = 更新文件上次修改时间 (MFMT 命令)

**使用示例**：
```python
# 添加具有所有权限的用户
fs.add_user("/path/to/share", "user", "123456", "elradfmw")

# 添加只读权限的用户
fs.add_user("/path/to/read-only", "guest", "password", "elr")

# 添加匿名用户
fs.add_user("/path/to/public", "", "")
```

#### remove_user()
**功能**：删除用户。

**参数**：
- `username`：待删除的用户名

**使用示例**：
```python
fs.remove_user("guest")
```

#### correct_user()
**功能**：修正用户信息。

**参数**：
- `oldusername`：需要修正的用户名
- `newdir`：可选，新路径
- `newusername`：可选，新用户名
- `newpassword`：可选，新密码
- `newperm`：可选，新权限组合体

**使用示例**：
```python
# 修改用户密码
fs.correct_user("user", newpassword="newpassword")

# 修改用户权限
fs.correct_user("user", newperm="elradfmw")
```

#### set_log()
**功能**：设置 FTP 服务器日志。

**参数**：
- `logfilename`：FTP日志路径，默认 "ftps.log"
- `level`：日志级别，默认 2(INFO)
- `encoding`：编码，默认 utf-8

**使用示例**：
```python
fs.set_log("ftp_server.log", level=1)  # 设置为DEBUG级别
```

#### start()
**功能**：开启 FTP 服务器。

**参数**：
- `host_res`：IP地址，默认 "127.0.0.1"
- `port`：端口，默认 2121
- `passive_port_range`：被动端口范围，默认 range(6000, 7000)
- `read_limit`：上传速度设置，单位 kB/s，默认 300
- `write_limit`：下载速度设置，单位 kB/s，默认 300
- `max_cons`：最大连接数，默认 30
- `max_cons_per_ip`：IP最大连接数，默认 10

**使用示例**：
```python
# 启动FTP服务器
fs.start(host_res="0.0.0.0", port=2121)

# 启动带速度限制的FTP服务器
fs.start(host_res="0.0.0.0", port=2121, read_limit=100, write_limit=100)
```

#### shutdown()
**功能**：关闭服务器。

**使用示例**：
```python
fs.shutdown()
```

**完整使用示例**：

```python
from hzgt.tools import Ftpserver

# 创建FTP服务器实例
fs = Ftpserver()

# 添加用户
fs.add_user("/path/to/share", "user", "123456", "elradfmw")
fs.add_user("/path/to/public", perm="elr")  # 匿名用户

# 设置日志
fs.set_log("ftps.log")

# 启动服务器
print("FTP服务器启动中...")
print("使用 Ctrl+C 停止服务器")
try:
    fs.start(host_res="0.0.0.0", port=2121)
except KeyboardInterrupt:
    print("\n正在关闭FTP服务器...")
    fs.shutdown()
    print("FTP服务器已关闭")
```

### Ftpclient

**功能**：创建 FTP 客户端，支持连接 FTP 服务器、上传下载文件等操作。

**构造方法参数**：
- `host`：目标主机IP
- `port`：端口，默认 2121
- `username`：用户昵称，默认为 anonymous
- `password`：密码
- `encoding`：默认编码为 UTF-8

**方法**：

#### dir()
**功能**：打印目录的文件信息。

**使用示例**：
```python
ftp_client.dir()
```

#### pwd()
**功能**：获取当前的工作目录。

**返回值**：当前的工作目录路径

**使用示例**：
```python
current_dir = ftp_client.pwd()
print(f"当前目录: {current_dir}")
```

#### quit()
**功能**：关闭连接。

**使用示例**：
```python
ftp_client.quit()
```

#### getfile()
**功能**：从服务器下载文件保存至本地。

**参数**：
- `server_filename`：服务器上待下载的文件，文件格式: "/path/to/thing.txt"
- `savepath`：保存路径，默认保存在同目录下新建文件夹 "FTP_Files"
- `savename`：保存的文件名，为空则默认使用服务器文件名
- `blocksize`：下载块大小

**使用示例**：
```python
# 下载文件到默认路径
ftp_client.getfile("/public/file.txt")

# 下载文件到指定路径并自定义文件名
ftp_client.getfile("/public/data.zip", savepath="downloads", savename="backup.zip")
```

#### upload()
**功能**：上传文件至当前工作目录。

**参数**：
- `local_file`：本地文件路径
- `server_savename`：新命名，默认使用本地文件名
- `blocksize`：上传块大小

**使用示例**：
```python
# 上传文件到服务器
ftp_client.upload("local_file.txt")

# 上传文件并自定义服务器文件名
ftp_client.upload("local_data.csv", server_savename="data_2024.csv")
```

#### size()
**功能**：获取服务器上文件的大小。

**参数**：
- `sname`：目标文件路径

**返回值**：文件大小（字节）

**使用示例**：
```python
file_size = ftp_client.size("/public/file.txt")
print(f"文件大小: {file_size} 字节")
```

#### list_show()
**功能**：打印服务器目录里的文件列表。

**参数**：
- `spath`：服务器的目录，默认查看当前工作目录

**使用示例**：
```python
# 查看当前目录
ftp_client.list_show()

# 查看指定目录
ftp_client.list_show("/public")
```

#### nlst()
**功能**：获取目标目录中所有的文件夹/文件。

**参数**：
- `spath`：目标目录

**返回值**：所有文件夹/文件组成的列表

**使用示例**：
```python
files = ftp_client.nlst("/public")
print("目录内容:")
for file in files:
    print(f"  - {file}")
```

#### rmd()
**功能**：删除目标目录。

**参数**：
- `spath`：目标目录

**使用示例**：
```python
ftp_client.rmd("/temp")
```

#### delete()
**功能**：删除远程文件。

**参数**：
- `sname`：远程文件名

**使用示例**：
```python
ftp_client.delete("/public/old_file.txt")
```

#### rename()
**功能**：将文件 `oldsname` 修改名称为 `newsname`。

**参数**：
- `oldsname`：旧文件名
- `newsname`：新文件名

**使用示例**：
```python
ftp_client.rename("/public/data.txt", "/public/data_updated.txt")
```

#### cwd()
**功能**：设置FTP当前操作的路径。

**参数**：
- `spath`：需要设置为当前工作路径的路径

**使用示例**：
```python
ftp_client.cwd("/public")
print(f"当前目录: {ftp_client.pwd()}")
```

#### mkd()
**功能**：创建新目录。

**参数**：
- `spath`：新目录路径

**使用示例**：
```python
ftp_client.mkd("/public/new_folder")
```

**完整使用示例**：

```python
from hzgt.tools import Ftpclient

# 使用with语句自动关闭连接
with Ftpclient(
    host="192.168.1.100",
    port=2121,
    username="user",
    password="123456"
) as ftp_client:
    # 查看当前目录
    print("=== 当前目录 ===")
    ftp_client.dir()
    
    # 列出指定目录内容
    print("\n=== 公共目录内容 ===")
    ftp_client.list_show("/public")
    
    # 上传文件
    print("\n=== 上传文件 ===")
    ftp_client.upload("local_file.txt", server_savename="uploaded_file.txt")
    
    # 下载文件
    print("\n=== 下载文件 ===")
    ftp_client.getfile("/public/sample.zip", savepath="downloads")
    
    # 创建目录
    print("\n=== 创建目录 ===")
    ftp_client.mkd("/public/test")
    print("目录创建成功")
    
    # 删除文件
    print("\n=== 删除文件 ===")
    ftp_client.delete("/public/test_file.txt")
    print("文件删除成功")

print("FTP操作完成，连接已关闭")
```