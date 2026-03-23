import ctypes
import io
import locale
import os
import subprocess
import sys
import threading
from typing import Union, List, Generator, Optional


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
    except Exception:
        # 其他异常情况，默认返回False
        return False


# Windows 内部命令白名单
if sys.platform.startswith('win'):
    WINDOWS_INTERNAL_CMDS = {
        'echo', 'dir', 'cd', 'type', 'copy', 'del', 'erase', 'ren', 'rename',
        'md', 'mkdir', 'rd', 'rmdir', 'cls', 'color', 'date', 'time', 'ver',
        'vol', 'path', 'prompt', 'set', 'title', 'pushd', 'popd', 'shift',
        'exit', 'pause', 'start', 'assoc', 'ftype', 'tree', 'where', 'for', 'if', 'rem'
    }


class _StderrCollector:
    """后台收集 stderr 输出"""

    def __init__(self, stderr_pipe, encoding, errors):
        self.stderr_pipe = stderr_pipe
        self.encoding = encoding
        self.errors = errors
        self.lines = []
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._collect, daemon=True)
        self._thread.start()

    def _collect(self):
        try:
            reader = io.TextIOWrapper(
                self.stderr_pipe,
                encoding=self.encoding,
                errors=self.errors,
                newline=''
            )
            for line in reader:
                if self._stop_event.is_set():
                    break
                self.lines.append(line.rstrip('\r\n'))
        except (ValueError, OSError):
            # 管道可能已关闭
            pass

    def stop(self):
        self._stop_event.set()
        # 关闭管道以释放线程
        if self.stderr_pipe:
            try:
                self.stderr_pipe.close()
            except:
                pass
        if self._thread.is_alive():
            self._thread.join(timeout=1)

    def get_stderr(self):
        return '\n'.join(self.lines)


def run_cmd(
        _cmd: Union[str, List[str]],
        encoding: Optional[str] = None,
        errors: str = 'replace',
        timeout: Optional[float] = None,
        merge_stderr: bool = True,
        check: bool = True
) -> Generator[str, None, None]:
    """
    执行命令并返回生成器，逐行输出结果（不包括换行符）。

    Args:
        _cmd: 要执行的命令，可以是字符串或字符串列表。
        encoding: 输出编码，默认为系统区域设置编码（locale.getpreferredencoding）。
        errors: 编码错误处理方式，默认为'replace'。
        timeout: 超时时间（秒），None表示无超时限制。超时后已输出的行仍会 yield，
                 然后抛出 TimeoutError。
        merge_stderr: 是否将 stderr 合并到 stdout 输出流。
                      - True: stderr 与 stdout 混合输出（默认）。
                      - False: stderr 被完全忽略（重定向到 os.devnull），
                                但会在命令失败时附加到异常消息中。
        check: 是否检查返回码，默认为 True。若为 True，当命令返回非零退出码时抛出 Exception。

    Yields:
        str: 命令输出的每一行（已去除末尾换行符）。

    Raises:
        TimeoutError: 命令执行超时（超时前已输出的行仍会被 yield），异常消息包含 stderr（若收集到）。
        Exception: 命令执行失败（返回码非0）且 check=True，异常消息包含返回码、命令和 stderr（若收集到）。
    """
    if encoding is None:
        encoding = locale.getpreferredencoding(False) or sys.getdefaultencoding()

    # 处理 Windows 内部命令的列表形式
    if isinstance(_cmd, list) and sys.platform.startswith('win'):
        if _cmd[0].lower() in WINDOWS_INTERNAL_CMDS:
            _cmd = ['cmd', '/c'] + _cmd

    if isinstance(_cmd, str):
        use_shell = sys.platform.startswith('win')
        cmd_args = _cmd
    else:
        use_shell = False
        cmd_args = _cmd

    # 配置标准错误处理
    if merge_stderr:
        stderr_target = subprocess.STDOUT
        stderr_collector = None
    else:
        stderr_target = subprocess.PIPE
        stderr_collector = None  # 稍后创建

    # 启动进程
    process: subprocess.Popen = subprocess.Popen(
        cmd_args,
        stdout=subprocess.PIPE,
        stderr=stderr_target,
        shell=use_shell,
        universal_newlines=False,
        bufsize=-1,
    )

    # 如果需要单独收集 stderr，创建收集器
    if not merge_stderr:
        stderr_collector = _StderrCollector(process.stderr, encoding, errors)

    timeout_event = threading.Event()
    timer = None

    def timeout_handler():
        timeout_event.set()
        process.terminate()

    if timeout is not None:
        timer = threading.Timer(timeout, timeout_handler)
        timer.daemon = True
        timer.start()

    try:
        text_stream = io.TextIOWrapper(
            process.stdout,
            encoding=encoding,
            errors=errors,
            newline=''
        )

        for line in text_stream:
            yield line.rstrip('\r\n')

        return_code = process.wait()

        if timeout_event.is_set():
            # 超时后确保进程退出
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            cmd_str = cmd_args if isinstance(cmd_args, str) else ' '.join(cmd_args)
            stderr_msg = ''
            if stderr_collector:
                stderr_msg = f"\nstderr:\n{stderr_collector.get_stderr()}"
            raise TimeoutError(f"命令执行超时 ({timeout}秒): [{cmd_str}]\n{stderr_msg}\n")

        if check and return_code != 0:
            cmd_str = cmd_args if isinstance(cmd_args, str) else ' '.join(cmd_args)
            stderr_msg = ''
            if stderr_collector:
                stderr_msg = f"\nstderr:\n{stderr_collector.get_stderr()}"
            raise Exception(f"命令执行失败，返回码 {return_code}: [{cmd_str}]\n{stderr_msg}\n")

    except (GeneratorExit, KeyboardInterrupt):
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        raise
    finally:
        if timer is not None:
            timer.cancel()
        if stderr_collector:
            stderr_collector.stop()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
