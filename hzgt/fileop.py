import os
import sys

import urllib.request

from .sc import SCError


def Bit_Unit_Conversion(fsize: int):
    """
    字节单位转换

    (大小,单位,原大小)

    :param fsize: 大小
    :return: 大小,单位,原大小
    """
    if fsize < 1024:
        return fsize, 'Byte', fsize
    else:
        KBX = fsize / 1024
        if KBX < 1024:
            return round(KBX, 2), 'KB', fsize
        else:
            MBX = KBX / 1024
            if MBX < 1024:
                return round(MBX, 2), 'MB', fsize
            else:
                return round(MBX / 1024, 2), 'GB', fsize


def getdirsize(dirpath: str):
    """
    :param dirpath:目录或者文件
    :return: size: 目录或者文件的大小
    """
    size = 0
    print(os.path.isdir(dirpath), os.path.isfile(dirpath))
    if os.path.isdir(dirpath): # 如果是目录
        for root, dirs, files in os.walk(dirpath):
            size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
        return size
    elif os.path.isfile(dirpath):  # 如果是文件
        size = os.path.getsize(dirpath)
        return size
    else:
        raise SCError("目录/文件 不存在")



def getFileSize(filepath: str):
    """
    获取目录或文件的总大小

    :param filePath: 目录或者文件
    :return: 例子：(2, 'M', 2048)
    """
    fsize = getdirsize(filepath)  # 返回的是字节大小
    return Bit_Unit_Conversion(fsize)


def getUrlFileSize(url: str):
    """
    获取url上的文件的总大小

    :param url: 网络url
    :return: 例子：(2, 'M', 2048)
    """
    response = urllib.request.urlopen(url)
    file_size = int(response.headers["Content-Length"])
    return Bit_Unit_Conversion(file_size)
