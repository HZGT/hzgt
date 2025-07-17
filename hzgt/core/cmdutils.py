import ctypes
import os
import subprocess
import sys
import threading
from typing import Generator, Union, Optional, List


def is_admin() -> bool:
    """
    检查当前是否以管理员权限运行

    Returns:
        bool: Windows系统下返回是否具有管理员权限，其他系统返回是否为root用户
    """
    try:
        if sys.platform.startswith('win'):
            # Windows系统：检查管理员权限
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            # Unix/Linux/macOS系统：检查是否为root用户
            return os.geteuid() == 0
    except AttributeError:
        # 如果无法检查权限，默认返回False
        return False
    except Exception:
        # 其他异常情况，默认返回False
        return False


def require_admin(message: Optional[str] = None) -> None:
    """
    请求以管理员权限重新运行程序

    Args:
        message: 可选的提示信息，用于告知用户为什么需要管理员权限
    """
    if is_admin():
        # 已经是管理员权限，无需操作
        return

    # 显示提示信息
    if message:
        print(f"需要管理员权限: {message}")
    else:
        print("此操作需要管理员权限，正在请求提权...")

    try:
        if sys.platform.startswith('win'):
            # Windows系统：使用UAC请求提权
            _require_admin_windows()
        else:
            # Unix/Linux/macOS系统：提示用户使用sudo
            _require_admin_unix()
    except Exception as e:
        print(f"请求管理员权限失败: {e}")
        sys.exit(1)


def _require_admin_windows() -> None:
    """Windows系统下请求管理员权限"""
    try:
        # 重新启动程序并请求UAC提权
        result = ctypes.windll.shell32.ShellExecuteW(
            None,  # hwnd
            'runas',  # lpOperation - 以管理员身份运行
            sys.executable,  # lpFile - Python解释器路径
            ' '.join(sys.argv),  # lpParameters - 命令行参数
            None,  # lpDirectory
            1  # nShowCmd - SW_SHOWNORMAL
        )

        # ShellExecuteW返回值大于32表示成功
        if result > 32:
            print("正在以管理员权限重新启动程序...")
            sys.exit(0)  # 结束当前非提权进程
        else:
            raise RuntimeError(f"UAC提权失败，错误代码: {result}")

    except Exception as e:
        raise RuntimeError(f"Windows UAC提权失败: {e}")


def _require_admin_unix() -> None:
    """Unix/Linux/macOS系统下请求管理员权限"""
    print("请使用sudo运行此程序以获取管理员权限:")
    print(f"sudo {' '.join(sys.argv)}")
    sys.exit(1)


def run_as_admin(func):
    """
    装饰器：确保被装饰的函数以管理员权限运行

    Args:
        func: 需要管理员权限的函数

    Returns:
        装饰后的函数
    """

    def wrapper(*args, **kwargs):
        if not is_admin():
            require_admin(f"函数 '{func.__name__}' 需要管理员权限")
        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def check_admin_and_prompt(operation_name: str = "此操作") -> bool:
    """
    检查管理员权限并提示用户

    Args:
        operation_name: 操作名称，用于提示信息

    Returns:
        bool: 是否具有管理员权限
    """
    if is_admin():
        return True
    else:
        print(f"警告: {operation_name}需要管理员权限才能执行")
        if sys.platform.startswith('win'):
            print("请以管理员身份重新运行此程序")
        else:
            print("请使用sudo重新运行此程序")
        return False


def execute_command(
        _cmd: Union[str, List[str]],
        encoding: Optional[str] = None,
        errors: str = 'replace',
        timeout: Optional[float] = None
) -> Generator[str, None, None]:
    """
    执行命令并返回生成器，逐行输出结果

    Args:
        _cmd: 要执行的命令，可以是字符串或字符串列表
        encoding: 输出编码，默认为系统默认编码
        errors: 编码错误处理方式，默认为'replace'
        timeout: 超时时间（秒），None表示无超时限制

    Yields:
        str: 命令输出的每一行

    Raises:
        subprocess.TimeoutExpired: 命令执行超时
        subprocess.CalledProcessError: 命令执行失败
        FileNotFoundError: 命令不存在
    """
    # 设置默认编码
    if encoding is None:
        encoding = sys.getdefaultencoding()

    # 处理命令格式
    if isinstance(_cmd, str):
        # 如果是字符串，在Windows上需要shell=True
        shell = sys.platform.startswith('win')
        command = _cmd
    else:
        # 如果是列表，不需要shell
        shell = False
        command = _cmd

    process = None
    timer = None

    try:
        # 启动进程
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 将stderr重定向到stdout
            shell=shell,
            universal_newlines=False,  # 使用二进制模式
            bufsize=1  # 行缓冲
        )

        # 设置超时定时器
        if timeout is not None:
            def timeout_handler():
                if process and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)  # 等待5秒让进程优雅退出
                    except subprocess.TimeoutExpired:
                        process.kill()  # 强制杀死进程

            timer = threading.Timer(timeout, timeout_handler)
            timer.start()

        # 逐行读取输出
        while True:
            # 读取一行输出
            line = process.stdout.readline()

            if not line:
                # 没有更多输出，检查进程是否结束
                if process.poll() is not None:
                    break
                continue

            # 解码并返回
            try:
                decoded_line = line.decode(encoding, errors=errors).rstrip('\r\n')
                if decoded_line:  # 只返回非空行
                    yield decoded_line
            except UnicodeDecodeError as e:
                # 如果解码失败，返回错误信息
                yield f"[解码错误: {str(e)}]"

        # 等待进程结束
        return_code = process.wait()

        # 检查返回码
        if return_code != 0:
            error_msg = f"命令执行失败，返回码: {return_code}"
            yield f"[错误: {error_msg}]"

    except subprocess.TimeoutExpired:
        yield f"[错误: 命令执行超时 ({timeout}秒)]"
        raise

    except FileNotFoundError:
        yield "[错误: 命令不存在或无法找到]"
        raise

    except Exception as e:
        yield f"[错误: {str(e)}]"
        raise

    finally:
        # 清理资源
        if timer:
            timer.cancel()

        if process:
            # 确保进程被正确关闭
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()


# 使用示例
if __name__ == "__main__":
    # 示例1: 执行简单命令
    print("=== 示例1: 执行 'echo Hello World' ===")
    try:
        for output in execute_command("echo Hello World"):
            print(f"输出: {output}")
    except Exception as e:
        print(f"执行失败: {e}")

    print("\n=== 示例2: 执行 'dir' 或 'ls' 命令 ===")
    try:
        # 根据系统选择命令
        cmd = "dir" if sys.platform.startswith('win') else "ls -la"
        for output in execute_command(cmd):
            print(f"输出: {output}")
    except Exception as e:
        print(f"执行失败: {e}")

    print("\n=== 示例3: 使用列表形式的命令 ===")
    try:
        if sys.platform.startswith('win'):
            cmd_list = ["cmd", "/c", "echo", "Hello from list"]
        else:
            cmd_list = ["echo", "Hello from list"]

        for output in execute_command(cmd_list):
            print(f"输出: {output}")
    except Exception as e:
        print(f"执行失败: {e}")

    print("\n=== 示例4: 带超时的命令 ===")
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
    except Exception as e:
        print(f"执行失败: {e}")

    print("\n=== 示例5: 处理不存在的命令 ===")
    try:
        for output in execute_command("nonexistent_command_12345"):
            print(f"输出: {output}")
    except FileNotFoundError:
        print("命令不存在")
    except Exception as e:
        print(f"执行失败: {e}")
