# ipss.py 文档

## 导航目录

- [getip()](#getip)
- [validate_ip()](#validate_ip)

## 函数说明

### getip()

**功能**：获取本机网络接口的IP地址信息，按接口名称合并，支持丰富的过滤和查询选项。

**参数**：
- `index`：如果指定，则返回地址列表中指定索引的单个结果
- `details`：为True时返回包含详细信息的字典列表；为False时仅返回IP地址字符串
- `family`：过滤地址族，可选 'ipv4', 'ipv6', 'mac'
- `ignore_local`：为True时过滤掉环回地址（127.0.0.1, ::1）和链路本地地址（fe80::）
- `include_mac`：为True时包含mac地址信息

**返回值**：根据参数返回字典列表、单个字典、IP字符串列表或单个IP字符串

**使用示例**：
```python
from hzgt import getip

# 获取所有网络接口的详细信息
interfaces = getip(details=True)
print(interfaces)

# 获取所有IP地址列表
all_ips = getip()
print(all_ips)

# 获取第一个网络接口的IPv4地址
first_ip = getip(index=0, family='ipv4')
print(first_ip)

# 获取所有IPv4地址，忽略本地地址
ipv4_ips = getip(family='ipv4', ignore_local=True)
print(ipv4_ips)

# 获取包含MAC地址的详细信息
interfaces_with_mac = getip(details=True, include_mac=True)
print(interfaces_with_mac)
```

### validate_ip()

**功能**：验证IP地址有效性并返回类型信息。

**参数**：
- `ip_str`：要验证的IP地址字符串

**返回值**：包含验证结果的字典，格式为：
```dict
{
    "valid": bool,       # IP是否有效
    "type": str or None,  # "ipv4"、"ipv6" 或 None(无效时)
    "normalized": str    # 标准化后的IP地址(有效时)
}
```

**使用示例**：
```python
from hzgt import validate_ip

# 验证IPv4地址
result1 = validate_ip("192.168.1.1")
print(result1)
# 输出：{"valid": true, "type": "ipv4", "normalized": "192.168.1.1"}

# 验证IPv6地址
result2 = validate_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
print(result2)
# 输出：{"valid": true, "type": "ipv6", "normalized": "2001:db8:85a3::8a2e:370:7334"}

# 验证无效IP
result3 = validate_ip("999.999.999.999")
print(result3)
# 输出：{"valid": false, "type": null, "normalized": ""}
```