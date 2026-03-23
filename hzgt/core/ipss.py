import os
import socket
from enum import Enum
from functools import lru_cache
from ipaddress import ip_address
from typing import Optional, List, Dict, Any, Union

import psutil


# ---------- 枚举定义 ----------
class AddressFamily(Enum):
    IPV4 = 'ipv4'
    IPV6 = 'ipv6'
    MAC = 'mac'


# ---------- 私有辅助函数 ----------
def _strip_ip_scope(address: str) -> Union[tuple[str, str], tuple[str, None]]:
    """分离IP地址中的 % 作用域标识 """
    if '%' in address:
        return address.split('%', 1)[0], address.split('%', 1)[1]
    return address, None


def _get_addr_properties(address: str, family: int):
    """
    返回 (is_loopback, is_link_local)
    对于MAC地址或解析失败的地址，两者均为False
    """
    if family not in (socket.AF_INET, socket.AF_INET6):
        return False, False
    try:
        clean_addr, _ = _strip_ip_scope(address)
        ip_obj = ip_address(clean_addr)
        return ip_obj.is_loopback, ip_obj.is_link_local
    except Exception:
        return False, False


def _get_wlan_names(wlan_names: Optional[List[str]]) -> List[str]:
    """获取无线接口名称前缀列表（用于排序放最后）"""
    if wlan_names is not None:
        return [name.strip().lower() for name in wlan_names]
    env_names = os.environ.get('GETIP_WLAN_NAMES', 'wlan')
    return [name.strip().lower() for name in env_names.split(',')]


def _validate_params(
        index: Optional[int],
        family: Optional[AddressFamily],
        include_mac: bool
) -> tuple:
    """
    验证参数并返回：
    - socket_family: 对应的socket地址族，或None
    - force_include_mac: 是否需要强制包含MAC（当family='mac'时）
    """
    if index is not None and not isinstance(index, int):
        raise TypeError("参数 'index' 必须为 整数 或 None")

    family_mapping = {
        AddressFamily.IPV4: socket.AF_INET,
        AddressFamily.IPV6: socket.AF_INET6,
        AddressFamily.MAC: psutil.AF_LINK
    }
    socket_family = None
    force_include_mac = include_mac

    if family is not None:
        if family not in family_mapping:
            raise ValueError(f"family参数必须为 {AddressFamily.IPV4}, {AddressFamily.IPV6}, {AddressFamily.MAC} 之一，而不是 '{family}'")
        socket_family = family_mapping[family]
        if family == AddressFamily.MAC:
            force_include_mac = True  # 强制包含MAC

    return socket_family, force_include_mac


def _build_interface_dict(
        socket_family: Optional[int],
        ignore_loopback: bool,
        ignore_link_local: bool,
        include_mac: bool
) -> Dict[str, Dict]:
    """
    遍历所有网络接口，构建原始数据字典：
    {
        iface_name: {
            'name': iface_name,
            'ipv4': [{'address':..., 'is_loopback':..., 'is_link_local':...}, ...],
            'ipv6': [...],
            'mac':  [{'address':...}, ...]
        }
    }
    已应用family、ignore_loopback、ignore_link_local过滤。
    """
    interface_dict = {}
    for iface_name, iface_addrs in psutil.net_if_addrs().items():
        if iface_name not in interface_dict:
            interface_dict[iface_name] = {
                'name': iface_name,
                'ipv4': [],
                'ipv6': [],
                'mac': []
            }

        for addr_info in iface_addrs:
            cur_family = addr_info.family
            raw_address = addr_info.address

            if socket_family is not None and cur_family != socket_family:
                continue

            is_loopback, is_link_local = _get_addr_properties(raw_address, cur_family)

            if ignore_loopback and is_loopback:
                continue
            if ignore_link_local and is_link_local:
                continue

            clean_address, _ = _strip_ip_scope(raw_address)
            addr_info_dict = {
                'address': clean_address,
                'is_loopback': is_loopback,
                'is_link_local': is_link_local
            }

            if cur_family == socket.AF_INET:
                interface_dict[iface_name]['ipv4'].append(addr_info_dict)
            elif cur_family == socket.AF_INET6:
                interface_dict[iface_name]['ipv6'].append(addr_info_dict)
            elif cur_family == psutil.AF_LINK and include_mac:
                interface_dict[iface_name]['mac'].append({'address': clean_address})

    return interface_dict


def _filter_and_sort_interfaces(
        interface_dict: Dict[str, Dict],
        socket_family: Optional[int],
        include_mac: bool,
        wlan_names: List[str]
) -> List[Dict]:
    """
    过滤掉空接口，转换为列表格式，并按规则排序（无线接口放最后）。
    返回列表中的每个字典格式同原函数中的接口字典。
    """
    all_interfaces = []
    for iface_name, data in interface_dict.items():
        # 根据family过滤空接口
        if socket_family == socket.AF_INET and not data['ipv4']:
            continue
        if socket_family == socket.AF_INET6 and not data['ipv6']:
            continue
        if socket_family == psutil.AF_LINK and not data['mac']:
            continue

        simplified = {'name': iface_name}
        if data['ipv4']:
            simplified['ipv4'] = data['ipv4']
        if data['ipv6']:
            simplified['ipv6'] = data['ipv6']
        if include_mac and data['mac']:
            simplified['mac'] = data['mac']

        if len(simplified) > 1:  # 至少包含一个地址
            all_interfaces.append(simplified)

    # 排序：无线接口放最后
    def _sort_key(iface):
        name_lower = iface['name'].lower()
        is_wlan = any(name_lower.startswith(prefix) for prefix in wlan_names)
        return (1, '') if is_wlan else (0, iface['name'])

    all_interfaces.sort(key=_sort_key)
    return all_interfaces


def _extract_ips_from_interface(iface_dict: Dict, family: Optional[AddressFamily]) -> List[str]:
    """从单个接口字典中提取指定family的IP地址列表"""
    ips = []
    if family in (None, AddressFamily.IPV4) and 'ipv4' in iface_dict:
        ips.extend(addr['address'] for addr in iface_dict['ipv4'])
    if family in (None, AddressFamily.IPV6) and 'ipv6' in iface_dict:
        ips.extend(addr['address'] for addr in iface_dict['ipv6'])
    if family == AddressFamily.MAC and 'mac' in iface_dict:
        ips.extend(addr['address'] for addr in iface_dict['mac'])
    return ips


def _collect_all_ips(
        all_interfaces: List[Dict],
        family: Optional[AddressFamily],
        include_mac: bool,
        include_wildcard: bool
) -> List[str]:
    """收集所有IP地址（用于details=False且index=None时）"""
    all_ips = []

    if include_wildcard:
        if family in (None, AddressFamily.IPV4):
            all_ips.append('0.0.0.0')
        if family in (None, AddressFamily.IPV6):
            all_ips.append('::')

    if family == AddressFamily.IPV4:
        keys = ['ipv4']
    elif family == AddressFamily.IPV6:
        keys = ['ipv6']
    elif family == AddressFamily.MAC:
        keys = ['mac']
    else:
        keys = ['ipv4', 'ipv6']
        if include_mac:
            keys.append('mac')

    for iface in all_interfaces:
        for key in keys:
            if key in iface:
                all_ips.extend(addr['address'] for addr in iface[key])
    return all_ips


# ---------- 主函数 ----------
@lru_cache
def getip(
        index: Optional[int] = None,
        details: bool = False,
        family: Optional[AddressFamily] = None,
        ignore_loopback: bool = False,
        ignore_link_local: bool = False,
        include_mac: bool = False,
        include_wildcard: bool = True,
        wlan_names: Optional[List[str]] = None
) -> Union[List[Dict[str, Any]], Dict[str, Any], List[str], str]:
    """
    获取本机网络接口的IP地址信息，按接口名称合并。

    处理IPv6地址时自动去除 `%` 之后的作用域标识（如 `fe80::1%eth0` → `fe80::1`）。

    :param index: 如果指定，则返回地址列表中指定索引的单个结果
    :param details: 为True时返回包含详细信息的字典列表；为False时仅返回IP地址字符串
    :param family: 过滤地址族，可选 AddressFamily.IPV4, AddressFamily.IPV6, AddressFamily.MAC
    :param ignore_loopback: 为True时过滤掉环回地址（127.0.0.1, ::1）
    :param ignore_link_local: 为True时过滤掉链路本地地址（169.254.x.x, fe80::/10）
    :param include_mac: 为True时包含mac地址信息
    :param include_wildcard: 为True且details=False时，在最终IP列表中添加通配地址（0.0.0.0和::）
    :param wlan_names: 视为无线接口的名称前缀列表（用于排序放最后）。默认从环境变量
                       GETIP_WLAN_NAMES 读取（逗号分隔），若未设置则使用 ('wlan',)
    :return: 根据参数返回字典列表、单个字典、IP字符串列表或单个IP字符串
    :raises TypeError: 当index参数类型错误时
    :raises ValueError: 当family参数不合法时
    :raises IndexError: 当index超出地址列表范围时
    """
    # 1. 参数验证
    socket_family, force_include_mac = _validate_params(index, family, include_mac)
    wlan_prefixes = _get_wlan_names(wlan_names)

    # 2. 构建接口字典
    interface_dict = _build_interface_dict(
        socket_family,
        ignore_loopback,
        ignore_link_local,
        force_include_mac
    )

    # 3. 过滤空接口并排序
    all_interfaces = _filter_and_sort_interfaces(
        interface_dict,
        socket_family,
        force_include_mac,
        wlan_prefixes
    )

    # 4. 根据参数返回结果
    if index is not None:
        if index >= len(all_interfaces):
            raise IndexError(f"索引 {index} 超出范围，列表共有 {len(all_interfaces)} 个接口")
        result = all_interfaces[index]

        if not details:
            ips = _extract_ips_from_interface(result, family)
            return ips[0] if len(ips) == 1 else ips
        return result

    if details:
        return all_interfaces

    # 返回IP地址列表
    return _collect_all_ips(all_interfaces, family, force_include_mac, include_wildcard)


def get_server_urls(
        host: str,
        port: int,
        protocol: str = "http",
        include_ipv4: bool = False,
) -> List[str]:
    """
    根据绑定的主机地址和端口，返回所有可访问的 URL 列表。

    自动识别主机地址的地址族（ipv4/ipv6）和通配属性：
    - 若主机是通配地址（"0.0.0.0" 或 "::"），则返回对应地址族的所有有效 ip，
      包括环回地址和链路本地地址。
    - 若主机是 ipv6 通配地址（"::"）且 `include_ipv4=True`，则同时返回
      ipv4 和 ipv6 地址（即双栈模式下的所有可用地址）。
    - 否则仅返回主机地址本身对应的 URL。

    :param host: 绑定的主机地址（例如 "0.0.0.0", "::", "192.168.1.100", "::1"）
    :param port: 端口号
    :param protocol: 协议 ("http" 或 "https")
    :param include_ipv4: 当 host 为 "::" 时，是否同时返回 ipv4 地址
    :return: URL 字符串列表
    """
    # 分离作用域标识
    addr_part, _ = _strip_ip_scope(host)

    # 验证并获取地址信息
    try:
        ip = ip_address(addr_part)
    except ValueError:
        return []

    normalized = str(ip)
    host_type = AddressFamily.IPV4 if ip.version == 4 else AddressFamily.IPV6
    is_wildcard = normalized in ("0.0.0.0", "::")

    if is_wildcard:
        # 处理 IPv6 通配且要求包含 IPv4 的情况
        if host_type == AddressFamily.IPV6 and include_ipv4:
            # 获取所有 IP（包含 IPv4 和 IPv6）
            all_ips = getip(
                details=False,
                family=None,
                ignore_loopback=False,
                ignore_link_local=True,
                include_wildcard=False
            )
            urls = []
            for addr in all_ips:
                if ':' in addr:  # IPv6
                    urls.append(f"{protocol}://[{addr}]:{port}")
                else:             # IPv4
                    urls.append(f"{protocol}://{addr}:{port}")
            return urls
        else:
            # 仅获取对应地址族的 IP
            all_ips = getip(
                details=False,
                family=host_type,
                ignore_loopback=False,
                ignore_link_local=True,
                include_wildcard=False
            )
            if host_type == AddressFamily.IPV6:
                return [f"{protocol}://[{addr}]:{port}" for addr in all_ips]
            else:
                return [f"{protocol}://{addr}:{port}" for addr in all_ips]

    # 非通配地址：直接返回该地址的 URL
    if host_type == AddressFamily.IPV6:
        return [f"{protocol}://[{normalized}]:{port}"]
    else:
        return [f"{protocol}://{normalized}:{port}"]
