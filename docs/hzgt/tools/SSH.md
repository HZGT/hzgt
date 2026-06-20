# SSH.py 文档

## 导航目录

- [SSHClient](#sshclient)
  - [构造方法](#构造方法)
  - [connect()](#connect)
  - [execute_command()](#execute_command)
  - [invoke_shell()](#invoke_shell)
  - [sftp_upload()](#sftp_upload)
  - [sftp_download()](#sftp_download)
  - [cd()](#cd)
  - [close()](#close)

## 类说明

### SSHClient

**功能**：增强的 SSH 客户端，支持密码/私钥认证、交互式 Shell、SFTP 文件传输、连接保活等功能。

**构造方法参数**：
- `hostname`：SSH 服务器地址
- `port`：端口，默认 22
- `username`：用户名
- `password`：密码（可选）
- `key_filename`：私钥文件路径（字符串或列表，可选）
- `passphrase`：私钥密码（可选）
- `look_for_keys`：是否自动查找密钥，默认 True
- `allow_agent`：是否允许 SSH agent，默认 True
- `hostkey_policy`：主机密钥验证策略：'strict'/'auto'/'warning'，默认 'warning'
- `expected_hostkey`：期望的主机密钥指纹（可选）
- `timeout`：连接超时时间（秒），默认 10
- `keepalive_interval`：保活间隔（秒），0 表示禁用，默认 0
- `logger`：自定义日志器

**使用示例**：
```python
from hzgt.tools import SSHClient

# 密码认证
ssh = SSHClient("192.168.1.100", username="user", password="123456")

# 私钥认证
ssh = SSHClient("192.168.1.100", username="user", key_filename="~/.ssh/id_rsa")

# 使用 with 语句（推荐）
with SSHClient("192.168.1.100", username="user", password="123456") as ssh:
    # 自动关闭连接
    pass
```

---

## 方法说明

#### connect()
**功能**：连接到 SSH 服务器。

**返回值**：True 如果连接成功，否则 False

**使用示例**：
```python
ssh = SSHClient("192.168.1.100", username="user", password="123456")
if ssh.connect():
    print("连接成功")
else:
    print("连接失败")
```

#### execute_command()
**功能**：执行远程命令，支持实时输出和伪终端。

**参数**：
- `command`：要执行的命令
- `timeout`：超时时间（秒，可选）
- `cwd`：工作目录（可选）
- `stream`：是否实时打印输出，默认 False
- `pty`：是否分配伪终端，默认 False

**返回值**：(stdout, stderr, exit_code) 元组

**使用示例**：
```python
# 基本命令执行
stdout, stderr, code = ssh.execute_command("ls -la")
print(f"退出码: {code}")
print(stdout)

# 指定工作目录
stdout, stderr, code = ssh.execute_command("pwd", cwd="~/Documents")

# 实时输出
ssh.execute_command("tail -f /var/log/syslog", stream=True)

# 使用伪终端（解决 sudo 等问题）
ssh.execute_command("sudo apt update", pty=True)
```

#### invoke_shell()
**功能**：启动交互式 Shell，用户可以直接在终端中输入命令。

**参数**：
- `term`：终端类型，默认 'vt100'
- `width`：终端宽度，默认 80
- `height`：终端高度，默认 24

**使用示例**：
```python
# 启动交互式 Shell
ssh.invoke_shell()
# 现在可以在终端中直接输入命令，包括 sudo 密码
```

#### sftp_upload()
**功能**：通过 SFTP 上传文件到远程服务器，支持进度条和断点续传。

**参数**：
- `local_path`：本地文件路径
- `remote_path`：远程文件路径
- `callback`：进度回调函数（可选）
- `resume`：是否断点续传，默认 False

**使用示例**：
```python
# 基本上传
ssh.sftp_upload("local_file.txt", "/remote/path/file.txt")

# 带进度回调
def progress(sent, total):
    print(f"进度: {sent}/{total} bytes")

ssh.sftp_upload("large_file.zip", "/backup/large_file.zip", callback=progress)

# 断点续传
ssh.sftp_upload("file.zip", "/backup/file.zip", resume=True)
```

#### sftp_download()
**功能**：通过 SFTP 从远程服务器下载文件，支持进度条和断点续传。

**参数**：
- `remote_path`：远程文件路径
- `local_path`：本地保存路径
- `callback`：进度回调函数（可选）
- `resume`：是否断点续传，默认 False

**使用示例**：
```python
# 基本下载
ssh.sftp_download("/remote/file.txt", "./local_file.txt")

# 带进度回调
def progress(sent, total):
    print(f"进度: {sent}/{total} bytes")

ssh.sftp_download("/backup/large_file.zip", "./large_file.zip", callback=progress)

# 断点续传
ssh.sftp_download("/backup/file.zip", "./file.zip", resume=True)
```

#### cd()
**功能**：临时切换远程工作目录的上下文管理器。

**参数**：
- `path`：目标目录路径

**使用示例**：
```python
# 临时切换到指定目录执行命令
with ssh.cd("~/Documents"):
    stdout, _, _ = ssh.execute_command("pwd")
    print(stdout)  # 输出: /home/user/Documents

# 退出上下文后恢复原目录
stdout, _, _ = ssh.execute_command("pwd")
print(stdout)  # 输出: /home/user
```

#### close()
**功能**：关闭 SSH 连接。

**使用示例**：
```python
ssh.close()
```

---

## 完整使用示例

```python
from hzgt.tools import SSHClient

# 使用 with 语句自动管理连接
with SSHClient(
    hostname="192.168.1.100",
    port=22,
    username="user",
    password="123456",
    keepalive_interval=30  # 每30秒发送保活
) as ssh:
    if not ssh.connect():
        print("连接失败")
        exit(1)
    
    print("=== 执行命令 ===")
    # 执行基本命令
    stdout, stderr, code = ssh.execute_command("uname -a")
    print(f"系统信息:\n{stdout}")
    
    # 指定工作目录执行命令
    print("\n=== 指定工作目录 ===")
    with ssh.cd("~/Documents"):
        stdout, _, _ = ssh.execute_command("ls -la")
        print(stdout)
    
    # 实时输出
    print("\n=== 实时输出 ===")
    ssh.execute_command("df -h", stream=True)
    
    # 上传文件
    print("\n=== 上传文件 ===")
    ssh.sftp_upload("local_file.txt", "/tmp/local_file.txt")
    
    # 下载文件
    print("\n=== 下载文件 ===")
    ssh.sftp_download("/tmp/remote_file.txt", "./remote_file.txt")
    
    # 启动交互式 Shell（会阻塞直到退出）
    # ssh.invoke_shell()

print("SSH 会话已结束")
```

---

## 功能特性

1. **多种认证方式**：支持密码、私钥、SSH Agent 认证
2. **主机密钥验证**：提供严格、自动、警告三种策略
3. **交互式 Shell**：支持直接在终端输入命令
4. **SFTP 文件传输**：支持上传下载，带进度条和断点续传
5. **连接保活**：防止长时间无操作导致连接断开
6. **工作目录管理**：支持临时切换目录的上下文管理器
7. **实时输出**：支持流式输出，适合长时间运行的命令
8. **伪终端支持**：解决 sudo 等需要终端环境的命令
9. **路径扩展**：自动扩展 ~ 为用户家目录
10. **集成日志**：所有操作都有详细的日志记录

## 注意事项

- 使用 with 语句可以自动管理连接的生命周期
- 启用 keepalive 可以防止防火墙断开空闲连接
- 对于需要交互的命令（如 sudo），使用 `pty=True` 或 `invoke_shell()`
- SFTP 传输大文件时建议使用进度回调监控传输状态
- 生产环境建议使用 'strict' 或 'warning' 主机密钥策略
