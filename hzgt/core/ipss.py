import ipaddress
import socket

import re

from typing import Union, List, Tuple, Optional, Dict, Any, Literal

import psutil


# def __get_ipv4_addresses() -> List[str]:
#     """
#     获取本机的 ipv4 地址列表
#     """
#     # 获取主机名
#     hostname = socket.gethostname()
#
#     # 获取 ipv4 地址列表
#     ipv4_addresses = socket.gethostbyname_ex(hostname)[-1]
#
#     # 尝试通过连接获取更多可能的 ipv4 地址
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     try:
#         sock.connect(('10.255.255.255', 1))
#         additional_ip = sock.getsockname()[0]
#         if additional_ip not in ipv4_addresses:
#             ipv4_addresses.append(additional_ip)
#     except Exception:
#         pass
#     finally:
#         sock.close()
#
#     # 确保包含本地回环地址
#     if '127.0.0.1' not in ipv4_addresses:
#         ipv4_addresses.insert(0, '127.0.0.1')
#
#     return ipv4_addresses
#
#
# def __get_ipv6_addresses() -> List[str]:
#     """
#     获取本机的 ipv6 地址列表
#     """
#     # 获取主机名
#     hostname = socket.gethostname()
#
#     # 获取 ipv6 地址列表
#     ipv6_addresses = []
#     try:
#         addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET6)
#         ipv6_addresses = [info[4][0] for info in addr_info]
#     except socket.gaierror:
#         pass
#
#     # 尝试通过连接获取更多可能的 ipv6 地址
#     sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
#     try:
#         sock.connect(('2402:4e00::', 1))
#         additional_ip = sock.getsockname()[0]
#         if additional_ip not in ipv6_addresses:
#             ipv6_addresses.append(additional_ip)
#     except Exception as err:
#         pass  # 不支持公网 IPV6
#     finally:
#         sock.close()
#
#     return ipv6_addresses
#
#
# def getip(index: int = None) -> Union[str, List[str]]:
#     """
#     获取本机 IP 地址
#
#     :param index: 如果指定 index, 则返回 IP 地址列表中索引为 index 的 IP, 否则返回 IP 地址列表
#     :return: IP 地址 或 IP 地址列表
#     """
#     if index is not None and not isinstance(index, int):
#         raise TypeError("参数 index 必须为整数 或为 None")
#
#     # 获取 ipv4 和 ipv6 地址列表
#     addresses = __get_ipv6_addresses() + __get_ipv4_addresses()
#
#     # 根据 index 返回结果
#     if index is None:
#         return addresses
#     else:
#         if index >= len(addresses):
#             raise IndexError(f"索引超出范围, 最大索引为 {len(addresses)}")
#         return addresses[index]
def getip(
        index: Optional[int] = None,
        details: bool = False,
        family: Literal['ipv4', 'ipv6', 'mac'] = None,
        ignore_local: bool = False,
        include_mac: bool = False
) -> Union[List[Dict[str, Any]], Dict[str, Any], List[str], str]:
    """
    获取本机网络接口的IP地址信息, 按接口名称合并

    :param index: 如果指定, 则返回地址列表中指定索引的单个结果
    :param details: 为True时返回包含详细信息的字典列表；为False时仅返回IP地址字符串
    :param family: 过滤地址族, 可选 'ipv4', 'ipv6', 'mac'
    :param ignore_local: 为True时过滤掉环回地址（127.0.0.1, ::1）和链路本地地址（fe80::）
    :param include_mac: 为True时包含mac地址信息
    :return: 根据参数返回字典列表、单个字典、IP字符串列表或单个IP字符串
    :raises TypeError: 当index参数类型错误时
    :raises ValueError: 当family参数不合法时
    :raises IndexError: 当index超出地址列表范围时
    """
    # 参数验证
    if index is not None and not isinstance(index, int):
        raise TypeError("参数 'index' 必须为整数或 None")

    # 定义family映射到socket常量
    family_mapping = {
        'ipv4': socket.AF_INET,
        'ipv6': socket.AF_INET6,
        'mac': psutil.AF_LINK
    }

    # 将字符串family转换为对应的socket常量
    socket_family = None
    if family is not None:
        if family not in family_mapping:
            raise ValueError(f"family参数必须为 'ipv4', 'ipv6', 'mac' 之一, 而不是 '{family}'")
        socket_family = family_mapping[family]
        # 如果family是'mac', 确保include_mac为True
        if family == 'mac':
            include_mac = True

    # 按接口名称分组收集地址信息
    interface_dict = {}

    for iface_name, iface_addrs in psutil.net_if_addrs().items():
        # 初始化接口字典
        if iface_name not in interface_dict:
            interface_dict[iface_name] = {
                'name': iface_name,
                'ipv4': [],
                'ipv6': [],
                'mac': []
            }

        for addr_info in iface_addrs:
            current_family = addr_info.family
            ip_address = addr_info.address

            # 1. 按地址族过滤
            if socket_family is not None and current_family != socket_family:
                continue

            # 2. 应用本地地址过滤
            if ignore_local and _is_local_address(ip_address):
                continue

            # 根据地址族类型添加到不同列表
            if current_family == socket.AF_INET:
                interface_dict[iface_name]['ipv4'].append(ip_address)
            elif current_family == socket.AF_INET6:
                interface_dict[iface_name]['ipv6'].append(ip_address)
            elif current_family == psutil.AF_LINK:
                if include_mac:
                    interface_dict[iface_name]['mac'].append(ip_address)

    # 转换为列表并过滤空接口、调整数据结构
    all_interfaces = []
    for iface_name, iface_data in interface_dict.items():
        # 如果指定了family但该接口没有该family的地址, 则跳过
        if socket_family is not None:
            if socket_family == socket.AF_INET and not iface_data['ipv4']:
                continue
            elif socket_family == socket.AF_INET6 and not iface_data['ipv6']:
                continue
            elif socket_family == psutil.AF_LINK and not iface_data['mac']:
                continue

        # 简化为单值而不是列表（如果只有一个地址）
        simplified_data = {'name': iface_name}

        # 处理ipv地址
        if len(iface_data['ipv4']) == 1:
            simplified_data['ipv4'] = iface_data['ipv4'][0]
        elif len(iface_data['ipv4']) > 1:
            simplified_data['ipv4'] = iface_data['ipv4']

        # 处理ipv6地址
        if len(iface_data['ipv6']) == 1:
            simplified_data['ipv6'] = iface_data['ipv6'][0]
        elif len(iface_data['ipv6']) > 1:
            simplified_data['ipv6'] = iface_data['ipv6']

        # 处理mac地址
        if include_mac:
            if len(iface_data['mac']) == 1:
                simplified_data['mac'] = iface_data['mac'][0]
            elif len(iface_data['mac']) > 1:
                simplified_data['mac'] = iface_data['mac']

        # 只有当接口至少有一种地址时才添加到结果列表
        if len(simplified_data) > 1:  # 除了name之外还有其他键
            all_interfaces.append(simplified_data)

    # 按接口名称排序, 但将WLAN排在最后
    def get_sort_key(_interface):
        name = _interface['name']
        return (1, '') if name == 'WLAN' else (0, name)

    all_interfaces.sort(key=get_sort_key)

    # 根据参数返回结果
    if index is not None:
        if index >= len(all_interfaces):
            raise IndexError(
                f"索引 {index} 超出范围列表共有 {len(all_interfaces)} 个接口"
            )
        result = all_interfaces[index]

        if not details:
            # 返回该接口的所有IP地址列表
            all_ips = []
            if 'ipv4' in result:
                if isinstance(result['ipv4'], list):
                    all_ips.extend(result['ipv4'])
                else:
                    all_ips.append(result['ipv4'])
            if 'ipv6' in result:
                if isinstance(result['ipv6'], list):
                    all_ips.extend(result['ipv6'])
                else:
                    all_ips.append(result['ipv6'])
            # 当family为'mac'时, 只返回mac地址
            if family == 'mac' and 'mac' in result:
                if isinstance(result['mac'], list):
                    all_ips.extend(result['mac'])
                else:
                    all_ips.append(result['mac'])
            return all_ips[0] if len(all_ips) == 1 else all_ips
        return result

    # 返回列表
    if details:
        return all_interfaces

    # 返回所有接口的所有IP地址列表
    all_ips = []
    for interface in all_interfaces:
        # 根据family参数决定返回哪些地址
        if family == 'ipv4':
            if 'ipv4' in interface:
                if isinstance(interface['ipv4'], list):
                    all_ips.extend(interface['ipv4'])
                else:
                    all_ips.append(interface['ipv4'])
        elif family == 'ipv6':
            if 'ipv6' in interface:
                if isinstance(interface['ipv6'], list):
                    all_ips.extend(interface['ipv6'])
                else:
                    all_ips.append(interface['ipv6'])
        elif family == 'mac':
            if 'mac' in interface:
                if isinstance(interface['mac'], list):
                    all_ips.extend(interface['mac'])
                else:
                    all_ips.append(interface['mac'])
        else:  # family为None, 返回所有类型地址
            if 'ipv4' in interface:
                if isinstance(interface['ipv4'], list):
                    all_ips.extend(interface['ipv4'])
                else:
                    all_ips.append(interface['ipv4'])
            if 'ipv6' in interface:
                if isinstance(interface['ipv6'], list):
                    all_ips.extend(interface['ipv6'])
                else:
                    all_ips.append(interface['ipv6'])
            if include_mac and 'mac' in interface:
                if isinstance(interface['mac'], list):
                    all_ips.extend(interface['mac'])
                else:
                    all_ips.append(interface['mac'])

    return all_ips


def _is_local_address(ip: str) -> bool:
    """
    判断一个IP地址是否为本地地址（环回或链路本地）
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_loopback or ip_obj.is_link_local
    except ValueError:
        return False


def validate_ip(ip_str: str) -> dict:
    """
    验证IP地址有效性并返回类型信息

    参数:
        ip_str (str): 要验证的IP地址字符串

    返回:
        dict: 包含验证结果的字典, 格式为:
            {
                "valid": bool,       # IP是否有效
                "type": str or None,  # "ipv4"、"ipv6" 或 None(无效时)
                "normalized": str    # 标准化后的IP地址(有效时)
            }

    """
    # 尝试匹配ipv
    ipv4_pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"

    if re.match(ipv4_pattern, ip_str):
        # 检查每个部分是否在0-255范围内
        parts = list(map(int, ip_str.split(".")))
        if all(0 <= p <= 255 for p in parts):
            return {
                "valid": True,
                "type": "ipv4",
                "normalized": ip_str  # ipv不需要特殊标准化
            }

    # 尝试匹配ipv6（支持多种格式）
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
        # 标准化ipv6地址
        normalized = __normalize_ipv6(ip_str)
        return {
            "valid": True,
            "type": "ipv6",
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
    标准化ipv6地址（RFC 5952格式）

    1. 小写十六进制字符
    2. 压缩连续的零段（使用::）
    3. 移除前导零
    4. 处理ipv映射地址

    参数:
        ipv6_str (str): 原始ipv6地址字符串

    返回:
        str: 标准化后的ipv6地址
    """
    # 如果包含ipv映射部分（::ffff:192.168.1.1）
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
            # 移除前导零, 但保留至少一个字符
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
