# -*- coding: utf-8 -*-

import ftplib
import json
import os
from typing import Optional, List, Dict, Callable

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.filesystems import AbstractedFS
from pyftpdlib.handlers import FTPHandler, ThrottledDTPHandler
from pyftpdlib.servers import FTPServer
from tqdm import trange

from ..core.fileop import truncate_fname
from ..core.log import set_log
from ..core.strop import restrop
from ..core.Decorator import vargs


# ==================== 服务器增强 ====================

class Ftpserver:
    """
    FTP 服务器类，基于 pyftpdlib，支持用户管理、限速、SSL、事件回调、配置持久化等功能。

    用法示例：
        fs = Ftpserver()
        fs.add_user("/path/to", "user", "123456", "elradfmw")
        fs.set_log()
        fs.start(host="0.0.0.0", port=21)
    """

    def __init__(self, logger=None):
        self.__authorizer = DummyAuthorizer()
        self.__handler = FTPHandler
        self.__server = None

        self.__logger = logger or set_log('pyftpdlib', fpath="logs", fname="ftps.log", level=2, encoding="utf-8")

    # ---------- 用户管理 ----------
    def add_user(self, homedir: str, username: str = "anonymous", password: str = "", perm: str = "",
                 msg_login: str = "Login successful.", msg_quit: str = "Goodbye.") -> None:
        """
        添加 FTP 用户。

        :param homedir: 用户家目录（必须存在，否则会尝试创建）
        :param username: 用户名，若为空字符串则添加匿名用户
        :param password: 用户密码
        :param perm: 权限组合字符串，如 "elradfmw" 表示所有权限。各字符含义：
            - "e" = 更改目录 (CWD)
            - "l" = 列出文件 (LIST, NLST, etc.)
            - "r" = 从服务器检索文件 (RETR)
            - "a" = 将数据附加到现有文件 (APPE)
            - "d" = 删除文件或目录 (DELE, RMD)
            - "f" = 重命名文件或目录 (RNFR, RNTO)
            - "m" = 创建目录 (MKD)
            - "w" = 将文件存储到服务器 (STOR, STOU)
            - "M" = 更改文件模式 (SITE CHMOD)
            - "T" = 更新文件上次修改时间 (MFMT)
        :param msg_login: 登录成功时的欢迎信息
        :param msg_quit: 退出时的告别信息
        :raises FileNotFoundError: 如果家目录不存在且创建失败
        """
        if not os.path.exists(homedir):
            try:
                os.makedirs(homedir)
            except Exception as e:
                raise FileNotFoundError(f"无法创建家目录 {homedir}: {e}") from None

        if username:  # 普通用户
            self.__authorizer.add_user(username, password, homedir, perm=perm, msg_login=msg_login, msg_quit=msg_quit)
        else:  # 匿名用户（使用 add_anonymous）
            self.__authorizer.add_anonymous(homedir, **{"msg_login": msg_login, "msg_quit": msg_quit})

    def enable_anonymous(self, homedir: str, perm: str = "elr", msg_login: str = "Anonymous login ok.",
                         msg_quit: str = "Goodbye.") -> None:
        """
        启用匿名用户访问。

        :param homedir: 匿名用户的家目录
        :param perm: 匿名用户权限（默认只读）
        :param msg_login: 登录消息
        :param msg_quit: 退出消息
        """
        self.add_user(homedir, username="", perm=perm, msg_login=msg_login, msg_quit=msg_quit)

    def remove_user(self, username: str) -> None:
        """
        删除指定用户。

        :param username: 要删除的用户名
        """
        self.__authorizer.remove_user(username)

    def correct_user(self, oldusername: str,
                     newdir: str = "", newusername: str = "", newpassword: str = "", newperm: str = ""):
        """
        修改用户信息（先删除原用户，再添加新用户）。

        :param oldusername: 原用户名
        :param newdir: 新家目录（留空表示不变）
        :param newusername: 新用户名（留空表示不变）
        :param newpassword: 新密码（留空表示不变）
        :param newperm: 新权限（留空表示不变）
        """
        if oldusername not in self.__authorizer.user_table:
            raise KeyError(f"用户 {oldusername} 不存在") from None

        old_info = self.__authorizer.user_table[oldusername]
        newdir = newdir if newdir else old_info["home"]
        newusername = newusername if newusername else oldusername
        newpassword = newpassword if newpassword else old_info.get("pwd", "")
        newperm = newperm if newperm else old_info.get("perm", "")

        self.remove_user(oldusername)
        self.add_user(newdir, newusername, newpassword, newperm,
                      msg_login=old_info.get("msg_login", "Login successful."),
                      msg_quit=old_info.get("msg_quit", "Goodbye."))

    def get_users(self) -> Dict:
        """
        获取当前所有用户信息。

        :return: 用户表字典
        """
        return self.__authorizer.user_table

    # ---------- 带宽限制 ----------
    def set_global_limits(self, read_limit: int = 300, write_limit: int = 300) -> None:
        """
        设置全局上传/下载速度限制（对所有用户生效）。

        :param read_limit: 上传限速（KB/s）
        :param write_limit: 下载限速（KB/s）
        """
        ThrottledDTPHandler.read_limit = read_limit * 1024
        ThrottledDTPHandler.write_limit = write_limit * 1024
        self.__handler.dtp_handler = ThrottledDTPHandler

    # ---------- 用户隔离 (chroot) ----------
    def enable_chroot(self, enable: bool = True) -> None:
        """
        启用或禁用用户家目录隔离（chroot）。启用后用户无法访问家目录之外的路径。

        :param enable: True 启用，False 禁用
        """
        if enable:
            self.__handler.abstracted_fs = AbstractedFS
        else:
            self.__handler.abstracted_fs = None  # 恢复默认

    # ---------- SSL/TLS 支持 ----------
    def enable_ssl(self, certfile: str, keyfile: str = None, ssl_version=None) -> None:
        """
        启用 FTPS 加密传输。

        :param certfile: SSL 证书文件路径
        :param keyfile: SSL 私钥文件路径（若证书文件包含私钥则可省略）
        :param ssl_version: SSL 版本，如 ssl.PROTOCOL_TLS_SERVER，默认使用 pyftpdlib 默认值
        """
        try:
            import ssl
        except ImportError:
            raise RuntimeError("SSL 模块不可用，无法启用加密") from None

        self.__handler.certfile = certfile
        if keyfile:
            self.__handler.keyfile = keyfile
        if ssl_version:
            self.__handler.ssl_version = ssl_version
        # 启用 TLS
        self.__handler.tls_control_required = True
        self.__handler.tls_data_required = True

    # ---------- 配置持久化 ----------
    def save_config(self, filepath: str) -> None:
        """
        将当前用户配置保存到 JSON 文件。

        :param filepath: 保存路径
        """
        config = {
            "users": []
        }
        for username, info in self.__authorizer.user_table.items():
            user_info = {
                "username": username,
                "homedir": info["home"],
                "perm": info.get("perm", ""),
                "msg_login": info.get("msg_login", ""),
                "msg_quit": info.get("msg_quit", "")
            }
            # 密码可能不存在（匿名用户）或需要保密，可选择性保存
            if "pwd" in info:
                user_info["password"] = info["pwd"]
            config["users"].append(user_info)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def load_config(self, filepath: str) -> None:
        """
        从 JSON 文件加载用户配置。

        :param filepath: 配置文件路径
        """
        with open(filepath, "r", encoding="utf-8") as f:
            config = json.load(f)

        for user in config["users"]:
            self.add_user(
                homedir=user["homedir"],
                username=user["username"],
                password=user.get("password", ""),
                perm=user.get("perm", ""),
                msg_login=user.get("msg_login", "Login successful."),
                msg_quit=user.get("msg_quit", "Goodbye.")
            )

    # ---------- 启动服务器 ----------
    def start(self, host: str = "127.0.0.1", port: int = 2121,
              passive_ports: range = range(6000, 7000),
              read_limit: int = 300, write_limit: int = 300,
              max_cons: int = 30, max_cons_per_ip: int = 10) -> None:
        """
        启动 FTP 服务器。

        :param host: 监听 IP 地址
        :param port: 监听端口
        :param passive_ports: 被动模式端口范围
        :param read_limit: 上传限速（KB/s）
        :param write_limit: 下载限速（KB/s）
        :param max_cons: 最大总连接数
        :param max_cons_per_ip: 每个 IP 的最大连接数
        """
        # 应用限速
        self.set_global_limits(read_limit, write_limit)

        # 设置被动端口范围
        self.__handler.passive_ports = list(passive_ports) if passive_ports else None

        # 绑定 authorizer
        self.__handler.authorizer = self.__authorizer

        # 创建服务器实例
        self.__server = FTPServer((host, port), self.__handler)

        # 设置连接限制
        self.__server.max_cons = max_cons
        self.__server.max_cons_per_ip = max_cons_per_ip

        self.__logger.info(f"FTP 服务器启动于 {restrop(host)}:{restrop(port, f=2)}")
        try:
            self.__server.serve_forever()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self) -> None:
        """关闭 FTP 服务器，释放资源。"""
        if self.__server:
            self.__server.close_all()
            self.__server.close()
            self.__logger.info("FTP 服务器已关闭。")


# ==================== 客户端 ====================
class Ftpclient:
    """
    FTP 客户端类，封装 ftplib，支持文件上传下载（带进度条）、目录递归操作、断点续传、主动/被动模式切换等。

    用法示例：
        with Ftpclient("127.0.0.1", 2121, "user", "pass") as client:
            client.upload("local.txt")
            client.download_dir("/remote/path", "local/path")
    """

    def __init__(self, host: str, port: int = 2121, username: str = "anonymous", password: str = "",
                 timeout: float = 30,
                 encoding: str = "utf-8",
                 passive: bool = True,
                 logger=None
                 ):
        """
        初始化 FTP 客户端并连接登录。

        :param host: FTP 服务器地址
        :param port: 端口号
        :param username: 用户名，默认为 anonymous
        :param password: 密码

        :param timeout: 连接超时时间（秒）
        :param encoding: 控制连接的编码
        :param passive: 是否使用被动模式

        :param logger: 日志器

        :raises FTPError: 连接或登录失败
        """
        self.host = host
        self.port = int(port)
        self.username = username if username else "anonymous"
        self.password = password
        self.encoding = encoding
        self.timeout = timeout
        self.passive = passive

        self.__logger = logger or set_log("ftpc", "logs", fname="ftpc.log", level=2, encoding="utf-8")

        self.__ftpc = ftplib.FTP()
        self.__ftpc.encoding = encoding
        try:
            self.__ftpc.connect(host, self.port, timeout=timeout)
            self.__ftpc.login(self.username, self.password)
            self.set_passive(passive)
        except Exception as e:
            raise Exception(f"连接/登录失败: {e}") from None

        self.__logger.info(f"用户 '{restrop(self.username, f=4)}' 已登录到 {restrop(host)}:{restrop(port)}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()

    # ---------- 基本操作 ----------
    def quit(self) -> None:
        """退出登录并关闭连接。"""
        try:
            self.__ftpc.quit()
        except:
            self.__ftpc.close()

    def pwd(self) -> str:
        """返回当前远程工作目录。"""
        return self.__ftpc.pwd()

    def cwd(self, path: str) -> str:
        """
        切换远程工作目录。

        :param path: 目标路径
        :return: 服务器返回的响应字符串
        """
        return self.__ftpc.cwd(path)

    def dir(self, *args) -> None:
        """
        打印当前目录的文件列表（详细格式）。可传入参数，如 dir("-la")。
        """
        print("========== 当前目录:", restrop(self.pwd(), f=2))
        self.__ftpc.dir(*args)
        print("==========")

    def list_files(self, path: str = "") -> List[str]:
        """
        获取指定目录下的文件和文件夹名称列表（NLST 命令）。

        :param path: 远程目录路径，默认为当前目录
        :return: 名称列表
        """
        return self.__ftpc.nlst(path or self.pwd())

    def list_details(self, path: str = "") -> List[Dict]:
        """
        获取指定目录下文件和文件夹的详细信息（使用 MLSD 命令，如果服务器支持）。

        :param path: 远程目录路径
        :return: 字典列表，每个字典包含 name, type, size, modify, perm 等字段
        :raises FTPError: 如果服务器不支持 MLSD
        """
        try:
            lines = []
            self.__ftpc.retrlines(f'MLSD {path}', lines.append)
            result = []
            for line in lines:
                facts, name = line.split(' ', 1)
                info = {'name': name}
                for fact in facts.split(';'):
                    if '=' in fact:
                        k, v = fact.split('=', 1)
                        info[k.lower()] = v
                result.append(info)
            return result
        except ftplib.error_perm as e:
            raise Exception(f"MLSD 命令失败，服务器可能不支持: {e}") from None

    def rename(self, old: str, new: str) -> str:
        """重命名远程文件或目录。"""
        return self.__ftpc.rename(old, new)

    def delete(self, filename: str) -> str:
        """删除远程文件。"""
        return self.__ftpc.delete(filename)

    def rmd(self, dirname: str) -> str:
        """删除空目录。"""
        return self.__ftpc.rmd(dirname)

    def mkd(self, dirname: str) -> str:
        """创建目录。"""
        return self.__ftpc.mkd(dirname)

    def size(self, filename: str) -> int:
        """获取远程文件大小（字节）。"""
        self.__ftpc.voidcmd('TYPE I')
        return self.__ftpc.size(filename)

    # ---------- 传输模式 ----------
    def set_passive(self, passive: bool = True) -> None:
        """设置是否使用被动模式。"""
        self.__ftpc.set_pasv(passive)

    @vargs({"mode": {"I", "A"}})
    def set_mode(self, mode: str = 'I') -> None:
        """
        设置传输模式：'I' 二进制，'A' ASCII。
        :param mode: 'I' 或 'A'
        """
        if mode.upper() == 'I':
            self.__ftpc.voidcmd('TYPE I')
        elif mode.upper() == 'A':
            self.__ftpc.voidcmd('TYPE A')
        else:
            raise ValueError("模式必须是 'I' 或 'A'") from None

    # ---------- 文件上传 ----------
    def upload(self, local_file: str, remote_name: str = "", blocksize: int = 8192,
               callback: Optional[Callable[[int, int], None]] = None) -> None:
        """
        上传文件到当前远程目录。

        :param local_file: 本地文件路径
        :param remote_name: 远程文件名，默认使用本地文件名
        :param blocksize: 传输块大小（字节）
        :param callback: 进度回调函数，接收 (已传输字节, 总字节)
        :raises FileNotFoundError: 本地文件不存在
        :raises FTPError: 上传失败
        """
        if not os.path.isfile(local_file):
            raise FileNotFoundError(f"本地文件不存在: {local_file}") from None

        remote_name = remote_name or os.path.basename(local_file)
        file_size = os.path.getsize(local_file)

        with open(local_file, 'rb') as f:
            # 如果没有回调，使用 tqdm 进度条
            if callback is None:
                with trange(file_size, desc=f'上传 {truncate_fname(remote_name)}',
                            unit='B', unit_divisor=1024, unit_scale=True) as t:
                    def _inner_cb(data):
                        t.update(len(data))
                        if callback:
                            callback(t.n, file_size)

                    self.__ftpc.storbinary(f'STOR {remote_name}', f, blocksize, callback=_inner_cb)
            else:
                # 自定义回调
                total = [0]

                def _cb(data):
                    total[0] += len(data)
                    callback(total[0], file_size)

                self.__ftpc.storbinary(f'STOR {remote_name}', f, blocksize, callback=_cb)

    def upload_dir(self, local_dir: str, remote_dir: str = "", blocksize: int = 8192,
                   callback: Optional[Callable[[str, int, int], None]] = None) -> None:
        """
        递归上传本地目录到远程。

        :param local_dir: 本地目录路径
        :param remote_dir: 远程目标目录，默认为当前目录下的同名文件夹
        :param blocksize: 传输块大小
        :param callback: 每个文件上传进度的回调，接收 (相对路径, 已传字节, 总字节)
        """
        if not os.path.isdir(local_dir):
            raise NotADirectoryError(f"本地目录不存在: {local_dir}") from None

        base_name = os.path.basename(local_dir)
        target_remote = remote_dir or base_name

        # 确保远程目录存在
        try:
            self.cwd(target_remote)
        except ftplib.error_perm:
            self.mkd(target_remote)
            self.cwd(target_remote)

        for root, dirs, files in os.walk(local_dir):
            # 计算相对路径
            rel_path = os.path.relpath(root, local_dir)
            if rel_path == '.':
                rel_path = ''

            # 切换到对应远程目录
            if rel_path:
                remote_path = os.path.join(target_remote, rel_path).replace('\\', '/')
                try:
                    self.cwd(remote_path)
                except ftplib.error_perm:
                    # 逐级创建目录
                    parts = rel_path.split(os.sep)
                    current = target_remote
                    for part in parts:
                        current += '/' + part
                        try:
                            self.cwd(current)
                        except:
                            self.mkd(current)
                            self.cwd(current)

            # 上传文件
            for file in files:
                local_file = os.path.join(root, file)
                remote_file = file
                if callback:
                    # 包装回调，加入文件路径
                    def make_cb(rel=os.path.join(rel_path, file)):
                        def inner(sent, total):
                            callback(rel, sent, total)

                        return inner

                    self.upload(local_file, remote_file, blocksize, callback=make_cb())
                else:
                    self.upload(local_file, remote_file, blocksize)

            # 处理子目录（由 walk 自动处理）

    # ---------- 文件下载 ----------
    def download(self, remote_file: str, local_path: str = ".", local_name: str = "",
                 blocksize: int = 8192, resume: bool = False,
                 callback: Optional[Callable[[int, int], None]] = None) -> None:
        """
        下载远程文件到本地。

        :param remote_file: 远程文件路径（可以是绝对路径或相对当前目录）
        :param local_path: 本地保存目录
        :param local_name: 本地文件名，默认使用远程文件名
        :param blocksize: 传输块大小
        :param resume: 是否断点续传（若本地已存在部分文件，则从断点处继续）
        :param callback: 进度回调，接收 (已传字节, 总字节)
        :raises FTPError: 下载失败
        """
        # 确保本地目录存在
        os.makedirs(local_path, exist_ok=True)

        # 确定本地文件路径
        remote_basename = os.path.basename(remote_file)
        local_filename = local_name or remote_basename
        local_filepath = os.path.join(local_path, local_filename)

        # 获取远程文件大小
        file_size = self.size(remote_file)

        # 断点续传：获取本地已存在大小
        local_size = 0
        mode = 'wb'
        if resume and os.path.exists(local_filepath):
            local_size = os.path.getsize(local_filepath)
            if local_size < file_size:
                mode = 'ab'
                # 发送 REST 命令设置偏移量
                self.__ftpc.voidcmd(f'REST {local_size}')
            else:
                self.__logger.info(f"文件 {local_filename} 已完整存在，跳过下载。")
                return

        with open(local_filepath, mode) as f:
            if callback is None:
                with trange(file_size, initial=local_size, desc=f'下载 {truncate_fname(remote_file)}',
                            unit='B', unit_divisor=1024, unit_scale=True) as t:
                    def _inner_cb(data):
                        f.write(data)
                        t.update(len(data))

                    self.__ftpc.retrbinary(f'RETR {remote_file}', _inner_cb, blocksize)
            else:
                total = [local_size]

                def _cb(data):
                    f.write(data)
                    total[0] += len(data)
                    callback(total[0], file_size)

                self.__ftpc.retrbinary(f'RETR {remote_file}', _cb, blocksize, rest=local_size if resume else None)

    def download_dir(self, remote_dir: str, local_dir: str = ".", blocksize: int = 8192,
                     callback: Optional[Callable[[str, int, int], None]] = None) -> None:
        """
        递归下载远程目录到本地。

        :param remote_dir: 远程目录路径
        :param local_dir: 本地保存根目录
        :param blocksize: 传输块大小
        :param callback: 每个文件下载进度的回调，接收 (相对路径, 已传字节, 总字节)
        """
        # 切换到远程目录，保存当前路径
        original_pwd = self.pwd()
        self.cwd(remote_dir)
        remote_base = remote_dir.rstrip('/')

        # 获取当前目录下的所有项目
        items = self.list_details('.')

        for item in items:
            name = item['name']
            if name in ('.', '..'):
                continue
            item_type = item.get('type')
            if item_type == 'dir' or item_type == 'pdir':  # 目录
                sub_remote = name
                sub_local = os.path.join(local_dir, name)
                self.download_dir(sub_remote, sub_local, blocksize, callback)
            else:  # 文件
                remote_path = name
                local_subdir = local_dir
                if callback:
                    def make_cb(rel=name):
                        def inner(sent, total):
                            callback(rel, sent, total)

                        return inner

                    self.download(remote_path, local_subdir, blocksize=blocksize, callback=make_cb())
                else:
                    self.download(remote_path, local_subdir, blocksize=blocksize)

        # 恢复原目录
        self.cwd(original_pwd)

    # ---------- 递归删除 ----------
    def rmtree(self, remote_dir: str) -> None:
        """
        递归删除远程目录及其所有内容。

        :param remote_dir: 远程目录路径
        """
        original_pwd = self.pwd()
        try:
            self.cwd(remote_dir)
        except ftplib.error_perm:
            # 可能不是目录，尝试删除文件
            try:
                self.delete(remote_dir)
            except:
                pass
            return

        items = self.list_details('.')
        for item in items:
            name = item['name']
            if name in ('.', '..'):
                continue
            if item.get('type') == 'dir':
                self.rmtree(name)
            else:
                self.delete(name)
        self.cwd(original_pwd)
        self.rmd(remote_dir)

    # ---------- 原始命令发送 ----------
    def send_command(self, cmd: str) -> str:
        """
        发送原始 FTP 命令并返回响应。

        :param cmd: FTP 命令字符串（如 "SYST"）
        :return: 服务器响应字符串
        """
        return self.__ftpc.voidcmd(cmd)

    # ---------- 重连 ----------
    def reconnect(self) -> None:
        """重新连接服务器（使用当前参数）。"""
        self.quit()
        self.__ftpc = ftplib.FTP()
        self.__ftpc.encoding = self.encoding
        self.__ftpc.connect(self.host, self.port, timeout=self.timeout)
        self.__ftpc.login(self.username, self.password)
        self.set_passive(self.passive)


__all__ = ["Ftpserver", "Ftpclient"]
