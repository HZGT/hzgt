# -*- coding: utf-8 -*-
import os
import smtplib
import imaplib
import datetime

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import email.header
import email
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
            self.__logger = set_log("hzgt.smtp", os.path.join("logs", "smtp.log"), level=2)
        else:
            self.__logger = logger
        self.__logger.info(f"SMTP类初始化完成")

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
        self.__logger.info(f"正在连接SMTP服务器: {self.host}:{self.port}")
        self.__server.starttls()  # 启用TLS加密
        try:
            self.__server.login(self.user, self.passwd)
            self.__logger.info(f"SMTP客户端已登录, 登陆账号: {self.user}")
        except Exception as err:
            self.__logger.error(f"SMTP客户端登录失败, 错误信息: {err}")
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
            self.__logger.info(f"已添加收件人: {recipient}")

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
            self.__logger.info(f"已添加附件: {file_path}")

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
            self.__logger.info(f"邮件已发送至: {self.__recipients}")
        else:
            self.__logger.error("SMTP服务器未登录, 无法发送邮件")
            raise ConnectionError("SMTP服务器未登录")

    def close(self):
        """
        关闭SMTP连接
        """
        if self.__server:
            self.__server.quit()
            self.__logger.info("SMTP客户端已关闭")


class Imapop:
    def __init__(self, host, port, user, passwd, logger=None):
        """
        初始化IMAP客户端

        :param host: IMAP服务器主机地址
        :param port: IMAP服务器端口
        :param user: 用户名
        :param passwd: 密码
        :param logger: 日志记录器
        """
        self.host = host
        self.port = int(port)
        self.user = user
        self.passwd = passwd
        self.__imap = None

        if logger is None:
            self.__logger = set_log("hzgt.imap", os.path.join("logs", "imap.log"), level=2)
        else:
            self.__logger = logger
        self.__logger.info(f"IMAP类初始化完成")

    def __enter__(self):
        """
        上下文管理器进入方法, 登录IMAP服务器
        """
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器退出方法, 关闭SIMAP连接
        """
        self.close()

    def login(self):
        """
        连接到IMAP服务器
        """
        try:
            self.__imap = imaplib.IMAP4_SSL(self.host)
            self.__imap._encoding = 'UTF-8'
            self.__imap.login(self.user, self.passwd)
            if self.__logger:
                self.__logger.info('成功连接到IMAP服务器')
        except imaplib.IMAP4.error as e:
            if self.__logger:
                self.__logger.error(f'连接IMAP服务器时出错: {e}')
            raise

    def close(self):
        if self.__imap:
            self.__imap.logout()
            if self.__logger:
                self.__logger.info('已从IMAP服务器断开连接')

    def get_mailbox(self):
        """
        获取邮箱列表

        "INBOX"            表示收件箱
        "Sent Messages"    表示已发送邮件文件夹
        "Drafts"           表示草稿箱
        "Deleted Messages" 表示已删除邮件文件夹
        "Junk"             表示垃圾邮件文件夹
        """
        try:
            status, mailbox_list = self.__imap.list()
            if status == 'OK':
                mailbox_names = []
                for mailbox in mailbox_list:
                    parts = mailbox.decode().split(' "/" ')[-1][1:-1]
                    if "&" not in parts:
                        mailbox_names.append(parts)
                return mailbox_names
            else:
                if self.__logger:
                    self.__logger.error('获取邮箱列表失败')
                return []
        except imaplib.IMAP4.error as e:
            if self.__logger:
                self.__logger.error(f'获取邮箱列表时出错: {e}')
            return []

    def select_mailbox(self, mailbox_name: str = "INBOX"):
        """
        选择邮箱文件夹
        """
        self.__imap.select(mailbox_name)

    def parse_email(self, msg):
        # 解析发件人
        sender = msg.get('From')
        if sender:
            sender_parts = email.header.decode_header(sender)
            # print(sender_parts)
            decoded_sender = []
            for part in sender_parts:
                if part[1]:
                    try:
                        part_text = part[0].decode(part[1])
                    except Exception:
                        part_text = part[0].decode('utf-8', 'ignore')
                else:
                    try:
                        part_text = part[0].decode('utf-8', 'ignore')
                    except:
                        part_text = part[0]
                decoded_sender.append(part_text)
            # print(decoded_sender)
            sender = ''.join(decoded_sender)

        # 解析收件人
        recipient = msg.get('To')
        if recipient:
            recipient_parts = email.header.decode_header(recipient)
            decoded_recipient = []
            for part in recipient_parts:
                if part[1]:
                    try:
                        part_text = part[0].decode(part[1])
                    except Exception:
                        part_text = part[0].decode('utf-8', 'ignore')
                else:
                    try:
                        part_text = part[0].decode('utf-8', 'ignore')
                    except:
                        part_text = part[0]
                decoded_recipient.append(part_text)
            recipient = ''.join(decoded_recipient)

        # 解析主题
        subject = msg.get('Subject')
        if subject:
            subject_parts = email.header.decode_header(subject)
            decoded_subject = []
            for part in subject_parts:
                if part[1]:
                    try:
                        part_text = part[0].decode(part[1])
                    except Exception:
                        part_text = part[0].decode('utf-8', 'ignore')
                else:
                    try:
                        part_text = part[0].decode('utf-8', 'ignore')
                    except:
                        part_text = part[0]
                decoded_subject.append(part_text)
            subject = ''.join(decoded_subject)

        # 解析日期
        date_str = msg.get('Date')
        dt = ''
        if date_str:
            try:
                try:
                    dt = self.convert_date(date_str, mode=2)
                except:
                    dt = self.convert_date(date_str[:-6], mode=2)
            except ValueError:
                pass

        return {
            'sender': sender,
            'recipient': recipient,
            'subject': subject,
            'date': date_str,
            'cdate': dt,
        }

    @staticmethod
    def convert_date(s, mode):
        if mode == 1:
            endt = datetime.datetime.strptime(s, '%Y-%m-%d').strftime('%d-%b-%Y')
        elif mode == 2:
            endt = datetime.datetime.strptime(s, '%a, %d %b %Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        return endt

    def search_mailid(self, sender: str = None, subject: str = None, recipient: str = None, sincedate: str = None,
                      beforedate: str = None, status: str = None):
        """
        搜索邮件

        :param sender: 用于指定发件人的邮件地址
        :param subject: 用于指定邮件的主题
        :param recipient: 用于指定收件人的邮件地址
        :param sincedate: 用于指定搜索邮件的起始日期（在该日期之后） 格式 "2024-12-31"
        :param beforedate: 用于指定搜索邮件的截止日期（在该日期之前） 格式 "2024-12-31"
        :param status: 用于指定邮件的状态 “seen”[已读] 或 “unseen”[未读]
        """
        search_criteria = []
        if not (sender or subject or recipient or sincedate or beforedate or status):
            search_criteria.append('ALL')
        else:
            if sender:
                search_criteria.append(f'(FROM "{sender}")')
            if subject:
                search_criteria.append(f'SUBJECT "{subject}"')
            if recipient:
                search_criteria.append(f'(TO "{recipient}")')
            if sincedate:
                search_criteria.append(f'SINCE "{self.convert_date(sincedate, mode=1)}"')
            if beforedate:
                search_criteria.append(f'BEFORE "{self.convert_date(beforedate, mode=1)}"')
            if status:
                if status.lower() == 'seen':
                    search_criteria.append('SEEN')
                elif status.lower() == 'unseen':
                    search_criteria.append('UNSEEN')

        combined_criteria = " ".join(search_criteria)

        typ, data = self.__imap.search(None, combined_criteria)
        mail_ids = data[0].split()

        idresult = []
        for mail_id in mail_ids:
            typ, msg_data = self.__imap.fetch(mail_id, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            idresult.append(mail_id)
        return idresult

    def get_mail(self, mail_id: str):
        typ, msg_data = self.__imap.fetch(mail_id, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])
        return self.parse_email(msg)
