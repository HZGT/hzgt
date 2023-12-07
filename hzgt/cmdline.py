# -*- coding: utf-8 -*-
import os
import sys
import locale
import subprocess
import time

from .CONST import INSTALLCMD

try:
    import click
except Exception as err:
    print(err)
    os.system(INSTALLCMD("click"))
    import click

from .strop import restrop
from .CONST import DEFAULT_ENCODING, PLATFORM, CURRENT_USERNAME


def CmdLine(cmd: str, encoding: str=DEFAULT_ENCODING):
    """
    执行cmd命令时可以查看输出的内容
    :param cmd: str 命令
    :param encoding: str 编码 默认使用系统编码
    """
    process = subprocess.Popen(['cmd', '/c', cmd],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,  # shell=True,
                               encoding=encoding)

    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output.strip() != '':
            print(output)  # .strip())

    """
    if encoding == '':
        encoding = DEFAULT_ENCODING
    screenData = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    current_line: str = ' '
    while True:
        line = screenData.stdout.readline().replace(b"\r\n", b"")
        _line = line.decode(encoding).strip("b'")
        print(_line)
        time.sleep(0.017)
        if current_line == _line == '':  # or subprocess.Popen.poll(screenData) == 0:
            screenData.stdout.close()
            break
        current_line = _line
    """

@click.group()
def losf():
    """
    - d 命令行 下载\n
        - m: 功能参数 1-文件下载 2-github仓库下载 3-视频下载\n
        - u: 文件/仓库/视频所在的url\n
        - s: 保存路径
    """
    pass

@click.command()
@click.option("-m", "--mode", default=None, type=click.INT, help="功能参数 1-文件下载 2-github仓库下载 3-视频下载")
@click.option("-u", "--url", default=None, type=click.STRING, help="文件/仓库/视频所在的url")
@click.option("-s", "--save", default='', type=click.STRING, help="保存路径")
def d(mode, url, save):
    """
    命令行 下载
    """
    if mode is None:
        os.system("hzgt d --help")
        exit()
    if mode not in [1, 2, 3]:
        print(f"功能参数 {mode} 无效")
        exit()
    from .download.download import downloadmain
    if save == '':
        if 'linux' in PLATFORM:  # linux
            downloadmain(mode, url, savepath=os.path.join("/home", CURRENT_USERNAME, "Download"))
        elif 'win' in PLATFORM:  # win
            downloadmain(mode, url, savepath="d:\\Download")
        else:
            currentpath = os.getcwd()
            downloadmain(mode, url, savepath=currentpath)
    else:
        downloadmain(mode, url, savepath=save)


losf.add_command(d)
if __name__ == "__main__":
    losf()