# -*- coding: utf-8 -*-

import ftplib
import logging
import os
import time

from ..fileop import get_file_size, bit_conversion
from ..strop import restrop

from tqdm import trange

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler, ThrottledDTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.log import LogFormatter


class Ftpserver:
    def __init__(self):
        """
            >>>fs = Ftpserver()

            >>>fs.add_user("/path/to/", "user", "123456", "elradfmw")

            >>>fs.set_log()

            >>>fs.start()
        """
        self.__authorizer = DummyAuthorizer()
        self.__handler = FTPHandler

    def add_user(self, homedir: str, username: str = "anonymous", password: str = "", perm: str = ""):
        """
        添加用户权限和路径 可以为不同的用户添加不同的目录和权限 如果 username 为空, 则添加匿名用户 anonymous

        + 读取权限:
            - "e" = 更改目录 (CWD 命令)
            - "l" = 列出文件 (LIST、NLST、STAT、MLSD、MLST、SIZE、MDTM 命令)
            - "r" = 从服务器检索文件 (RETR 命令)

       + 写入权限:
            - "a" = 将数据附加到现有文件 (APPE 命令)
            - "d" = 删除文件或目录 (DELE、RMD 命令)
            - "f" = 重命名文件或目录 (RNFR、RNTO 命令)
            - "m" = 创建目录 (MKD 命令)
            - "w" = 将文件存储到服务器 (STOR、STOU 命令)
            - "M" = 更改文件模式 (SITE CHMOD 命令)
            - "T" = 更新文件上次修改时间 (MFMT 命令)

        :param username: str: 用户名称  如果为空, 则添加匿名用户 anonymous
        :param password: str: 用户密码
        :param homedir: str: 目录
        :param perm: str: 权限组合体 ”elradfmw“ 表示对应的所有权限
        :return:
        """
        if not os.path.exists(homedir):
            os.mkdir(homedir)

        if username:  # 添加用户
            self.__authorizer.add_user(username, password, homedir, perm)
        else:  # 添加匿名用户
            self.__authorizer.add_anonymous(homedir)

    def remove_user(self, username: str):
        """
        删除用户

        :param username: 待删除的用户名
        :return:
        """
        return self.__authorizer.remove_user(username)

    def correct_user(self, oldusername: str,
                     newdir: str = "", newusername: str = "", newpassword: str = "", newperm: str = ""):
        """
        修正用户信息

        + 读取权限:
            - "e" = 更改目录 (CWD 命令)
            - "l" = 列出文件 (LIST、NLST、STAT、MLSD、MLST、SIZE、MDTM 命令)
            - "r" = 从服务器检索文件 (RETR 命令)

       + 写入权限:
            - "a" = 将数据附加到现有文件 (APPE 命令)
            - "d" = 删除文件或目录 (DELE、RMD 命令)
            - "f" = 重命名文件或目录 (RNFR、RNTO 命令)
            - "m" = 创建目录 (MKD 命令)
            - "w" = 将文件存储到服务器 (STOR、STOU 命令)
            - "M" = 更改文件模式 (SITE CHMOD 命令)
            - "T" = 更新文件上次修改时间 (MFMT 命令)

        :param oldusername: 需要修正的用户名
        :param newdir: 可选 新路径
        :param newusername: 可选 新用户名
        :param newpassword: 可选 新密码
        :param newperm: 可选 新权限组合体 ”elradfmw“ 表示拥有所有权限
        :return: None
        """
        _temp_dict = self.__authorizer.user_table[oldusername]
        old_dir = _temp_dict["home"]
        old_un = oldusername
        old_pwd = _temp_dict["pwd"]
        old_perm = _temp_dict["perm"]

        newdir = newdir if newdir else old_dir
        newusername = newusername if newusername else old_un
        newpassword = newpassword if newpassword else old_pwd
        newperm = newperm if newperm else old_perm

        self.remove_user(oldusername)
        self.add_user(newdir, newusername, newpassword, newperm)
        return self.__authorizer.user_table

    def set_log(self, logfilename: str = "ftps.log", level=logging.INFO, encoding="utf-8"):
        """
        + level
            * logging.CRITICAL
            * logging.FATAL
            * logging.ERROR
            * logging.WARNING
            * logging.WARN
            * logging.INFO
            * logging.DEBUG
            * logging.NOTSET

        :param logfilename: FTP日志路径 默认 "ftp.log"
        :param level: 日志级别 默认 logging.INFO
        :param encoding: 编码 默认 utf-8
        :return:
        """
        logfilename = logfilename if logfilename else "ftps.log"

        logger = logging.getLogger()
        logger.setLevel(level)

        stream = logging.StreamHandler()
        log_file = logging.FileHandler(filename=logfilename, encoding=encoding)

        stream.setFormatter(LogFormatter())
        log_file.setFormatter(LogFormatter())

        logger.addHandler(stream)
        logger.addHandler(log_file)

    def start(self, host_res: str = "127.0.0.1", port: int = 2121,
              passive_port_range: None = range(6000, 7000), read_limit: int = 300, write_limit: int = 300,
              max_cons: int = 30, max_cons_per_ip: int = 10):
        """
        开启服务器

        :param host_res: IP地址 默认 127.0.0.1
        :param port: 端口 默认 2121

        :param passive_port_range: 被动端口范围 默认 range(6000, 7000)
        :param read_limit: 上传速度设置 单位 kB/s 默认 300
        :param write_limit: 下载速度设置 单位 kB/s 默认 300

        :param max_cons: 最大连接数 默认 30
        :param max_cons_per_ip: IP最大连接数 默认 10
        :return:
        """
        host_res = host_res if host_res else "127.0.0.1"
        port = int(port) if port else 2121
        passive_port_range = passive_port_range if passive_port_range else range(6000, 7000)
        read_limit = read_limit if read_limit else 300
        write_limit = write_limit if write_limit else 300
        max_cons = max_cons if max_cons else 30
        max_cons_per_ip = max_cons_per_ip if max_cons_per_ip else 10

        # 加载用户
        self.__handler.authorizer = self.__authorizer
        # 添加被动端口范围
        self.__handler.passive_ports = passive_port_range

        # 上传下载的速度设置 单位kB/s
        dtp_handler = ThrottledDTPHandler
        dtp_handler.read_limit = read_limit * 1024 * 8
        dtp_handler.write_limit = write_limit * 1024 * 8
        self.__handler.dtp_handler = dtp_handler

        # 监听ip和端口 linux需要root用户才能使用21端口
        self.server = FTPServer((host_res, port), self.__handler)

        # 最大连接数
        self.server.max_cons = max_cons
        self.server.max_cons_per_ip = max_cons_per_ip
        print(f"HOST & PORT: {restrop(host_res)} {restrop(port, f=2)}")
        # 开始服务
        self.server.serve_forever()

    def shutdown(self):
        """
        关闭服务器
        :return:
        """
        self.server.close_all()
        self.server.close()
        # self.server.shutdown()


class Ftpclient:
    def __init__(self, host: str, port: int = 2121, username: str = "anonymous", password: str = "",
                 encoding: str = "utf-8"):
        """
        FTP客户端

        :param host: 目标主机IP
        :param port: 端口 默认 2121
        :param username: 用户昵称 默认为 anonymous
        :param password: 密码
        :param encoding: 默认编码为 UTF-8
        """
        username = username if username else "anonymous"
        self.ftpc = ftplib.FTP()
        self.ftpc.encoding = encoding
        self.ftpc.connect(host, int(port))
        self.ftpc.login(username, password)
        print(f"`{restrop(username, f=4)}` 登陆FTP服务器 `{restrop(host)}`")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()
        return exc_type, exc_val, exc_tb

    def dir(self, *args):
        """
        打印目录的文件信息

        :param args:
        :return:
        """
        print("========== " + restrop("当前工作目录:", f=2) + " " + restrop(self.ftpc.pwd(), f=4))
        self.ftpc.dir(*args)
        print("========== ==========")

    def pwd(self):
        """
        获取当前的工作目录

        :return: 返回当前的工作目录
        """
        return self.ftpc.pwd()

    def quit(self):
        """
        关闭连接

        :return:
        """
        self.ftpc.quit()

    def getfile(self, server_filename: str, savepath: str = "FTP_Files", savename: str = "", blocksize: int = 8 * 1024):
        """
        从服务器下载文件保存至本地

        :param server_filename: 服务器上待下载的文件 文件格式: "/path/to/thing.txt"
        :param savepath: 保存路径 默认保存在 同目录下 新建 文件夹 "FTP_Files"
        :param savename: 保存的文件名 为空则默认服务器命名
        :param blocksize: 下载块大小
        :return:
        """
        file_name, extension = os.path.splitext(os.path.basename(server_filename))
        savepath = savepath if savepath else "FTP_Files"
        savename = savename if savename else file_name + extension

        if not os.path.exists(savepath):
            os.makedirs(savepath)

        sfsize = bit_conversion(self.size(server_filename))  # 转换总大小
        print(f"[{restrop(server_filename)}] 文件大小: {restrop(sfsize[0], f=4)} {sfsize[1]}")
        with (trange(sfsize[2], desc='下载中', unit="B", unit_divisor=1024, unit_scale=True, ncols=100) as tbar,
              open(os.path.join(savepath, savename), "wb") as file_handle):  # 以写模式在本地打开文件
            def _callback(data):
                file_handle.write(data)
                tbar.update(len(data))  # 更新进度条

            self.ftpc.retrbinary(f"RETR {server_filename}", callback=_callback,
                                 blocksize=blocksize)  # 接收服务器上文件并写入本地文件

    def upload(self, local_file: str, server_savename: str = "", blocksize: int = 8 * 1024):
        """
        上传文件至当前工作目录

        :param local_file: 本地文件路径
        :param server_savename: 新命名 默认本地文件名
        :param blocksize: 上传块大小
        :return:
        """
        file_name, extension = os.path.splitext(os.path.basename(local_file))
        server_savename = server_savename if server_savename else file_name + extension  # 默认使用本地命名

        lfsize = get_file_size(local_file)  # 获取文件大小
        print(f"[{restrop(local_file)}] 文件大小: {restrop(lfsize[0], f=4)} {lfsize[1]}")
        time.sleep(0.17)
        with (trange(lfsize[2], desc='上传中', unit="B", unit_divisor=1024, unit_scale=True, ncols=100) as tbar,
              open(local_file, 'rb') as file_handle):
            def _callback(data):
                tbar.update(len(data))  # 更新进度条

            self.ftpc.storbinary(f"STOR {server_savename}", file_handle,
                                 blocksize=blocksize, callback=_callback)

    def size(self, sname: str):
        """
        获取服务器上文件的大小

        :param sname: 目标文件
        :return:
        """
        self.ftpc.voidcmd('TYPE I')
        return self.ftpc.size(sname)

    def list_show(self, spath: str = ""):
        """
        打印服务器目录里的文件列表

        :param spath: 服务器的目录
        :return:
        """
        spath = spath if spath else self.pwd()  # 默认查看当前工作目录的文件列表

        print("========== " + restrop("目录文件列表: ", f=2) + " " + restrop(spath, f=4))
        self.ftpc.retrlines('LIST ' + spath)
        print("========== ==========")

    def nlst(self, spath: str):
        """
        获取目标目录中所有的 文件夹 / 文件

        :param spath: 目标目录
        :return: list 所有 文件夹 / 文件 组成的 list
        """
        return self.ftpc.nlst(spath)

    def rmd(self, spath: str):
        """
        删除目标目录

        :param spath: 目标目录
        :return:
        """
        return self.ftpc.rmd(spath)

    def delete(self, sname: str):
        """
        删除远程文件

        :param sname: 远程文件名
        :return:
        """
        return self.ftpc.delete(sname)

    def rename(self, oldsname: str, newsname: str):
        """
        将文件 `oldsname` 修改名称为 `newsname`

        :param oldsname: 旧文件名
        :param newsname: 新文件名
        :return:
        """
        return self.ftpc.rename(oldsname, newsname)

    def cwd(self, spath):
        """
        设置FTP当前操作的路径

        :param spath: 需要设置为当前工作路径的路径
        :return:
        """
        self.ftpc.cwd(spath)  # 设置FTP当前操作的路径

    def mkd(self, spath):
        """
        创建新目录

        :param spath: 新目录
        :return:
        """
        return self.ftpc.mkd(spath)


__all__ = ["Ftpserver", "Ftpclient"]
