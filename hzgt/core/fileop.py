# -*- coding: utf-8 -*-

import os

import urllib.request
from typing import Optional, Union, Tuple

import unicodedata


def bitconv(fsize: int) -> tuple[float, str, int]:
    """
    字节单位转换

    :param fsize: 大小（字节）
    :return: 转换后的大小（保留两位小数）, 单位, 原大小
    """
    units = ["Byte", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB", "BB"]
    size = fsize
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    if unit_index == 0:  # Byte 单位时返回整数
        return int(size), units[unit_index], fsize
    return round(size, 2), units[unit_index], fsize


def _get_dir_size(dirpath: str) -> int:
    """
    计算目录大小（递归）

    :param dirpath: 目录路径
    :return: 目录总字节数
    :raises NotADirectoryError: 如果路径不是目录
    :raises OSError: 权限不足等系统错误
    """
    if not os.path.isdir(dirpath):
        raise NotADirectoryError(f"路径不是目录: {dirpath}")

    total = 0
    for root, dirs, files in os.walk(dirpath):
        for name in files:
            filepath = os.path.join(root, name)
            try:
                total += os.path.getsize(filepath)
            except OSError as e:
                # 可以记录日志或直接忽略权限错误的文件
                # 这里简单跳过，或者抛出异常（按需选择）
                # 为了健壮性，我们选择跳过无法访问的文件
                continue
    return total


def getfsize(filepath: str, timeout: int = 5) -> Tuple[Union[int, float], str, int]:
    """
    获取目录、文件或URL指向的资源的总大小

    :param filepath: 本地路径或URL
    :param timeout: URL请求超时时间
    :return: (转换后的大小, 单位, 原字节数)
    :raises ValueError: 路径不存在或无法获取大小
    :raises urllib.error.URLError: URL访问错误
    """
    # 本地路径处理
    if os.path.exists(filepath):
        try:
            if os.path.isdir(filepath):
                fsize = _get_dir_size(filepath)
            else:
                fsize = os.path.getsize(filepath)
            return bitconv(fsize)
        except Exception as e:
            raise ValueError(f"无法获取本地路径大小: {e}") from e

    # URL处理
    with urllib.request.urlopen(filepath, timeout=timeout) as resp:
        # 某些服务器可能不返回 Content-Length
        content_length = resp.headers.get("Content-Length")
        if content_length is None:
            raise ValueError("服务器未返回 Content-Length，无法获取文件大小")
        fsize = int(content_length)
        return bitconv(fsize)


def ensure_file(file_path: str) -> None:
    """
    确保文件及其目录存在。如果目录不存在则创建，如果文件不存在则创建空文件。

    如果指定路径已存在且为目录，则抛出 FileExistsError。
    如果文件已存在且为普通文件，则不做任何修改。

    :param file_path: 文件路径
    :raises FileExistsError: 如果路径存在且为目录
    :raises OSError: 目录创建失败或文件创建失败
    """
    normalized_path = os.path.normpath(file_path)
    dir_path = os.path.dirname(normalized_path)

    # 检查路径是否已存在且为目录
    if os.path.exists(normalized_path):
        if os.path.isdir(normalized_path):
            raise FileExistsError(f"路径已存在且为目录: {normalized_path}")
        # 是文件，已存在，直接返回
        return

    # 创建目录
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    # 创建空文件
    open(normalized_path, 'a').close()


def ensure_suffix(
        name: str,
        fname: Optional[str] = None,
        suffix: str = ".log"
) -> str:
    """
    生成文件名，确保以指定的 suffix 结尾。

    如果提供了 fname，优先使用 fname 作为基础名，否则使用 name。
    无论原文件名是否有扩展名，都会被替换为 suffix（除非原文件名已以 suffix 结尾）。

    :param name: 基础名称（当 fname 未提供时使用）
    :param fname: 可选的自定义文件名
    :param suffix: 期望的文件后缀（会自动确保以点开头）
    :return: 处理后的文件名
    """
    # 确保 suffix 以点开头
    if not suffix.startswith("."):
        suffix = f".{suffix.lstrip('.')}"

    base_name = fname if fname is not None else name

    # 如果已经以目标后缀结尾，直接返回
    if base_name.endswith(suffix):
        return base_name

    # 分离主名和最后一个扩展名（使用 splitext 更安全）
    main_part, old_ext = os.path.splitext(base_name)
    return main_part + suffix


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def _char_width(char: str) -> int:
    """
    返回单个字符的显示宽度，基于Unicode East Asian Width属性。
    全角字符宽度为2，半角为1。
    """
    code = ord(char)
    # 常见范围
    if code <= 0x7F:  # ASCII
        return 1
    # 使用unicodedata获取East Asian Width
    ea = unicodedata.east_asian_width(char)
    if ea in ('F', 'W'):  # Fullwidth, Wide
        return 2
    if ea == 'A':  # Ambiguous
        # 在中文环境下通常视为2
        return 1
    # 其他：Na, H, N 都视为半角
    return 1


def _str_width(s: str) -> int:
    """返回字符串的总显示宽度"""
    return sum(_char_width(ch) for ch in s)


def _split_prefix_by_width(s: str, max_width: int) -> str:
    """
    从字符串开头截取，使得截取部分的显示宽度不超过 max_width。
    不会切分一个完整字符（如汉字）。
    """
    width = 0
    for i, ch in enumerate(s):
        w = _char_width(ch)
        if width + w > max_width:
            return s[:i]
        width += w
    return s


def _split_suffix_by_width(s: str, max_width: int) -> str:
    """
    从字符串末尾截取，使得截取部分的显示宽度不超过 max_width。
    """
    width = 0
    # 从后往前遍历
    for i in range(len(s) - 1, -1, -1):
        w = _char_width(s[i])
        if width + w > max_width:
            return s[i + 1:]
        width += w
    return s


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def truncate_fname(filename: str, max_len: int = 30,
                   front_len: Optional[int] = None,
                   back_len: Optional[int] = None,
                   min_front: int = 1) -> str:
    """
    文本显示格式化文件名，按视觉宽度截断为 "前段...后段.后缀" 格式。

    中文字符宽度计为2，英文字符宽度计为1，确保截断后的字符串在等宽终端中
    视觉宽度不超过 max_len。

    :param filename: 原始文件名 (e.g., "my_very_long_document_file_name.txt")
    :param max_len: 允许的最大视觉宽度（包括扩展名和省略号）
    :param front_len: 前段目标视觉宽度（不计扩展名），若为 None 则自动分配
    :param back_len: 后段目标视觉宽度（不计扩展名），若为 None 则自动分配
    :param min_front: 前段最小视觉宽度（默认 1），调整时不会低于此值
    :return: 格式化后的字符串，视觉宽度不超过 max_len
    """
    # 分离文件名主部和扩展名
    name_part, ext = os.path.splitext(filename)
    ext_width = _str_width(ext)

    # 计算整个文件名的视觉宽度
    total_width = _str_width(name_part) + ext_width

    # 如果整个文件名宽度不超过最大宽度，直接返回
    if total_width <= max_len:
        return filename

    # 最小需求宽度：省略号(3) + 扩展名
    min_required = 3 + ext_width
    if max_len < min_required:
        # 极端情况：连省略号+扩展名都放不下，则只返回省略号+扩展名（可能超宽，但尽力）
        if ext_width > 0:
            return "..." + ext
        else:
            return "..."

    # 可用于主名的宽度（扣除扩展名和省略号）
    available = max_len - ext_width - 3

    # 自动分配前后宽度（如果未指定）
    if front_len is None and back_len is None:
        # 平均分配，余数给前段
        front_len = (available + 1) // 2
        back_len = available // 2
    elif front_len is None:
        # 只提供了 back_len，自动计算 front_len
        front_len = max(min_front, available - back_len)
        if front_len + back_len > available:
            # 如果超出，按比例缩减
            total = front_len + back_len
            front_len = max(min_front, int(front_len * available / total))
            back_len = max(1, int(back_len * available / total))
    elif back_len is None:
        # 只提供了 front_len，自动计算 back_len
        back_len = max(1, available - front_len)
        if front_len + back_len > available:
            total = front_len + back_len
            front_len = max(min_front, int(front_len * available / total))
            back_len = max(1, int(back_len * available / total))
    else:
        # 两者都提供了，如果总和超出可用宽度，按比例缩减
        if front_len + back_len > available:
            total = front_len + back_len
            front_len = max(min_front, int(front_len * available / total))
            back_len = max(1, int(back_len * available / total))
            # 再次检查取整后是否仍超出
            if front_len + back_len > available:
                # 优先缩减前段（后段通常更重要）
                front_len = available - back_len
                if front_len < min_front:
                    front_len = min_front
                    back_len = available - min_front

    # 确保前后宽度不超过实际主名的宽度（按宽度计算）
    name_width = _str_width(name_part)
    front_len = min(front_len, name_width)
    back_len = min(back_len, name_width)

    # 截取前后部分（按宽度，不切分字符）
    front_part = _split_prefix_by_width(name_part, front_len)
    back_part = _split_suffix_by_width(name_part, back_len) if back_len > 0 else ""

    # 组合
    if ext:
        formatted = f"{front_part}...{back_part}{ext}"
    else:
        formatted = f"{front_part}...{back_part}"

    # 检查最终宽度，若仍超宽则逐步缩减后段，再缩减前段
    if _str_width(formatted) > max_len:
        # 优先缩减后段
        current_back = back_len
        while _str_width(formatted) > max_len and current_back > 0:
            current_back -= 1
            back_part = _split_suffix_by_width(name_part, current_back) if current_back > 0 else ""
            if ext:
                formatted = f"{front_part}...{back_part}{ext}"
            else:
                formatted = f"{front_part}...{back_part}"

        # 如果后段已减至0仍超宽，缩减前段（但保证前段 >= min_front）
        current_front = front_len
        while _str_width(formatted) > max_len and current_front > min_front:
            current_front -= 1
            front_part = _split_prefix_by_width(name_part, current_front)
            back_part = _split_suffix_by_width(name_part, current_back) if current_back > 0 else ""
            if ext:
                formatted = f"{front_part}...{back_part}{ext}"
            else:
                formatted = f"{front_part}...{back_part}"

        # 最终保险：直接截断（理论上不会发生）
        if _str_width(formatted) > max_len:
            # 按宽度截断整个字符串（可能破坏格式）
            formatted = _split_prefix_by_width(formatted, max_len)

    return formatted
