# sysutils.py 文档

## 导航目录

- [is_admin()](#is_admin)
- [require_admin()](#require_admin)
- [run_as_admin()](#run_as_admin)
- [check_admin_and_prompt()](#check_admin_and_prompt)
- [execute_command()](#execute_command)

## 函数说明

### is_admin()

**功能**：检查当前是否以管理员权限运行。

**返回值**：`bool` - Windows系统下返回是否具有管理员权限，其他系统返回是否为root用户

**使用示例**：
```python
from hzgt import is_admin

if is_admin():
    print("当前以管理员权限运行")
else:
    print("当前没有管理员权限")
```

### require_admin()

**功能**：请求以管理员权限重新运行程序。

**参数**：
- `message`：可选的提示信息，用于告知用户为什么需要管理员权限

**返回值**：`None`

**使用示例**：
```python
from hzgt import require_admin

# 请求管理员权限
require_admin("需要管理员权限来修改系统设置")

# 后续代码会在管理员权限下执行
print("现在以管理员权限运行")
```

### run_as_admin()

**功能**：装饰器，确保被装饰的函数以管理员权限运行。

**参数**：
- `func`：需要管理员权限的函数

**返回值**：装饰后的函数

**使用示例**：
```python
from hzgt import run_as_admin

@run_as_admin
def install_service():
    """安装系统服务"""
    print("正在安装服务...")
    # 安装服务的代码

# 调用函数时会自动检查并请求管理员权限
install_service()
```

### check_admin_and_prompt()

**功能**：检查管理员权限并提示用户。

**参数**：
- `operation_name`：操作名称，用于提示信息

**返回值**：`bool` - 是否具有管理员权限

**使用示例**：
```python
from hzgt import check_admin_and_prompt

if check_admin_and_prompt("修改系统配置"):
    # 具有管理员权限，执行操作
    print("执行系统配置修改")
else:
    # 没有管理员权限，退出或执行其他操作
    print("无法执行操作，需要管理员权限")
```

### execute_command()

**功能**：执行命令并返回生成器，逐行输出结果。支持超时设置、编码处理和异常捕获。

**参数**：
- `_cmd` (Union[str, List[str]])：要执行的命令，可以是字符串或字符串列表
- `encoding` (Optional[str])：输出编码，默认为系统默认编码
- `errors` (str)：编码错误处理方式，默认为'replace'
- `timeout` (Optional[float])：超时时间（秒），None表示无超时限制

**返回值**：`Generator[str, None, None]` - 命令输出的每一行。当命令执行出错时，会通过生成器产生错误信息，同时重新抛出异常。

**异常**：
- `subprocess.TimeoutExpired`：命令执行超时
- `subprocess.CalledProcessError`：命令执行失败
- `FileNotFoundError`：命令不存在

**使用示例**：
```python
from hzgt import execute_command
import subprocess

# 执行简单命令
print("执行 'echo Hello World'")
for output in execute_command("echo Hello World"):
    print(f"输出: {output}")

# 执行列出目录的命令
print("\n执行目录列表命令")
import sys
cmd = "dir" if sys.platform.startswith('win') else "ls -la"
for output in execute_command(cmd):
    print(f"输出: {output}")

# 使用列表形式的命令
print("\n使用列表形式的命令")
if sys.platform.startswith('win'):
    cmd_list = ["cmd", "/c", "echo", "Hello from list"]
else:
    cmd_list = ["echo", "Hello from list"]

for output in execute_command(cmd_list):
    print(f"输出: {output}")

# 带超时的命令
print("\n带超时的命令")
try:
    # 执行一个可能耗时的命令，设置3秒超时
    if sys.platform.startswith('win'):
        cmd = "ping -n 10 127.0.0.1"  # Windows ping命令
    else:
        cmd = "ping -c 10 127.0.0.1"  # Linux/Mac ping命令

    for output in execute_command(cmd, timeout=3.0):
        print(f"输出: {output}")
except subprocess.TimeoutExpired:
    print("命令执行超时")
```