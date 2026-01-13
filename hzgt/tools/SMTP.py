# -*- coding: utf-8 -*-
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Union, Iterable

from hzgt.core.log import set_log


class Smtpop:
    """
    基于SMTPLib库封装, 提供SMTP邮件发送功能
    """

    def __init__(self, host: str, port: int, user: str, passwd: str, logger=None):
        """
        初始化SMTP客户端

        :param host: SMTP服务器地址 例如: "smtp.qq.com"
        :param port: SMTP服务器端口 例如: 587
        :param user: 登录用户名
        :param passwd: 授权码

        :param logger: 日志记录器
        """
        self.host = host
        self.port = int(port)
        self.user = user
        self.passwd = passwd
        self.__server = None
        self.__recipients = []  # 收件人列表
        self.__msg = MIMEMultipart()  # 邮件信息

        if logger is None:
            self.__logger = set_log("hzgt.smtp", fpath="logs", fname="smtp", level=2)
        else:
            self.__logger = logger
        self.__logger.info(f"SMTP类初始化完成", stacklevel=3)

    def __enter__(self):
        """
        上下文管理器进入方法, 登录SMTP服务器
        """
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器退出方法, 关闭SMTP连接
        """
        self.close()

    def login(self):
        """
        登录SMTP服务器
        """
        self.__server = smtplib.SMTP(self.host, self.port)
        self.__logger.info(f"正在连接SMTP服务器: {self.host}:{self.port}", stacklevel=3)
        self.__server.starttls()  # 启用TLS加密
        try:
            self.__server.login(self.user, self.passwd)
            self.__logger.info(f"SMTP客户端已登录, 登陆账号: {self.user}", stacklevel=3)
        except Exception as err:
            self.__logger.error(f"SMTP客户端登录失败, 错误信息: {err}", stacklevel=3)
            raise

    def add_recipient(self, recipient: Union[str, Iterable[str]], *args):
        """
        添加收件人

        :param recipient: 收件人邮箱地址
        :type recipient: Union[str, Iterable[str]]

        :param args: *args也能接受单个的收件人邮箱地址或者可迭代的收件人邮箱地址容器(如列表、元组、集合)
        """
        try:
            # 处理主参数
            if isinstance(recipient, str):
                self._add_unique_recipient(recipient)
            elif isinstance(recipient, Iterable):
                self._add_unique_recipients(recipient)
            else:
                raise TypeError("Recipient 必须是字符串或字符串的可迭代对象")

            # 处理 *args 参数
            for arg in args:
                if isinstance(arg, str):
                    self._add_unique_recipient(arg)
                elif isinstance(arg, Iterable):
                    self._add_unique_recipients(arg)
                else:
                    raise TypeError("*args 中的每个参数都必须是字符串或字符串的可迭代对象")
        except Exception as e:
            raise Exception(f"添加收件人时出错: {e}") from None

    def _add_unique_recipient(self, recipient: str):
        """
        添加单个收件人

        :param recipient: 收件人邮箱地址
        :return:
        """
        if recipient not in self.__recipients:
            self.__recipients.append(recipient)
            self.__logger.info(f"已添加收件人: {recipient}", stacklevel=4)

    def _add_unique_recipients(self, recipients: Iterable):
        """
        添加多个收件人

        :param recipients: 可迭代对象
        :return:
        """
        for r in recipients:
            if r not in self.__recipients:
                self._add_unique_recipient(r)

    def add_file(self, file_path: str):
        """
        添加附件到邮件中

        :param file_path: 附件文件路径
        """
        with open(file_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={file_path}")
            self.__msg.attach(part)
            self.__logger.info(f"已添加附件: {file_path}", stacklevel=3)

    def send(self, subject: str, body: str, html=False):
        """
        发送邮件

        :param subject: 邮件主题
        :param body: 邮件正文
        :param html: 布尔值, 指示邮件正文是否为HTML格式默认为False
        """
        self.__msg["From"] = self.user
        self.__msg["To"] = ", ".join(self.__recipients)
        self.__msg["Subject"] = subject

        if html:
            self.__msg.attach(MIMEText(body, "html"))
        else:
            self.__msg.attach(MIMEText(body, "plain"))
        # 发送邮件
        if self.__server:
            self.__server.sendmail(self.user, self.__recipients, self.__msg.as_string())
            self.__logger.info(f"邮件已发送至: {self.__recipients}", stacklevel=3)
        else:
            self.__logger.error("SMTP服务器未登录, 无法发送邮件", stacklevel=3)
            raise ConnectionError("SMTP服务器未登录")

    def close(self):
        """
        关闭SMTP连接
        """
        if self.__server:
            self.__server.quit()
            self.__logger.info("SMTP客户端已关闭", stacklevel=3)

