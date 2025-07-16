import click
import typing as t
import click.formatting


def __wrap_text(
        text: str,
        width: int = 78,
        initial_indent: str = "",
        subsequent_indent: str = "",
        preserve_paragraphs: bool = False,
) -> str:
    """A helper function that intelligently wraps text.  By default, it
    assumes that it operates on a single paragraph of text but if the
    `preserve_paragraphs` parameter is provided it will intelligently
    handle paragraphs (defined by two empty lines).

    If paragraphs are handled, a paragraph can be prefixed with an empty
    line containing the ``\\b`` character (``\\x08``) to indicate that
    no rewrapping should happen in that block.

    :param text: the text that should be rewrapped.
    :param width: the maximum width for the text.
    :param initial_indent: the initial indent that should be placed on the
                           first line as a string.
    :param subsequent_indent: the indent string that should be placed on
                              each consecutive line.
    :param preserve_paragraphs: if this flag is set then the wrapping will
                                intelligently handle paragraphs.
    """
    from click._compat import term_len
    from click._textwrap import TextWrapper

    text = text.expandtabs()
    wrapper = TextWrapper(
        width,
        initial_indent=initial_indent,
        subsequent_indent=subsequent_indent,
        replace_whitespace=False,
    )
    if not preserve_paragraphs:
        return wrapper.fill(text)

    p: t.List[t.Tuple[int, bool, str]] = []
    buf: t.List[str] = []
    indent = None

    def _flush_par() -> None:
        if not buf:
            return
        if buf[0].strip() == "\b":
            p.append((indent or 0, True, "\n".join(buf[1:])))
        else:
            p.append((indent or 0, False, " ".join(buf)))
        del buf[:]

    for line in text.splitlines():
        if not line:
            _flush_par()
            indent = None
        else:
            if indent is None:
                orig_len = term_len(line)
                line = line.lstrip()
                indent = orig_len - term_len(line)
            buf.append(line)
    _flush_par()

    rv = []
    for indent, raw, text in p:
        with wrapper.extra_indent(" " * indent):
            if raw:
                rv.append(wrapper.indent_only(text))
            else:
                rv.append(wrapper.fill(text))
    return "\n".join(rv)


click.formatting.wrap_text = __wrap_text

# ================================================== 重写 wrap_text 函数 =================================================

# -*- coding: utf-8 -*-

import os

from .tools import Ftpserver, Fileserver
from .core.ipss import getip
from .core.CONST import CURRENT_USERNAME

__HELP_CTRL_SET_DICT = {'help_option_names': ['-h', '--help']}  # 让 -h 与 --help 功能一样


@click.group(context_settings=__HELP_CTRL_SET_DICT)
def __losf():
    """
    ftps  FTP服务端

    fs    HZGT文件服务器

    ips 输出IP列表
    """
    pass


@click.command(context_settings=__HELP_CTRL_SET_DICT, epilog="")  # epilog 末尾额外信息
@click.argument('directory', default=os.getcwd(), type=click.STRING)
@click.option("-r", "--res", default=getip(-1), type=click.STRING, help="选填- IP地址", show_default=True)
@click.option("-p", "--port", default=5001, type=click.INT, help="选填- 端口", show_default=True)
@click.option("-pe", "--perm", default="elradfmwMT", type=click.STRING, help="选填- 权限", show_default=True)
@click.option("-u", "--user", default=CURRENT_USERNAME, type=click.STRING, help="选填- 用户名", show_default=True)
@click.option("-pw", "--password", default=CURRENT_USERNAME, type=click.STRING, help="选填- 密码", show_default=True)
def ftps(directory, res, port, perm, user, password):
    """
    FTP服务器端模块

    perm:

        + 读取权限

            * "e" | 更改目录

            * "l" | 列表文件

            * "r" | 从服务器检索文件

        + 写入权限

            * "a" | 将数据追加到现有文件

            * "d" | 删除文件或目录

            * "f" | 重命名文件或目录

            * "m" | 创建目录

            * "w" | 将文件存储到服务器

            * "M" | 更改 文件模式 / 权限

            * "T" | 更改文件修改时间

    :param directory: FTP主目录

    :param res: IP地址 默认 局域网地址

    :param port: 端口 默认 5001

    :param perm: 权限 默认 "elradfmwMT"

    :param user: 用户名 默认计算机名

    :param password: 密码 默认计算机名
    """
    click.echo(f"工作目录: {directory}\n")
    fs = Ftpserver()
    fs.add_user(directory, user, password, perm=perm)
    fs.set_log()
    fs.start(res, port)


@click.command(context_settings=__HELP_CTRL_SET_DICT, epilog="")
@click.argument('directory', default=os.getcwd(), type=click.STRING, required=False)
@click.option("-r", "--res", default=getip(-1), type=click.STRING,
              help="选填- IP地址 或者在 `hzgt ips` 命令长度之间(如需输入负数, 使用`-- -3`的方式)", show_default=True)
@click.option("-p", "--port", default=9090, type=click.INT, help="选填- 端口", show_default=True)
def fs(directory, res, port):
    """
    HZGT 文件服务器

    :param directory: 目录 默认当前目录

    :param res: 选填- IP地址 或者在 `hzgt ips` 命令长度之间

    :param port: 选填- 端口
    """
    tempips = getip()
    if res in [f"{i}" for i in range(-len(tempips), len(tempips))]:
        res = tempips[int(res)]
    Fileserver(directory, res, port)


@click.command(context_settings=__HELP_CTRL_SET_DICT, epilog="")
@click.argument('index', nargs=1, type=click.INT, required=False, default=None)
def ips(index):
    """
    获取本机 IP 列表

    如果 索引 index 为 负数, 请使用 ```hzgt ips -- -1```

    :param index: 如果指定 index, 则返回 IP地址列表 中索引为 index 的 IP, 否则返回 IP地址列表

    """
    print(getip(index))


__losf.add_command(ftps)
__losf.add_command(fs)
__losf.add_command(ips)

if __name__ == "__main__":
    __losf()
