import typing as t

import click
import click.formatting
from tabulate import tabulate


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

from .__version import __version__ as hzgt_version
from .tools import Ftpserver, Fileserver
from .core.ipss import getip
from .core.CONST import CURRENT_USERNAME

__HELP_CTRL_SET_DICT = {'help_option_names': ['-h', '--help']}  # 让 -h 与 --help 功能一样


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# group
# hzgt -v
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def print_version(ctx, param, value):
    """版本选项的回调函数"""
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"当前版本: {hzgt_version}")
    ctx.exit()  # 显示版本后退出


@click.group(context_settings=__HELP_CTRL_SET_DICT)
@click.option('-v', '--version',
              is_flag=True,
              callback=print_version,
              expose_value=False,
              is_eager=True,  # 确保优先处理
              help='显示版本信息')
def __losf():
    """HZGT 工具箱"""
    pass  # 无需任何逻辑


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# hzgt ftps
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
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


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# hzgt fs
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
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


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# hzgt ips
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
@click.command(context_settings=__HELP_CTRL_SET_DICT, epilog="")
@click.argument('index', nargs=1, type=click.INT, required=False, default=None)
@click.option('-d', '--details', is_flag=True, default=False,
              help='显示详细信息（接口名称、地址类型等）')
@click.option('-f', '--family', type=click.Choice(['ipv4', 'ipv6', 'mac', 'all']),
              default='all', help='筛选地址类型: ipv4, ipv6, mac 或 all')
@click.option('-i', '--ignore-local', is_flag=True, default=False,
              help='过滤本地地址（127.0.0.1, ::1, fe80::）')
@click.option('--no-mac', is_flag=True, default=False,
              help='不显示mac地址（当family=all时有效）')
@click.option('-t', '--table', is_flag=True, default=False,
              help='以表格形式显示详细信息（自动启用--details）')
@click.option('-j', '--json', is_flag=True, default=False,
              help='以JSON格式输出（适合程序处理）')
def ips(index, details, family, ignore_local, no_mac, table, json):
    """
    获取本机网络接口信息

    如果索引 index 为负数，请使用: hzgt ips -- -1

    ⚠️ 重要提示：

      选项（如 -j, -d, -t 等）必须放在 -- 之前

      正确：hzgt ips -j -- -1

      错误：hzgt ips -- -1 -j

    示例:

      # 1. 基础用法

      hzgt ips                  # 所有IP地址

      hzgt ips 0                # 第一个IP地址

      hzgt ips -- -1            # 最后一个IP地址（负数索引）

      # 2. 筛选功能

      hzgt ips -f ipv4          # 只显示ipv4地址

      hzgt ips -f ipv6          # 只显示ipv6地址

      hzgt ips -f mac           # 只显示mac地址

      hzgt ips -f ipv4 --no-mac # ipv4地址，不显示mac

      # 3. 显示模式

      hzgt ips -d               # 详细信息（默认格式）

      hzgt ips -t               # 表格形式（更清晰）

      hzgt ips -j               # JSON格式（程序友好）

      hzgt ips -i               # 过滤本地地址

      # 4. 混合模式

      hzgt ips -j -f ipv4 -- -1         # 以json格式显示最后一个IP地址信息(仅ipv4)
    """
    # 处理参数逻辑
    if table:
        details = True  # 表格模式自动启用详细信息

    if family == 'all':
        family_param = None
    else:
        family_param = family

    if json:
        result = getip(
            index=index,
            details=True,
            family=family_param,
            ignore_local=ignore_local,
            include_mac=not no_mac
        )
    else:
        result = getip(
            index=index,
            details=details,
            family=family_param,
            ignore_local=ignore_local,
            include_mac=not no_mac
        )

    # 格式化输出
    output = _format_output(result, details, table, json, index)
    click.echo(output)


def _format_output(result, details, table, json_format, index=None):
    """格式化输出结果"""
    if json_format:
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)

    if not details:
        # 简单IP列表输出
        if isinstance(result, list):
            if len(result) == 0:
                return "未找到匹配的地址"
            return "\n".join(str(ip) for ip in result)
        else:
            return str(result)

    # 详细信息输出
    if isinstance(result, dict):
        # 单个接口
        return _format_single_interface(result, table)
    elif isinstance(result, list) and result:
        # 接口列表
        return _format_interface_list(result, table, index)

    return "未找到匹配的网络接口"


def _format_single_interface(interface, table):
    """格式化单个接口信息"""
    if table:
        return _create_interface_table([interface])

    output = [f"接口: {interface['name']}"]

    for key in ['ipv4', 'ipv6', 'mac']:
        if key in interface:
            value = interface[key]
            if isinstance(value, list):
                if value:
                    output.append(f"  {key}:")
                    for item in value:
                        output.append(f"    - {item}")
            elif value:
                output.append(f"  {key}: {value}")

    return "\n".join(output)


def _format_interface_list(interfaces, table, index):
    """格式化接口列表"""
    if not interfaces:
        return "未找到网络接口"

    if table:
        return _create_interface_table(interfaces)

    output = []
    for i, interface in enumerate(interfaces):
        if index is None:
            output.append(f"[{i}] {interface['name']}")
        else:
            output.append(f"{interface['name']}")

        for key in ['ipv4', 'ipv6', 'mac']:
            if key in interface:
                value = interface[key]
                if isinstance(value, list):
                    if value:
                        output.append(f"  {key}:")
                        for item in value:
                            output.append(f"    - {item}")
                elif value:
                    output.append(f"  {key}: {value}")

        if i < len(interfaces) - 1:
            output.append("─" * 40)

    return "\n".join(output)


def _create_interface_table(interfaces):
    """创建表格输出"""
    table_data = []

    for interface in interfaces:
        row = {
            '接口名称': interface['name'],
            'ipv4': _format_value(interface.get('ipv4')),
            'ipv6': _format_value(interface.get('ipv6')),
            'mac': _format_value(interface.get('mac'))
        }
        table_data.append(row)

    return tabulate(table_data, headers='keys', tablefmt='grid')


def _format_value(value):
    """格式化值：列表转字符串"""
    if isinstance(value, list):
        if not value:
            return ''
        return '\n'.join(value)
    return value if value else ''


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

__losf.add_command(ftps)
__losf.add_command(fs)
__losf.add_command(ips)

if __name__ == "__main__":
    __losf()
