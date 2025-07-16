import socket

import re

from typing import Union, List


def __get_ipv4_addresses() -> List[str]:
    """
    获取本机的 IPv4 地址列表
    """
    # 获取主机名
    hostname = socket.gethostname()

    # 获取 IPv4 地址列表
    ipv4_addresses = socket.gethostbyname_ex(hostname)[-1]

    # 尝试通过连接获取更多可能的 IPv4 地址
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(('10.255.255.255', 1))
        additional_ip = sock.getsockname()[0]
        if additional_ip not in ipv4_addresses:
            ipv4_addresses.append(additional_ip)
    except Exception:
        pass
    finally:
        sock.close()

    # 确保包含本地回环地址
    if '127.0.0.1' not in ipv4_addresses:
        ipv4_addresses.insert(0, '127.0.0.1')

    return ipv4_addresses


def __get_ipv6_addresses() -> List[str]:
    """
    获取本机的 IPv6 地址列表
    """
    # 获取主机名
    hostname = socket.gethostname()

    # 获取 IPv6 地址列表
    ipv6_addresses = []
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET6)
        ipv6_addresses = [info[4][0] for info in addr_info]
    except socket.gaierror:
        pass

    # 尝试通过连接获取更多可能的 IPv6 地址
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    try:
        sock.connect(('2402:4e00::', 1))
        additional_ip = sock.getsockname()[0]
        if additional_ip not in ipv6_addresses:
            ipv6_addresses.append(additional_ip)
    except Exception as err:
        pass  # 不支持公网 IPV6
    finally:
        sock.close()

    return ipv6_addresses


def getip(index: int = None) -> Union[str, List[str]]:
    """
    获取本机 IP 地址

    :param index: 如果指定 index, 则返回 IP 地址列表中索引为 index 的 IP, 否则返回 IP 地址列表
    :return: IP 地址 或 IP 地址列表
    """
    if index is not None and not isinstance(index, int):
        raise TypeError("参数 index 必须为整数 或为 None")

    # 获取 IPv4 和 IPv6 地址列表
    addresses = __get_ipv6_addresses() + __get_ipv4_addresses()

    # 根据 index 返回结果
    if index is None:
        return addresses
    else:
        if index >= len(addresses):
            raise IndexError(f"索引超出范围, 最大索引为 {len(addresses)}")
        return addresses[index]


def validate_ip(ip_str: str) -> dict:
    """
    验证IP地址有效性并返回类型信息

    参数:
        ip_str (str): 要验证的IP地址字符串

    返回:
        dict: 包含验证结果的字典，格式为:
            {
                "valid": bool,       # IP是否有效
                "type": str or None,  # "IPv4"、"IPv6" 或 None(无效时)
                "normalized": str    # 标准化后的IP地址(有效时)
            }

    """
    # 尝试匹配IPv4
    ipv4_pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
    
    if re.match(ipv4_pattern, ip_str):
        # 检查每个部分是否在0-255范围内
        parts = list(map(int, ip_str.split(".")))
        if all(0 <= p <= 255 for p in parts):
            return {
                "valid": True,
                "type": "IPv4",
                "normalized": ip_str  # IPv4不需要特殊标准化
            }

    # 尝试匹配IPv6（支持多种格式）
    ipv6_pattern = r'^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|' \
                   r'([0-9a-fA-F]{1,4}:){1,7}:|' \
                   r'([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|' \
                   r'([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|' \
                   r'([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|' \
                   r'([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|' \
                   r'([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|' \
                   r'[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|' \
                   r':((:[0-9a-fA-F]{1,4}){1,7}|:)|' \
                   r'fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|' \
                   r'::(ffff(:0{1,4}){0,1}:){0,1}' \
                   r'((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}' \
                   r'(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|' \
                   r'([0-9a-fA-F]{1,4}:){1,4}:' \
                   r'((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}' \
                   r'(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))(\%[\S]+)?$'

    if re.match(ipv6_pattern, ip_str):
        # 标准化IPv6地址
        normalized = __normalize_ipv6(ip_str)
        return {
            "valid": True,
            "type": "IPv6",
            "normalized": normalized
        }

    # 无效IP
    return {
        "valid": False,
        "type": None,
        "normalized": ""
    }


def __normalize_ipv6(ipv6_str: str) -> str:
    """
    标准化IPv6地址（RFC 5952格式）

    1. 小写十六进制字符
    2. 压缩连续的零段（使用::）
    3. 移除前导零
    4. 处理IPv4映射地址

    参数:
        ipv6_str (str): 原始IPv6地址字符串

    返回:
        str: 标准化后的IPv6地址
    """
    # 如果包含IPv4映射部分（::ffff:192.168.1.1）
    if '.' in ipv6_str and '::' in ipv6_str:
        parts = ipv6_str.split(':')
        ipv4_part = parts[-1]
        return '::ffff:' + ipv4_part

    # 移除所有前导零并小写
    segments = []
    for segment in ipv6_str.split(':'):
        if segment == '':
            segments.append('')
        else:
            # 移除前导零，但保留至少一个字符
            segment = segment.lstrip('0') or '0'
            segments.append(segment.lower())

    # 重建地址
    normalized = ':'.join(segments)

    # 压缩最长的连续零段（但避免压缩单个零段）
    best_start = -1
    best_length = 0
    current_start = -1
    current_length = 0

    # 查找最长的连续空段
    for i, seg in enumerate(segments):
        if seg == '' or seg == '0':
            if current_start == -1:
                current_start = i
            current_length += 1
        else:
            if current_length > best_length:
                best_start = current_start
                best_length = current_length
            current_start = -1
            current_length = 0

    # 检查末尾的连续零
    if current_length > best_length:
        best_start = current_start
        best_length = current_length

    # 如果有需要压缩的段
    if best_length > 1:
        # 构建压缩后的地址
        before = ':'.join(segments[:best_start])
        after = ':'.join(segments[best_start + best_length:])

        # 处理开头和结尾的特殊情况
        if not before and not after:
            return "::"
        elif not before:
            return "::" + after
        elif not after:
            return before + "::"
        else:
            return before + "::" + after

    return normalized

