"""
SSH 客户端模块

提供增强的 SSH 连接功能，包括：
- 密码和私钥认证
- SFTP 文件传输（支持进度条和断点续传）
- 交互式 Shell
- 命令执行（支持工作目录切换）
- 连接保活机制

使用示例:
    from hzgt.tools import SSHClient
    
    # 基本用法
    with SSHClient("192.168.1.100", username="user", password="pass") as ssh:
        ssh.execute_command("ls -la")
        ssh.upload_file("local.txt", "/remote/path")
"""

import logging
import os
import platform
import posixpath
import sys
from contextlib import contextmanager
from typing import Optional, Callable, Union, List

import paramiko
import select
from tqdm import tqdm

from ..core.log import set_log


class SSHClient:
    """
    增强的 SSH 客户端封装类
    
    基于 paramiko 库提供更友好的 SSH 操作接口，主要特性：
    
    1. 多种认证方式：
       - 密码认证
       - 私钥文件认证
       - SSH Agent 自动查找密钥
    
    2. 安全特性：
       - 主机密钥验证策略（严格/自动/警告）
       - 可选的主机密钥指纹校验
    
    3. 文件传输：
       - SFTP 上传/下载
       - 分块传输（默认 32KB）
       - 自动显示进度条（tqdm）
       - 传输后文件大小校验
       - 自动创建远程目录
    
    4. 命令执行：
       - 支持指定工作目录
       - 实时流式输出
       - 伪终端支持（用于 sudo 等交互命令）
    
    5. 交互式 Shell：
       - Unix: 原始模式，实时按键响应
       - Windows: 行缓冲模式，回车发送
    
    6. 连接管理：
       - 上下文管理器支持（with 语句）
       - 自动连接保活（keepalive）
       - 临时目录切换（cd 上下文管理器）
    
    7. 日志记录：
       - 集成 hzgt 日志系统
       - 所有操作都有详细日志
    
    典型用法:
        # 密码认证
        ssh = SSHClient("host", username="user", password="pass")
        ssh.connect()
        ssh.execute_command("ls")
        ssh.close()
        
        # 推荐：使用 with 语句
        with SSHClient("host", username="user", key_filename="~/.ssh/id_rsa") as ssh:
            ssh.upload_file("local.txt", "/remote/")
            ssh.download_file("/remote/file.txt", "./")
    """

    def __init__(
            self,
            hostname: str,
            port: int = 22,
            username: Optional[str] = None,
            password: Optional[str] = None,
            key_filename: Optional[Union[str, List[str]]] = None,
            passphrase: Optional[str] = None,
            look_for_keys: bool = True,
            allow_agent: bool = True,
            hostkey_policy: str = 'warning',
            expected_hostkey: Optional[str] = None,
            timeout: int = 10,
            keepalive_interval: int = 0,
            logger: Optional[logging.Logger] = None
    ):
        """
        初始化 SSH 客户端配置
        
        :param hostname: SSH 服务器地址（IP 或域名）
        :param port: SSH 端口号，默认 22
        :param username: 登录用户名
        :param password: 登录密码（与 key_filename 二选一）
        :param key_filename: 私钥文件路径，可以是单个文件或文件列表
                            例如: "~/.ssh/id_rsa" 或 ["~/.ssh/id_rsa", "~/.ssh/id_ed25519"]
        :param passphrase: 私钥文件的密码短语（如果私钥有加密）
        :param look_for_keys: 是否自动在 ~/.ssh/ 目录下查找私钥文件，默认 True
        :param allow_agent: 是否允许使用 SSH agent 进行认证，默认 True
        :param hostkey_policy: 主机密钥验证策略：
                              - 'strict': 拒绝未知主机（最安全）
                              - 'auto': 自动接受并保存新主机密钥
                              - 'warning': 接受但显示警告（默认）
        :param expected_hostkey: 期望的主机密钥指纹（十六进制字符串），
                                如果不匹配则拒绝连接，提供额外的安全保障
        :param timeout: 连接超时时间（秒），默认 10
        :param keepalive_interval: TCP keepalive 间隔（秒），0 表示禁用。
                                  建议设置为 30-60 以防止防火墙断开空闲连接
        :param logger: 自定义日志器，如果为 None 则使用默认的 hzgt.ssh 日志器
        """
        # 保存连接参数
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.passphrase = passphrase
        self.look_for_keys = look_for_keys
        self.allow_agent = allow_agent
        self.hostkey_policy = hostkey_policy
        self.expected_hostkey = expected_hostkey
        self.timeout = timeout
        self.keepalive_interval = keepalive_interval
        
        # SSH 客户端实例（connect() 后创建）
        self.client: Optional[paramiko.SSHClient] = None
        
        # 用户家目录缓存（用于 ~ 路径扩展）
        self._home: Optional[str] = None

        # 初始化日志器
        self.logger = logger or set_log("hzgt.ssh", "logs", "ssh.log")

    def _setup_hostkey_policy(self) -> None:
        """
        根据配置设置主机密钥验证策略
        
        主机密钥验证是 SSH 安全的重要组成部分，用于防止中间人攻击。
        三种策略的安全性从高到低：
        - strict: 只接受已知主机，首次连接会失败（需要手动添加到 known_hosts）
        - warning: 接受新主机但显示警告（推荐用于开发环境）
        - auto: 自动接受并保存所有新主机（方便但不安全）
        
        :raises ValueError: 如果提供了无效的 hostkey_policy 值
        """
        if self.hostkey_policy == 'strict':
            # 严格模式：拒绝未知主机密钥
            policy = paramiko.RejectPolicy()
        elif self.hostkey_policy == 'auto':
            # 自动模式：自动接受并保存新主机密钥
            policy = paramiko.AutoAddPolicy()
        elif self.hostkey_policy == 'warning':
            # 警告模式：接受新主机但显示警告信息
            policy = paramiko.WarningPolicy()
        else:
            raise ValueError(f"未知的 hostkey_policy: {self.hostkey_policy}")
        
        # 应用策略到 SSH 客户端
        self.client.set_missing_host_key_policy(policy)

    def _verify_hostkey(self, hostname: str, key: paramiko.PKey) -> None:
        """
        验证远程主机密钥指纹是否与期望值匹配
        
        这是一种额外的安全检查，可以确保连接到的是预期的服务器，
        即使使用了 auto 或 warning 策略也能提供保护。
        
        :param hostname: 主机名（用于日志记录）
        :param key: 远程服务器的公钥对象
        :raises paramiko.SSHException: 如果指纹不匹配则抛出异常
        """
        if self.expected_hostkey:
            # 获取实际的主机密钥指纹（十六进制格式）
            fingerprint = key.get_fingerprint().hex()
            
            # 检查期望的指纹是否在实际指纹中
            # 使用 in 而不是 == 是因为用户可能只提供部分指纹
            if self.expected_hostkey not in fingerprint:
                raise paramiko.SSHException(
                    f"主机密钥指纹不匹配！期望: {self.expected_hostkey}, 实际: {fingerprint}"
                )

    def _expand_remote_path(self, path: str) -> str:
        """
        扩展远程路径中的波浪号 (~) 为用户家目录
        
        将类似 ~/Documents 的路径转换为绝对路径 /home/user/Documents。
        仅在路径以 ~/ 开头且已获取到家目录时进行转换。
        
        :param path: 远程路径（可能包含 ~）
        :return: 扩展后的绝对路径
        """
        if path.startswith('~/') and self._home:
            # 只替换第一个 ~，避免替换路径中其他位置的 ~
            return path.replace('~', self._home, 1)
        return path

    def connect(self) -> bool:
        """
        建立 SSH 连接到远程服务器
        
        该方法会：
        1. 创建 paramiko.SSHClient 实例
        2. 设置主机密钥验证策略
        3. 根据配置选择认证方式（密码或私钥）
        4. 验证主机密钥指纹（如果提供了 expected_hostkey）
        5. 设置连接保活（如果启用了 keepalive）
        6. 获取用户家目录（用于 ~ 路径扩展）
        
        :return: True 表示连接成功，False 表示连接失败
        :raises paramiko.AuthenticationException: 认证失败（用户名/密码错误）
        :raises paramiko.SSHException: SSH 协议错误
        :raises Exception: 其他连接错误
        
        使用示例:
            ssh = SSHClient("192.168.1.100", username="user", password="pass")
            if ssh.connect():
                print("连接成功")
            else:
                print("连接失败")
        """
        try:
            # 创建 SSH 客户端实例
            self.client = paramiko.SSHClient()
            
            # 配置主机密钥验证策略
            self._setup_hostkey_policy()

            # 构建连接参数字典
            connect_kwargs = {
                'hostname': self.hostname,
                'port': self.port,
                'username': self.username,
                'timeout': self.timeout,
                'look_for_keys': self.look_for_keys,  # 自动查找 ~/.ssh/ 下的密钥
                'allow_agent': self.allow_agent,       # 允许使用 ssh-agent
            }
            
            # 添加可选的认证参数
            if self.password:
                connect_kwargs['password'] = self.password
            if self.key_filename:
                connect_kwargs['key_filename'] = self.key_filename
            if self.passphrase:
                connect_kwargs['passphrase'] = self.passphrase

            # 执行连接
            self.client.connect(**connect_kwargs)

            # 如果指定了期望的主机密钥指纹，进行验证
            if self.expected_hostkey:
                transport = self.client.get_transport()
                remote_key = transport.get_remote_server_key()
                self._verify_hostkey(self.hostname, remote_key)

            # 启用 TCP keepalive 防止防火墙断开空闲连接
            if self.keepalive_interval > 0:
                transport = self.client.get_transport()
                if transport:
                    transport.set_keepalive(self.keepalive_interval)

            # 获取用户家目录，用于后续的路径扩展（~ -> /home/user）
            try:
                stdin, stdout, stderr = self.client.exec_command('echo ~')
                self._home = stdout.read().decode('utf-8').strip()
                self.logger.debug(f"获取用户家目录: {self._home}")
            except Exception as e:
                # 如果获取失败，设置为 None，~ 路径将无法扩展
                self.logger.warning(f"获取用户家目录失败: {e}")
                self._home = None

            self.logger.info(f"成功连接到 {self.hostname}:{self.port}")
            return True

        except paramiko.AuthenticationException as e:
            # 认证失败：用户名、密码或密钥不正确
            self.logger.error(f"认证失败: {e}")
        except paramiko.SSHException as e:
            # SSH 协议层面的错误
            self.logger.error(f"SSH 连接异常: {e}")
        except Exception as e:
            # 其他未预期的错误（网络问题、超时等）
            self.logger.error(f"连接失败: {e}")
        return False

    def execute_command(self, command: str, timeout: Optional[int] = None,
                        cwd: Optional[str] = None, stream: bool = False,
                        pty: bool = False) -> tuple:
        """
        在远程服务器上执行命令
        
        支持两种模式：
        1. 普通模式（stream=False）：等待命令执行完成，返回所有输出
        2. 流式模式（stream=True）：实时打印输出，适合长时间运行的命令
        
        :param command: 要执行的 shell 命令字符串
                       例如: "ls -la", "ps aux | grep python"
        :param timeout: 命令执行超时时间（秒），None 表示不超时
        :param cwd: 工作目录，命令将在此目录下执行。
                   支持 ~ 路径扩展，例如: "~/Documents"
        :param stream: 是否实时流式输出：
                      - False: 等待命令完成，返回完整输出（默认）
                      - True: 逐行实时打印到终端，不等待命令结束
        :param pty: 是否分配伪终端（pseudo-terminal）：
                   - False: 非交互式模式（默认）
                   - True: 交互式模式，解决某些命令需要终端环境的问题
                          例如: sudo, apt-get install, top 等
        :return: (stdout, stderr, exit_code) 元组
                - stdout: 标准输出内容（字符串）
                - stderr: 错误输出内容（字符串）
                - exit_code: 命令退出码，0 表示成功，非 0 表示失败
                注意：如果 stream=True，返回 ('', '', exit_code)
        
        使用示例:
            # 基本用法
            stdout, stderr, code = ssh.execute_command("uname -a")
            print(stdout)
            
            # 指定工作目录
            stdout, _, _ = ssh.execute_command("pwd", cwd="~/Documents")
            
            # 实时输出（适合 tail, ping 等长时间命令）
            ssh.execute_command("tail -f /var/log/syslog", stream=True)
            
            # 使用伪终端（解决 sudo 密码输入问题）
            ssh.execute_command("sudo apt update", pty=True)
        """
        if not self.client:
            raise Exception("未建立连接，请先调用 connect()")

        # 如果指定了工作目录，使用 cd && command 的方式切换目录后执行
        full_command = command
        if cwd:
            # 扩展 ~ 路径
            cwd_expanded = self._expand_remote_path(cwd)
            full_command = f'cd {cwd_expanded} && {command}'

        self.logger.debug(f"执行命令: {full_command}")
        try:
            # 执行命令，get_pty=True 会分配伪终端
            stdin, stdout, stderr = self.client.exec_command(
                full_command, 
                timeout=timeout, 
                get_pty=pty
            )

            if stream:
                # 流式模式：实时读取并打印输出
                # 同时监听 stdout 和 stderr 两个通道
                channels = [stdout.channel, stderr.channel]
                while not stdout.channel.closed or not stderr.channel.closed:
                    # 使用 select 实现非阻塞 IO，超时 0.1 秒
                    rlist, _, _ = select.select(channels, [], [], 0.1)
                    for chan in rlist:
                        # 读取标准输出
                        if chan.recv_ready():
                            data = chan.recv(4096).decode('utf-8', errors='replace')
                            print(data, end='', flush=True)
                        # 读取错误输出
                        if chan.recv_stderr_ready():
                            data = chan.recv_stderr(4096).decode('utf-8', errors='replace')
                            print(data, end='', flush=True, file=sys.stderr)
                
                # 获取命令退出码
                exit_code = stdout.channel.recv_exit_status()
                # 流式模式下已实时输出，不再返回累积内容
                return '', '', exit_code
            else:
                # 普通模式：等待命令完成，读取所有输出
                exit_code = stdout.channel.recv_exit_status()
                stdout_output = stdout.read().decode('utf-8')
                stderr_output = stderr.read().decode('utf-8')
                
                # 根据退出码记录日志
                if exit_code != 0:
                    self.logger.debug(f"命令执行失败，退出码 {exit_code}: {stderr_output}")
                else:
                    self.logger.debug(f"命令执行成功，退出码 0")
                
                return stdout_output, stderr_output, exit_code
        except Exception as e:
            self.logger.error(f"执行命令失败: {e}")
            return None, None, -1

    def invoke_shell(self, term: str = 'vt100', width: int = 80, height: int = 24) -> None:
        """
        启动交互式 Shell 会话
        
        允许用户直接在终端中与远程服务器交互，就像使用 ssh 命令一样。
        支持输入任何命令，包括需要交互的命令（如 sudo 密码输入）。
        
        平台差异：
        - Unix/Linux/macOS: 使用原始模式（raw mode），实现实时按键响应
        - Windows: 使用行缓冲模式，按回车后发送整行命令
        
        :param term: 终端类型，默认 'vt100'
                    常见值: 'vt100', 'xterm', 'ansi'
        :param width: 终端宽度（字符数），默认 80
        :param height: 终端高度（行数），默认 24
        
        注意:
        - 此方法是阻塞的，会一直运行直到用户退出 Shell
        - 在 Windows 上不支持某些特殊键（如方向键）
        - 退出 Shell 后会自动关闭通道
        
        使用示例:
            ssh.invoke_shell()
            # 现在可以像普通 SSH 会话一样操作
            # 输入 exit 或按 Ctrl+D 退出
        """
        if not self.client:
            raise Exception("未建立连接，请先调用 connect()")

        channel = self.client.invoke_shell(term=term, width=width, height=height)
        channel.settimeout(0.1)
        self.logger.info("进入交互式 Shell，输入 exit 或 Ctrl+D 退出。")

        is_windows = platform.system() == 'Windows'

        try:
            if not is_windows:
                # Unix 系统：使用原始模式，实时按键
                import tty
                import termios
                old_settings = termios.tcgetattr(sys.stdin)
                try:
                    tty.setraw(sys.stdin.fileno())
                    while True:
                        if channel.recv_ready():
                            data = channel.recv(4096)
                            sys.stdout.write(data.decode('utf-8', errors='replace'))
                            sys.stdout.flush()
                        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                            key = sys.stdin.read(1)
                            if not key:
                                break
                            channel.send(key)
                finally:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            else:
                # Windows 系统：使用行缓冲模式，按回车发送
                import threading

                def read_stdin():
                    while True:
                        line = sys.stdin.readline()
                        if not line:
                            break
                        channel.send(line)

                stdin_thread = threading.Thread(target=read_stdin, daemon=True)
                stdin_thread.start()

                while not channel.closed:
                    try:
                        if channel.recv_ready():
                            data = channel.recv(4096)
                            sys.stdout.write(data.decode('utf-8', errors='replace'))
                            sys.stdout.flush()
                    except Exception:
                        break
        except Exception as e:
            self.logger.error(f"交互式 Shell 异常: {e}")
        finally:
            channel.close()
            self.logger.info("交互式 Shell 已退出")

    def open_sftp(self) -> paramiko.SFTPClient:
        """
        打开 SFTP 会话用于文件传输
        
        SFTP (SSH File Transfer Protocol) 是基于 SSH 的安全文件传输协议。
        返回的 SFTPClient 对象可以用于上传、下载、列出目录等操作。
        
        :return: paramiko.SFTPClient 实例
        :raises Exception: 如果未建立 SSH 连接
        
        注意:
        - 使用完毕后应该关闭 SFTP 会话（建议使用 with 语句）
        - 每个 SFTP 会话都是独立的，可以并发使用多个会话
        
        使用示例:
            with ssh.open_sftp() as sftp:
                sftp.put('local.txt', '/remote.txt')
                sftp.get('/remote.txt', 'local.txt')
        """
        if not self.client:
            raise Exception("未建立连接，请先调用 connect()")
        self.logger.debug("打开 SFTP 会话")
        return self.client.open_sftp()

    # -------------------- 目录操作辅助 --------------------
    def _mkdir_p(self, sftp: paramiko.SFTPClient, remote_dir: str) -> None:
        """
        递归创建远程目录（类似 Unix 的 mkdir -p 命令）
        
        如果目录已存在则不执行任何操作。
        如果父目录不存在，会先递归创建父目录。
        
        :param sftp: SFTP 客户端实例
        :param remote_dir: 要创建的远程目录路径
        :raises PermissionError: 如果权限不足无法创建目录
        
        使用示例:
            with ssh.open_sftp() as sftp:
                ssh._mkdir_p(sftp, '/home/user/a/b/c')
                # 会依次创建 /home/user/a, /home/user/a/b, /home/user/a/b/c
        """
        # 根目录或空路径无需创建
        if remote_dir in ('', '/'):
            return
        try:
            # 检查目录是否已存在
            sftp.stat(remote_dir)
        except FileNotFoundError:
            # 目录不存在，先创建父目录
            parent = posixpath.dirname(remote_dir)
            self._mkdir_p(sftp, parent)
            try:
                # 创建当前目录
                sftp.mkdir(remote_dir)
                self.logger.debug(f"创建远程目录: {remote_dir}")
            except PermissionError as e:
                self.logger.error(f"无法创建远程目录 {remote_dir}: 权限不足")
                raise PermissionError(f"无法创建远程目录 {remote_dir}: 权限不足") from e
        except PermissionError:
            # 目录存在但无访问权限
            self.logger.error(f"无法访问远程目录 {remote_dir}: 权限不足")
            raise PermissionError(f"无法访问远程目录 {remote_dir}: 权限不足")

    @contextmanager
    def cd(self, path: str):
        """
        上下文管理器，用于临时切换远程工作目录。
        返回的代理对象会自动将相对路径解析为相对于 path 的路径。
        用法：
            with client.cd('~/桌面/sshtest') as cd:
                cd.execute_command('ls -l')           # 在 ~/桌面/sshtest 下执行
                cd.upload_file('local.txt', '.')      # 上传到 ~/桌面/sshtest
                cd.download_file('remote.txt', '.')   # 从 ~/桌面/sshtest 下载
        """

        class CWDProxy:
            def __init__(self, client, base_path):
                self.client = client
                self.base_path = base_path

            def _resolve_path(self, remote_path: str) -> str:
                """如果 remote_path 是相对路径，则拼接 base_path"""
                # 绝对路径（以 '/' 或 '~' 开头）直接返回
                if remote_path.startswith('/') or remote_path.startswith('~'):
                    return remote_path
                # 相对路径则与 base_path 拼接
                return posixpath.join(self.base_path, remote_path)

            def execute_command(self, command, **kwargs):
                return self.client.execute_command(command, cwd=self.base_path, **kwargs)

            def upload_file(self, local_file, remote_dir, remote_name=None, **kwargs):
                resolved_remote_dir = self._resolve_path(remote_dir)
                return self.client.upload_file(local_file, resolved_remote_dir, remote_name, **kwargs)

            def download_file(self, remote_file, local_dir, local_name=None, **kwargs):
                resolved_remote_file = self._resolve_path(remote_file)
                return self.client.download_file(resolved_remote_file, local_dir, local_name, **kwargs)

        yield CWDProxy(self, path)

    # -------------------- SFTP 大文件传输（分块 + 进度回调） --------------------
    def upload_file(
            self,
            local_file: str,
            remote_dir: str = ".",
            remote_name: Optional[str] = None,
            callback: Optional[Callable[[int, int], None]] = None,
            block_size: int = 32768,
            confirm: bool = True
    ) -> bool:
        """
        上传本地文件到远程服务器
        
        使用 SFTP 协议进行安全的文件传输，支持：
        - 分块传输（默认 32KB/块），适合大文件
        - 自动显示进度条（tqdm）或自定义进度回调
        - 传输后文件大小校验，确保完整性
        - 自动创建远程目录（包括父目录）
        - 支持 ~ 路径扩展
        
        :param local_file: 本地文件路径（必须存在）
        :param remote_dir: 远程目标目录，默认当前目录 "."
                          支持 ~ 路径扩展，例如: "~/uploads"
                          如果目录不存在会自动创建
        :param remote_name: 远程文件名，默认为本地文件名
                           可以指定不同的文件名
        :param callback: 进度回调函数，签名为 callback(sent_bytes, total_bytes)
                        如果不提供，则自动使用 tqdm 进度条
        :param block_size: 每次读取/写入的块大小（字节），默认 32KB (32768)
                          较大的值可以提高传输速度，但占用更多内存
        :param confirm: 是否在传输完成后校验文件大小，默认 True
                       如果远程文件大小与本地不一致会抛出异常
        :return: 成功返回 True，失败抛出异常
        :raises FileNotFoundError: 本地文件不存在
        :raises Exception: 传输失败或文件校验不通过
        
        使用示例:
            # 基本上传（自动显示进度条）
            ssh.upload_file("local.zip", "/remote/path")
            
            # 自定义远程文件名
            ssh.upload_file("data.csv", "/backup", remote_name="backup_2024.csv")
            
            # 自定义进度回调
            def progress(sent, total):
                pct = sent / total * 100
                print(f"进度: {pct:.1f}%")
            ssh.upload_file("large.iso", "/tmp", callback=progress)
            
            # 禁用文件校验（提高速度但不安全）
            ssh.upload_file("file.txt", "/tmp", confirm=False)
        """
        if not os.path.isfile(local_file):
            raise FileNotFoundError(f"本地文件不存在: {local_file}")

        # 确定远程文件名和路径
        remote_name = remote_name or os.path.basename(local_file)
        remote_dir = self._expand_remote_path(remote_dir)  # 扩展 ~ 路径
        remote_path = posixpath.join(remote_dir, remote_name)

        # 获取本地文件大小，用于进度显示和校验
        total_size = os.path.getsize(local_file)
        uploaded = 0  # 已上传字节数计数器

        # 如果没有提供回调函数，使用 tqdm 进度条
        pbar = None
        if callback is None:
            desc = f'上传 {remote_name}'
            pbar = tqdm(total=total_size, unit='B', unit_divisor=1024, unit_scale=True, desc=desc)

        self.logger.info(f"开始上传文件: {local_file} -> {remote_path} ({total_size} 字节)")
        try:
            # 打开 SFTP 会话
            with self.open_sftp() as sftp:
                # 递归创建远程目录（如果不存在）
                self._mkdir_p(sftp, remote_dir)

                # 以二进制读模式打开本地文件
                with open(local_file, 'rb') as local_f:
                    # 以二进制写模式打开远程文件
                    with sftp.open(remote_path, 'wb') as remote_f:
                        # 分块读取和写入，避免一次性加载大文件到内存
                        while True:
                            data = local_f.read(block_size)
                            if not data:
                                break  # 文件读取完毕
                            
                            # 写入远程文件
                            remote_f.write(data)
                            uploaded += len(data)
                            
                            # 更新进度条或调用回调函数
                            if pbar:
                                pbar.update(len(data))
                            if callback:
                                callback(uploaded, total_size)

            # 传输完成后校验文件大小
            if confirm:
                with self.open_sftp() as sftp:
                    remote_size = sftp.stat(remote_path).st_size
                    if remote_size != total_size:
                        raise Exception(f"上传不完整: 本地 {total_size} 字节，远程 {remote_size} 字节")
            
            self.logger.info(f"上传文件完成: {remote_path}")
            return True
        except Exception as e:
            self.logger.error(f"上传文件失败: {e}")
            raise
        finally:
            # 确保进度条被关闭
            if pbar:
                pbar.close()

    def download_file(
            self,
            remote_file: str,
            local_dir: str = "ssh_dwnl",
            local_name: Optional[str] = None,
            callback: Optional[Callable[[int, int], None]] = None,
            block_size: int = 32768,
            confirm: bool = True
    ) -> bool:
        """
        从远程服务器下载文件到本地
        
        使用 SFTP 协议进行安全的文件传输，功能与 upload_file 对称：
        - 分块传输（默认 32KB/块）
        - 自动显示进度条或自定义回调
        - 传输后文件大小校验
        - 自动创建本地目录
        - 支持 ~ 路径扩展
        
        :param remote_file: 远程文件路径
                           支持 ~ 路径扩展，例如: "~/documents/file.txt"
        :param local_dir: 本地保存目录，默认 "ssh_dwnl"
                         如果目录不存在会自动创建
        :param local_name: 本地文件名，默认为远程文件名
                          可以指定不同的文件名
        :param callback: 进度回调函数，签名为 callback(downloaded_bytes, total_bytes)
                        如果不提供，则自动使用 tqdm 进度条
        :param block_size: 每次读取/写入的块大小（字节），默认 32KB (32768)
        :param confirm: 是否在传输完成后校验文件大小，默认 True
        :return: 成功返回 True，失败抛出异常
        :raises Exception: 传输失败或文件校验不通过
        
        使用示例:
            # 基本下载（自动显示进度条）
            ssh.download_file("/remote/file.zip", "./downloads")
            
            # 自定义本地文件名
            ssh.download_file("/backup/data.csv", "./data", local_name="backup.csv")
            
            # 自定义进度回调
            def progress(sent, total):
                pct = sent / total * 100
                print(f"进度: {pct:.1f}%")
            ssh.download_file("/large.iso", "./", callback=progress)
        """
        local_name = local_name or os.path.basename(remote_file)
        local_path = os.path.join(local_dir, local_name)

        # 确保本地目录存在（exist_ok=True 表示如果已存在不报错）
        os.makedirs(local_dir, exist_ok=True)

        # 扩展远程路径中的 ~
        remote_file = self._expand_remote_path(remote_file)

        self.logger.info(f"开始下载文件: {remote_file} -> {local_path}")
        try:
            # 打开 SFTP 会话
            with self.open_sftp() as sftp:
                # 获取远程文件大小，用于进度显示和校验
                total_size = sftp.stat(remote_file).st_size
                downloaded = 0  # 已下载字节数计数器

                # 如果没有提供回调函数，使用 tqdm 进度条
                pbar = None
                if callback is None:
                    desc = f'下载 {local_name}'
                    pbar = tqdm(total=total_size, unit='B', unit_divisor=1024, unit_scale=True, desc=desc)

                # 以二进制写模式打开本地文件
                with open(local_path, 'wb') as local_f:
                    # 以二进制读模式打开远程文件
                    with sftp.open(remote_file, 'rb') as remote_f:
                        # 分块读取和写入
                        while True:
                            data = remote_f.read(block_size)
                            if not data:
                                break  # 文件读取完毕
                            
                            # 写入本地文件
                            local_f.write(data)
                            downloaded += len(data)
                            
                            # 更新进度条或调用回调函数
                            if pbar:
                                pbar.update(len(data))
                            if callback:
                                callback(downloaded, total_size)

                # 关闭进度条
                if pbar:
                    pbar.close()

            # 传输完成后校验文件大小
            if confirm:
                local_size = os.path.getsize(local_path)
                if local_size != total_size:
                    raise Exception(f"下载不完整: 本地 {local_size} 字节，远程 {total_size} 字节")
            
            self.logger.info(f"下载文件完成: {local_path}")
            return True
        except Exception as e:
            self.logger.error(f"下载文件失败: {e}")
            raise

    # -------------------- 连接管理 --------------------
    def close(self) -> None:
        """
        关闭 SSH 连接，释放资源
        
        应该在不再需要 SSH 连接时调用此方法。
        如果使用 with 语句，会自动调用此方法。
        
        使用示例:
            ssh = SSHClient("host", username="user", password="pass")
            ssh.connect()
            # ... 执行操作 ...
            ssh.close()  # 手动关闭
            
            # 或者推荐的方式：
            with SSHClient("host", username="user", password="pass") as ssh:
                # ... 执行操作 ...
            # 退出 with 块时自动关闭
        """
        if self.client:
            self.client.close()
            self.client = None
            self.logger.info("SSH 连接已关闭")

    def __enter__(self):
        """
        上下文管理器入口：自动建立连接
        
        支持 with 语句，进入 with 块时自动调用 connect()
        
        :return: self (SSHClient 实例)
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口：自动关闭连接
        
        退出 with 块时自动调用 close()，无论是否发生异常
        
        :param exc_type: 异常类型（如果有）
        :param exc_val: 异常值（如果有）
        :param exc_tb: 异常回溯（如果有）
        """
        self.close()
