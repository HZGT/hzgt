# -*- coding: utf-8 -*-

import os

import urllib.request
from typing import Optional


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
    增强对Windows系统同名文件冲突的处理。

    :param file_path: 文件路径
    """
    # 标准化路径并获取目录路径
    normalized_path = os.path.normpath(file_path)
    dir_path = os.path.dirname(normalized_path)

    # 仅当目录路径非空时才处理目录创建
    if dir_path:
        # 检查路径是否已存在
        if os.path.exists(dir_path):
            # 如果路径存在但不是目录（即文件），则引发错误
            if not os.path.isdir(dir_path):
                raise FileExistsError(
                    f"创建目录失败 '{dir_path}' 因为该路径已存在且不是目录"
                )
            # 如果是目录，则跳过创建（正常情况）
        else:
            # 路径不存在，安全创建目录
            os.makedirs(dir_path, exist_ok=True)

    # 安全创建文件（仅当文件不存在时）
    if not os.path.exists(normalized_path):
        open(normalized_path, 'a').close()


def generate_filename(
    name: str,
    fname: Optional[str] = None,
    suffix: str = ".log"
) -> str:
    """
    生成文件名（避免双重扩展，支持自定义后缀）

    :param name: 基础名称（当 fname 未提供时使用）
    :param fname: 可选的自定义文件名
    :param suffix: 期望的文件后缀（必须以点开头，默认为 .log）
    :return: 正确的文件名（确保以指定的 suffix 结尾）
    """
    if not suffix.startswith("."):
        suffix = f".{suffix.lstrip('.')}"

    # 优先使用 fname
    if fname is not None:
        base, _, ext = fname.rpartition(".")
        if ext and fname.endswith(suffix):
            return fname
        if base:  # 有其它扩展名或无扩展名
            return f"{base}{suffix}"
        return f"{fname}{suffix}"

    # 处理 name
    base, _, ext = name.rpartition(".")
    if ext and name.endswith(suffix):
        return name
    if base:
        return f"{base}{suffix}"
    return f"{name}{suffix}"


def format_filename(filename: str, max_len: int = 30, front_len: int = 10, back_len: int = 10) -> str:
    """
    格式化文件名，超长时截断为 "前段...后段.后缀" 格式

    :param filename: 原始文件名 (e.g., "my_very_long_document_file_name.txt")
    :param max_len: 允许的最大显示长度
    :param front_len: 截断时保留的前段字符数
    :param back_len: 截断时保留的后段字符数 (不包含扩展名)
    :return: 格式化后的文件名
    """
    # 分离文件名主部和扩展名
    name_part, ext = os.path.splitext(filename)

    # 如果文件名本身不超过最大长度，直接返回
    if len(filename) <= max_len:
        return filename

    # 如果即使截断也无法满足最大长度要求，直接返回缩短版（极端情况处理）
    if max_len < (front_len + back_len + 3 + len(ext)):
        # 3是省略号"..."的长度
        return name_part[:max_len - len(ext) - 3] + "..." + ext

    # 正常截断处理
    # 前段部分
    front_part = name_part[:front_len]
    # 后段部分（从后往前取back_len个字符）
    back_part = name_part[-back_len:] if back_len > 0 else ""

    # 组合成新文件名
    formatted_name = f"{front_part}...{back_part}.{ext}"

    return formatted_name
