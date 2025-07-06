# -*- coding: utf-8 -*-

import os

import urllib.request


def bitconv(fsize: int):
    """
    字节单位转换

    :param fsize: 大小（字节）
    :return: 转换后的大小（保留两位小数），单位
    """
    units = ["Byte", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB", "BB"]
    size = fsize
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    if unit_index == 0:  # Byte 单位时返回整数
        return size, units[unit_index]
    return round(size, 2), units[unit_index]


def __get_dir_size(dirpath: str):
    """
    :param dirpath:目录或者文件
    :return: size: 目录或者文件的大小
    """
    size = 0
    if os.path.isdir(dirpath):  # 如果是目录
        for root, dirs, files in os.walk(dirpath):
            size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
        return size
    elif os.path.isfile(dirpath):  # 如果是文件
        size = os.path.getsize(dirpath)
        return size
    else:
        raise NotADirectoryError("目录/文件 不存在")


def getfsize(filepath: str, timeout: int = 5):
    """
    获取目录、文件或URL指向的资源的总大小

    :param filepath: 目录路径、文件路径或URL
    :param timeout: URL文件请求超时时间
    :return: 转换后的大小和单位元组，如(6.66, 'MB')。失败时报错
    """
    # 先尝试作为本地路径处理
    if os.path.exists(filepath):
        try:
            if os.path.isdir(filepath):
                fsize = __get_dir_size(filepath)  # 目录大小
            else:
                fsize = os.path.getsize(filepath)  # 文件大小
            return bitconv(fsize)
        except Exception as e:
            raise ValueError(f"本地路径处理错误: {e}")

    # 尝试作为URL处理
    try:
        with urllib.request.urlopen(filepath, timeout=timeout) as response:
            fsize = int(response.headers["Content-Length"])
            return bitconv(fsize)
    except Exception as err:
        raise ValueError(f"URL处理错误: {err}")


def ensure_file(file_path: str) -> None:
    """
    确保文件及其目录存在。如果目录或文件不存在，则创建它们。

    :param file_path: 文件路径
    """
    # 获取文件所在的目录（并确保路径标准化）
    dir_path = os.path.dirname(os.path.normpath(file_path))

    # 使用makedirs的exist_ok参数简化目录创建
    if dir_path:  # 避免创建空路径（如当前目录）
        os.makedirs(dir_path, exist_ok=True)

    # 仅当文件不存在时创建（避免意外覆盖）
    if not os.path.exists(file_path):
        open(file_path, 'a').close()  # 使用追加模式安全创建
