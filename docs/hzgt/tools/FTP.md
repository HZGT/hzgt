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
  - [基本操作](#基本操作)
    - [dir()](#dir)
    - [pwd()](#pwd)
    - [quit()](#quit)
    - [cwd()](#cwd)
    - [nlst() / list_files()](#nlst--list_files)
    - [list_details()](#list_details)
    - [rename()](#rename)
    - [delete()](#delete)
    - [rmd()](#rmd)
    - [mkd()](#mkd)
    - [size()](#size)
    - [exists()](#exists)
    - [is_dir()](#is_dir)
    - [is_file()](#is_file)
  - [传输模式](#传输模式)
    - [set_passive()](#set_passive)
    - [set_mode()](#set_mode)
  - [文件上传](#文件上传)
    - [upload()](#upload)
    - [upload_dir()](#upload_dir)
    - [upload_files()](#upload_files)
  - [文件下载](#文件下载)
    - [download()](#download)
    - [download_dir()](#download_dir)
    - [download_files()](#download_files)
  - [目录管理](#目录管理)
    - [rmtree()](#rmtree)
  - [连接管理](#连接管理)
    - [send_command()](#send_command)
    - [chmod()](#chmod)
    - [is_connected](#is_connected)
    - [keep_alive()](#keep_alive)
    - [reconnect()](#reconnect)

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
    fs.start(host="0.0.0.0", port=2121)
except KeyboardInterrupt:
    print("\n正在关闭FTP服务器...")
    fs.shutdown()
    print("FTP服务器已关闭")
```

---

### Ftpclient

**功能**：创建 FTP 客户端，支持连接 FTP 服务器、文件上传下载（带进度条）、目录递归操作、断点续传、批量操作等功能。

**构造方法参数**：
- `host`：目标主机IP
- `port`：端口，默认 2121
- `username`：用户昵称，默认为 anonymous
- `password`：密码
- `timeout`：连接超时时间（秒），默认 30
- `encoding`：默认编码为 UTF-8
- `passive`：是否使用被动模式，默认 True
- `logger`：自定义日志器

**使用示例**：
```python
from hzgt.tools import Ftpclient

# 基本连接
ftp_client = Ftpclient("192.168.1.100", 2121, "user", "123456")

# 使用 with 语句（推荐）
with Ftpclient("192.168.1.100", 2121, "user", "123456") as ftp_client:
    # 自动关闭连接
    pass
```

---

## 基本操作

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

#### cwd()
**功能**：切换远程工作目录。

**参数**：
- `path`：目标路径

**返回值**：服务器返回的响应字符串

**使用示例**：
```python
ftp_client.cwd("/public")
print(f"当前目录: {ftp_client.pwd()}")
```

#### nlst() / list_files()
**功能**：获取指定目录下的文件和文件夹名称列表（NLST 命令）。

**参数**：
- `path`：远程目录路径，默认为当前目录

**返回值**：名称列表

**使用示例**：
```python
files = ftp_client.nlst("/public")
print("目录内容:")
for file in files:
    print(f"  - {file}")
```

#### list_details()
**功能**：获取指定目录下文件和文件夹的详细信息（使用 MLSD 命令）。

**参数**：
- `path`：远程目录路径

**返回值**：字典列表，每个字典包含 name, type, size, modify, perm 等字段

**使用示例**：
```python
items = ftp_client.list_details("/public")
for item in items:
    print(f"{item['name']} - 类型: {item.get('type')}, 大小: {item.get('size')}")
```

#### rename()
**功能**：重命名远程文件或目录。

**参数**：
- `old`：旧文件名
- `new`：新文件名

**使用示例**：
```python
ftp_client.rename("/public/data.txt", "/public/data_updated.txt")
```

#### delete()
**功能**：删除远程文件。

**参数**：
- `filename`：远程文件名

**使用示例**：
```python
ftp_client.delete("/public/old_file.txt")
```

#### rmd()
**功能**：删除空目录。

**参数**：
- `dirname`：目标目录

**使用示例**：
```python
ftp_client.rmd("/temp")
```

#### mkd()
**功能**：创建新目录。

**参数**：
- `dirname`：新目录路径

**使用示例**：
```python
ftp_client.mkd("/public/new_folder")
```

#### size()
**功能**：获取远程文件大小（字节）。

**参数**：
- `filename`：目标文件路径

**返回值**：文件大小（字节）

**使用示例**：
```python
file_size = ftp_client.size("/public/file.txt")
print(f"文件大小: {file_size} 字节")
```

#### exists()
**功能**：检查远程文件或目录是否存在。

**参数**：
- `path`：远程路径

**返回值**：True 如果存在，否则 False

**使用示例**：
```python
if ftp_client.exists("/public/file.txt"):
    print("文件存在")
else:
    print("文件不存在")
```

#### is_dir()
**功能**：检查远程路径是否为目录。

**参数**：
- `path`：远程路径

**返回值**：True 如果是目录，否则 False

**使用示例**：
```python
if ftp_client.is_dir("/public/folder"):
    print("这是一个目录")
```

#### is_file()
**功能**：检查远程路径是否为文件。

**参数**：
- `path`：远程路径

**返回值**：True 如果是文件，否则 False

**使用示例**：
```python
if ftp_client.is_file("/public/file.txt"):
    print("这是一个文件")
```

---

## 传输模式

#### set_passive()
**功能**：设置是否使用被动模式。

**参数**：
- `passive`：True 启用被动模式，False 启用主动模式

**使用示例**：
```python
ftp_client.set_passive(True)  # 启用被动模式
```

#### set_mode()
**功能**：设置传输模式：'I' 二进制，'A' ASCII。

**参数**：
- `mode`：'I' 或 'A'

**使用示例**：
```python
ftp_client.set_mode('I')  # 设置为二进制模式
```

---

## 文件上传

#### upload()
**功能**：上传文件到当前远程目录，支持断点续传和进度条显示。

**参数**：
- `local_file`：本地文件路径
- `remote_name`：远程文件名，默认使用本地文件名
- `blocksize`：传输块大小（字节），默认 8192
- `callback`：进度回调函数，接收 (已传输字节, 总字节)
- `resume`：是否断点续传，默认 False

**使用示例**：
```python
# 基本上传
ftp_client.upload("local_file.txt")

# 上传并自定义远程文件名
ftp_client.upload("local_data.csv", remote_name="data_2024.csv")

# 断点续传上传
ftp_client.upload("large_file.zip", resume=True)

# 带自定义回调的上传
def progress_callback(sent, total):
    print(f"进度: {sent}/{total} bytes")

ftp_client.upload("file.txt", callback=progress_callback)
```

#### upload_dir()
**功能**：递归上传本地目录到远程，自动创建目录结构。

**参数**：
- `local_dir`：本地目录路径
- `remote_dir`：远程目标目录，默认为当前目录下的同名文件夹
- `blocksize`：传输块大小，默认 8192
- `callback`：每个文件上传进度的回调，接收 (相对路径, 已传字节, 总字节)

**使用示例**：
```python
# 上传整个目录
ftp_client.upload_dir("./local_folder", "/remote/folder")

# 带进度回调的上传
def file_progress(rel_path, sent, total):
    print(f"{rel_path}: {sent}/{total} bytes")

ftp_client.upload_dir("./src", "/backup/src", callback=file_progress)
```

#### upload_files()
**功能**：批量上传多个文件到远程目录。

**参数**：
- `local_files`：本地文件路径列表
- `remote_dir`：远程目标目录
- `blocksize`：传输块大小，默认 8192
- `callback`：每个文件上传进度的回调，接收 (文件名, 已传字节, 总字节)

**使用示例**：
```python
# 批量上传文件
files = ["file1.txt", "file2.csv", "data.json"]
ftp_client.upload_files(files, "/uploads")

# 带进度回调
def file_progress(fname, sent, total):
    print(f"{fname}: {sent}/{total}")

ftp_client.upload_files(files, callback=file_progress)
```

---

## 文件下载

#### download()
**功能**：下载远程文件到本地，支持断点续传和进度条显示。

**参数**：
- `remote_file`：远程文件路径（可以是绝对路径或相对当前目录）
- `local_path`：本地保存目录，默认 "."
- `local_name`：本地文件名，默认使用远程文件名
- `blocksize`：传输块大小，默认 8192
- `resume`：是否断点续传，默认 False
- `callback`：进度回调，接收 (已传字节, 总字节)

**使用示例**：
```python
# 基本下载
ftp_client.download("/public/file.txt", "./downloads")

# 断点续传下载
ftp_client.download("/public/large_file.zip", resume=True)

# 自定义文件名
ftp_client.download("/public/data.csv", "./data", local_name="backup.csv")

# 带进度回调
def progress_callback(sent, total):
    print(f"进度: {sent}/{total} bytes")

ftp_client.download("/public/file.txt", callback=progress_callback)
```

#### download_dir()
**功能**：递归下载远程目录到本地，保持目录结构。

**参数**：
- `remote_dir`：远程目录路径
- `local_dir`：本地保存根目录，默认 "."
- `blocksize`：传输块大小，默认 8192
- `callback`：每个文件下载进度的回调，接收 (相对路径, 已传字节, 总字节)

**使用示例**：
```python
# 下载整个目录
ftp_client.download_dir("/remote/folder", "./local_folder")

# 带进度回调
def file_progress(rel_path, sent, total):
    print(f"{rel_path}: {sent}/{total} bytes")

ftp_client.download_dir("/backup/src", "./src", callback=file_progress)
```

#### download_files()
**功能**：批量下载多个远程文件到本地目录。

**参数**：
- `remote_files`：远程文件路径列表
- `local_dir`：本地保存根目录，默认 "."
- `blocksize`：传输块大小，默认 8192
- `resume`：是否断点续传，默认 False
- `callback`：每个文件下载进度的回调，接收 (文件名, 已传字节, 总字节)

**使用示例**：
```python
# 批量下载文件
files = ["/public/file1.txt", "/public/file2.csv", "/public/data.json"]
ftp_client.download_files(files, "./downloads")

# 断点续传批量下载
ftp_client.download_files(files, "./downloads", resume=True)

# 带进度回调
def file_progress(fname, sent, total):
    print(f"{fname}: {sent}/{total}")

ftp_client.download_files(files, callback=file_progress)
```

---

## 目录管理

#### rmtree()
**功能**：递归删除远程目录及其所有内容。

**参数**：
- `remote_dir`：远程目录路径

**使用示例**：
```python
ftp_client.rmtree("/temp/old_folder")
```

---

## 连接管理

#### send_command()
**功能**：发送原始 FTP 命令并返回响应。

**参数**：
- `cmd`：FTP 命令字符串（如 "SYST"）

**返回值**：服务器响应字符串

**使用示例**：
```python
response = ftp_client.send_command("SYST")
print(f"系统类型: {response}")
```

#### chmod()
**功能**：修改远程文件或目录的权限（SITE CHMOD 命令）。

**参数**：
- `path`：远程路径
- `mode`：权限模式（八进制，如 0o755）

**使用示例**：
```python
ftp_client.chmod("/public/script.sh", 0o755)  # 设置为可执行
```

#### is_connected
**功能**：检查连接是否活跃（属性）。

**返回值**：True 如果连接正常，否则 False

**使用示例**：
```python
if ftp_client.is_connected:
    print("连接正常")
else:
    print("连接已断开")
```

#### keep_alive()
**功能**：保持连接活跃（定期发送 NOOP 命令）。注意：这是一个阻塞方法，适合在后台线程中使用。

**参数**：
- `interval`：发送 NOOP 的间隔秒数，默认 60

**使用示例**：
```python
import threading

# 在后台线程中保持连接活跃
thread = threading.Thread(target=ftp_client.keep_alive, args=(60,))
thread.daemon = True
thread.start()
```

#### reconnect()
**功能**：重新连接服务器（使用当前参数）。

**使用示例**：
```python
# 重新连接
ftp_client.reconnect()
print("重新连接成功")
```

---

## 完整使用示例

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
    files = ftp_client.nlst("/public")
    for f in files:
        print(f"  - {f}")
    
    # 检查文件是否存在
    if ftp_client.exists("/public/sample.txt"):
        print("\n文件存在，开始下载...")
        # 下载文件（支持断点续传）
        ftp_client.download("/public/sample.txt", "./downloads", resume=True)
    
    # 上传文件（支持断点续传）
    print("\n=== 上传文件 ===")
    ftp_client.upload("local_file.txt", resume=True)
    
    # 批量上传
    print("\n=== 批量上传 ===")
    files_to_upload = ["file1.txt", "file2.csv"]
    ftp_client.upload_files(files_to_upload, "/uploads")
    
    # 上传整个目录
    print("\n=== 上传目录 ===")
    ftp_client.upload_dir("./src", "/backup/src")
    
    # 创建目录
    print("\n=== 创建目录 ===")
    ftp_client.mkd("/public/test")
    print("目录创建成功")
    
    # 删除文件
    print("\n=== 删除文件 ===")
    ftp_client.delete("/public/test_file.txt")
    print("文件删除成功")
    
    # 检查连接状态
    if ftp_client.is_connected:
        print("\n连接状态: 正常")

print("FTP操作完成，连接已关闭")
```
