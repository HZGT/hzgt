# -*- coding: utf-8 -*-
import subprocess
from functools import partial

subprocess.Popen = partial(subprocess.Popen, encoding='utf-8')  # 子进程设置全局编码改为 UTF-8, 且在 import execjs 前导入

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

import execjs

PRIVATEKEY = ("MIICeAIBADANBgkqhkiG9w0BAQEFAASCAmIwggJeAgEAAoGBANKpd+l3HQL/vu/T"
              "AYHLYkdgIG70ljrCElyDS77180IY3Fsp8UyNlRnqKT/ks4gNE8qxNv1lhkRRTZci"
              "MQg28+hjH2sfhAmq2gYqSziCe5GM7Um+JF6VI60M7dgmblABh3t+G+KUdK21lNID"
              "8rVJU6UJF+bwI3bQdFeJgpGfNs6LAgMBAAECgYEAm2WXpwjOxd+SIactfWliXfRy"
              "+GZES6PNl6Dix0L25tMf+b++2BG44xzwwMkcBkhfSS3gupuhp9OxwMLgGIcw8+wE"
              "fxJCpmoEC9F2uni0KvE2oEnNean1bR6rPeSf1xRMWVTRieJWIzyR0DhzHMQ9ii0n"
              "oPuhDWNsUl2YmRFrYYECQQD9OxLqLvtcBAZNMNAZeCCV7npCXdNrX1C4k5EZ9yMQ"
              "g26znefPDikdhuP4x067lPScUytrgCeuWNNp6HVer0QJAkEA1Pc43cI40NXMk0A3"
              "nGg0JTSE1mbpbIk6CT2zXyuUiiPgjsmP6TJ3cnOeQxI1ld3KwqvVNxpNNAScAY0G"
              "+aHq8wJBAOklYYXRWcXfQroBDifU7RN9rHy8C/JYoGZAHyEr49HJYLvoz0tYe0xf"
              "LDeZsQiN3SSsglaIeIBR8dwZlS5m6ZkCQQDIYIBJ7veETtW4asCoUkdWBk9CZ/wT"
              "Gh7YGQzPa/LL8yvTTYUxdkF7F5v+IYD3rIKdng30VbP0UK30q5u3f4jPAkAPs/yI"
              "3/Z3FkzrTxxPOZT4ZjjKIOxe4I7vVJVhtzV9ItwuA83WyuslJY758kFz6AxrhT8K"
              "F30CPO1sEazBH9xD")  # 解密密钥

PUBLICKEY = ("MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDSqXfpdx0C/77v0wGBy2JHYCBu"
             "9JY6whJcg0u+9fNCGNxbKfFMjZUZ6ik/5LOIDRPKsTb9ZYZEUU2XIjEINvPoYx9r"
             "H4QJqtoGKks4gnuRjO1JviRelSOtDO3YJm5QAYd7fhvilHSttZTSA/K1SVOlCRfm"
             "8CN20HRXiYKRnzbOiwIDAQAB")  # 加密密钥

# 以下内容为 ini-parser 库[版本 1.2.1 / MIT许可] 的内容
# The following is the content of the library called ini-parser [version 1.2.1 / MIT License].
# 详细内容可见: https://pypi.org/project/ini-parser/
# Details are available here: https://pypi.org/project/ini-parser/

# ===================================================== ini-parser =====================================================
import json
import os
import re


def _parse_value(value):
    if isinstance(value, int) or value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
        return int(value)

    if re.match(r'^\d*\.\d+$', value):
        return float(value)

    return value


def encode(obj, opt=None):
    children = []
    out = ''

    if isinstance(opt, str):
        opt = {
            'section': opt,
            'whitespace': True
        }
    else:
        opt = opt or {}
        opt['whitespace'] = opt.get('whitespace', True)

    separator = ' = ' if opt['whitespace'] else '='

    for k, v in obj.items():
        if v and isinstance(v, list):
            for item in v:
                out += safe(k + '[]') + separator + safe(item) + '\n'
        elif v and isinstance(v, dict):
            children.append(k)
        else:
            out += safe(k) + separator + safe(v) + '\n'

    if opt.get('section') and len(out):
        out = '[' + safe(opt['section']) + ']' + '\n' + out

    for k in children:
        nk = '.'.join(_dot_split(k))
        section = (opt['section'] + '.' if opt.get('section') else '') + nk
        child = encode(obj[k], {
            'section': section,
            'whitespace': opt['whitespace']
        })
        if len(out) and len(child):
            out += '\n'
        out += child

    return out


def _dot_split(string):
    return re.sub(r'\\\.', '\u0001', string).split('.')


EMPTY_KEY_SENTINEL = object()


def decode(string, on_empty_key=EMPTY_KEY_SENTINEL):
    out = {}
    p = out
    regex = re.compile(r'^\[([^]]*)]$|^([^=]+)(=(.*))?$', re.IGNORECASE)
    lines = re.split(r'[\r\n]+', string)

    for line in lines:
        if not line or re.match(r'^\s*[;#]', line):
            continue
        match = regex.match(line)
        if not match:
            continue
        if match[1]:
            section = unsafe(match[1])
            p = out[section] = out.get(section, {})
            continue
        key = unsafe(match[2])
        if match[3]:
            if match[4].strip():
                value = _parse_value(unsafe(match[4]))
            elif on_empty_key is EMPTY_KEY_SENTINEL:
                raise ValueError(key)
            else:
                value = on_empty_key
        else:
            value = True
        if value in ('true', 'True'):
            value = True
        elif value in ('false', 'False'):
            value = False
        elif value in ('null', 'None'):
            value = None

        # Convert keys with '[]' suffix to an array
        if len(key) > 2 and key[-2:] == '[]':
            key = key[:-2]
            if key not in p:
                p[key] = []
            elif not isinstance(p[key], list):
                p[key] = [p[key]]

        # safeguard against resetting a previously defined
        # array by accidentally forgetting the brackets
        if isinstance(p.get(key), list):
            p[key].append(value)
        else:
            p[key] = value

    # {a:{y:1},"a.b":{x:2}} --> {a:{y:1,b:{x:2}}}
    # use a filter to return the keys that have to be deleted.
    _out = dict(out)
    for k in _out.keys():
        if not out[k] or not isinstance(out[k], dict) or isinstance(out[k], list):
            continue
        # see if the parent section is also an object.
        # if so, add it to that, and mark this one for deletion
        parts = _dot_split(k)
        p = out
        l = parts.pop()
        nl = re.sub(r'\\\.', '.', l)
        for part in parts:
            if part not in p or not isinstance(p[part], dict):
                p[part] = {}
            p = p[part]
        if p == out and nl == l:
            continue
        p[nl] = out[k]
        del out[k]

    return out


def _is_quoted(val):
    return (val[0] == '"' and val[-1] == '"') or (val[0] == "'" and val[-1] == "'")


def safe(val):
    return json.dumps(val) if \
        (not isinstance(val, str) or
         re.match(r'[=\r\n]', val) or
         re.match(r'^\[', val) or
         (len(val) > 1 and _is_quoted(val)) or
         val != val.strip()) else \
        val.replace(';', '\\;').replace('#', '\\#')


def unsafe(val):
    val = (val or '').strip()
    if _is_quoted(val):
        # remove the single quotes before calling JSON.parse
        if val[0] == "'":
            val = val[1:-1]
        try:
            val = json.loads(val)
        except:
            pass
    else:
        # walk the val to find the first not-escaped ; character
        esc = False
        unesc = ''
        for i in range(len(val)):
            c = val[i]
            if esc:
                if c in '\\;#':
                    unesc += c
                else:
                    unesc += '\\' + c
                esc = False
            elif c in ';#':
                break
            elif c == '\\':
                esc = True
            else:
                unesc += c
        if esc:
            unesc += '\\'
        return unesc.strip()
    return val


parse = decode
stringify = encode


# 以上内容为 ini-parser 库[版本 1.2.1 / MIT许可] 的内容
# The above is the content of the library called ini-parser [version 1.2.1 / MIT License].
# ===================================================== ini-parser =====================================================
def readini(inifile: str, encoding: str = "utf-8") -> dict:
    """
    读取 ini 文件 返回字典

    :param inifile: ini 文件路径
    :param encoding: 编码 默认 utf-8
    :return: dict ini 对应嵌套字典
    """
    return parse(open(inifile, encoding=encoding).read())


def saveini(savename: str, iniconfig: dict, section_prefix: str = "",
            bool_space: bool = True, encoding="utf-8") -> None:
    """
    保存嵌套字典为ini文件

    :param savename: 保存文件名 可不包含后缀名 .ini
    :param iniconfig: 嵌套字典
    :param section_prefix: ini文件的 section 部分前缀 默认为空[即不添加前缀]
    :param bool_space: 等号前后是否添加空格 默认为 True[即默认添加空格]
    :param encoding: 编码 默认 utf-8
    :return: None
    """
    file_name, extension = os.path.splitext(savename)
    if ".ini" != extension:
        savename = savename + ".ini"

    with open(savename, "w+", encoding=encoding) as fp:
        fp.write(stringify(iniconfig,
                           {"section": section_prefix,  # 各项前缀
                            "whitespace": bool_space  # 等号两边是否添加空格
                            }))


# ======================================================================================================================
def getbyjs(js_path_or_script: str, funcname: str, *args, encoding: str = 'utf - 8'):
    """
    返回 js文件 或 js文本字符串 的函数运算结果
    :param js_path_or_script: js文件路径 或 js文本字符串
    :param funcname: js函数名
    :param encoding: 编码方式 默认 UTF - 8
    :return: js函数执行后的返回结果
    """
    try:
        with open(js_path_or_script, 'r', encoding=encoding) as f:
            res = f.read()
    except:
        res = js_path_or_script

    if not res or funcname:
        raise ValueError("js字符串为空 或 js函数名 funcname 参数无效")

    ctx = execjs.compile(res)  # 加载JS文件
    return ctx.call(funcname, *args)  # 执行函数并返回结果


def decrypt_rsa(text: str, keyt: str = PRIVATEKEY):
    """
    RSA解密

    :param text: 待解密字符串
    :param keyt: 解密密钥
    """
    return getbyjs("rsa.js", 'decryptRSA', text, keyt)


def encrypt_rsa(text: str, keyr: str = PUBLICKEY):
    """
    RSA加密

    :param text: 待加密字符串
    :param keyr: 加密密钥
    """
    return getbyjs("rsa.js", 'encryptRSA', text, keyr)


def ende_dict(nested_dict: dict, endefunc=None, args: tuple = None, options: list = None):
    """
    对字典的值进行加解密


    >>> from hzgt.tools import ende_dict, PUBLICKEY, PRIVATEKEY, encrypt_rsa, decrypt_rsa
    >>>
    >>> my_dict = {  # 待加密的嵌套字典
    >>>     "key1": "value1",
    >>>     "key2": {
    >>>         "subkey1": "subkey1_value",
    >>>         "subkey2": "subkey2_value",
    >>>         "uky": {
    >>>             "sub1": "sub1_value",
    >>>             "sub2": {
    >>>                 "subsubkey1": "subsubkey1_value",
    >>>                 "subsubkey2": "subsubkey2_value"
    >>>             }
    >>>         }
    >>>     },
    >>>     "key3": "value3"
    >>> }
    >>> print(my_dict)
    >>> options = [["key1"], ["key2", "subkey1", ["uky", ["sub2", "subsubkey2"]]]]  # 待加密的值对应的键
    >>> enresult = ende_dict(my_dict, endefunc=encrypt_rsa, args=(PUBLICKEY,), options=options)  # 通过加密函数以及参数进行加密
    >>> print(enresult)
    >>>
    >>> deresult = ende_dict(enresult, endefunc=decrypt_rsa, args=(PRIVATEKEY,), options=options)  # 解密
    >>> print(deresult)

    # OUTPUT:

    # {
    'key1': 'value1',
    'key2': {
        'subkey1': 'subkey1_value',
        'subkey2': 'subkey2_value',
        'uky': {
            'sub1': 'sub1_value',
            'sub2': {
                'subsubkey1': 'subsubkey1_value',
                'subsubkey2': 'subsubkey2_value'
                }
            }
        },
    'key3': 'value3'
    }  # 待加密的字典

    # {
    'key1': 'RhUwMRsG64eLbYbOs87+gBOF8YKTFm9HlRhD9zEo3+vaaEY0eicQzC0q4LGPphhKdh3FWEBDh4S4EgGGt4DFBxKDQ/8U198gHKtkoZ96LV8cCP6CZ/UQHPCcyiXSdhkM2flKeeCgosqhcQIojgvJDsA/BCRPEONUKpyf1/y4Kbs=', '
    key2': {
        'subkey1': 'GLqQdzPfGP80zVWNqgQTLegKi5vJ6dXsXn5Qt1Y0Skdf4QM4FG3nKRr0AhHilXlF0X7USYwD3M/E+pYKHXDCnO8V64D9RnJa+HI4tXPwCygNChPmfIHXyw9+OA9Oq/NTaO9x1EcHXeXbAZpI1p7/BbLSVFuk48TjrwJHf5rbois=',
        'subkey2': 'subkey2_value',
        'uky': {
            'sub1': 'sub1_value',
            'sub2': {
                'subsubkey1': 'subsubkey1_value',
                'subsubkey2': 'qvZIVNFlSivsSJQIbHG3FFrMlvj9tgls/PhDnaUMhyREHaVTi3LGGFjIO5ji+YDx5YWCpUG+/l6iUS4Qr3C7wMdn2oDvBzZ5chpswnsO/7x9fAODTbw1n+ebHHEMYANZCsUhDiEPs6FYg7NkpXioGGOWmRBZVyxXKPeOVMHIN3I='
                }
            }
        },
    'key3': 'value3'
    }  # 对给出的键对应的值进行加密

    # {
    'key1': 'value1',
    'key2': {
        'subkey1': 'subkey1_value',
        'subkey2': 'subkey2_value',
        'uky': {
            'sub1': 'sub1_value',
            'sub2': {
                'subsubkey1': 'subsubkey1_value',
                'subsubkey2': 'subsubkey2_value'
            }
        }
    },
    'key3': 'value3'
    }  # 解密

    :param nested_dict: dict 字典
    :param endefunc: 加解密函数 如果为 None 则使用默认的加解密函数 该函数的第一个参数一定是待加密的文本
    :param args: tuple 加解密函数的参数 忽略第一个参数（待加密的文本） 详细可参照 encrypt_rsa() / decrypt_rsa()
    :param options: 加解密的键选项, 对选项中的键对应的值进行加密
    :return: 返回加解密后的字典
    """
    if endefunc is None:
        def endefunc(s, *args):
            return s[::-1]

    def match_key(key, option):
        if isinstance(option, list):
            for sub_option in option:
                if match_key(key, sub_option):
                    return True
            return False
        return key == option

    encrypted_dict = {}
    for key, value in nested_dict.items():
        if options is not None:
            should_encrypt = False
            for sublist in options:
                for item in sublist:
                    if match_key(key, item):
                        should_encrypt = True
                        break
                if should_encrypt:
                    break
        else:
            should_encrypt = True

        if not should_encrypt:
            encrypted_value = value
        else:
            if isinstance(value, dict):
                encrypted_value = ende_dict(value, endefunc, args, options)
            else:
                if args:
                    encrypted_value = endefunc(value, *args)
                else:
                    encrypted_value = endefunc(value)
        encrypted_dict[key] = encrypted_value
    return encrypted_dict


# ======================================================================================================================
class RSAEncryptor:
    """
    RSA 加解密器
    """

    def __init__(self, private_key: RSAPrivateKey = None, public_key: RSAPublicKey = None,
                 private_pem_path: str = None, public_pem_path: str = None,
                 private_pem_str: str = None, public_pem_str: str = None):
        """
        初始化 RSA 加解密器
        :param private_key: 私钥对象
        :param public_key: 公钥对象
        :param private_pem_path: 私钥文件路径
        :param public_pem_path: 公钥文件路径
        :param private_pem_str: 私钥字符串
        :param public_pem_str: 公钥字符串
        """
        self.private_key = private_key
        self.public_key = public_key

        # 优先级：对象 > 字符串 > 文件路径

        # 如果提供了私钥对象，则不处理其他输入
        if private_key is None:
            # 如果提供了私钥字符串，则加载私钥
            if private_pem_str:
                pem_str = self.__ensure_pem_format(private_pem_str, is_private=True)
                self.private_key = serialization.load_pem_private_key(
                    pem_str.encode(),
                    password=None
                )
            elif private_pem_path:
                with open(private_pem_path, "rb") as f:
                    self.private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None
                    )

        # 如果提供了公钥对象，则不处理其他输入
        if public_key is None:
            # 如果提供了公钥字符串，则加载公钥
            if public_pem_str:
                pem_str = self.__ensure_pem_format(public_pem_str, is_private=False)
                self.public_key = serialization.load_pem_public_key(
                    pem_str.encode()
                )
            elif public_pem_path:
                with open(public_pem_path, "rb") as f:
                    self.public_key = serialization.load_pem_public_key(f.read())

        # 如果只提供了私钥，自动提取公钥
        if self.private_key and not self.public_key:
            self.public_key = self.private_key.public_key()

        # 如果两者都没有提供，抛出异常
        if self.private_key is None and self.public_key is None:
            raise ValueError("必须提供至少一个密钥、文件路径或 PEM 字符串")

    @staticmethod
    def __ensure_pem_format(key_data: str, is_private: bool = False) -> str:
        """确保字符串具有正确的 PEM 格式"""
        if "-----BEGIN" in key_data:
            return key_data  # 已经是完整 PEM 格式，直接返回

        if is_private:
            header = "-----BEGIN PRIVATE KEY-----"
            footer = "-----END PRIVATE KEY-----"
        else:
            header = "-----BEGIN PUBLIC KEY-----"
            footer = "-----END PUBLIC KEY-----"

        # 去除空白并插入换行
        return f"{header}\n{key_data.strip()}\n{footer}"

    def generate_keys(self):
        """生成 RSA 公钥和私钥"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        return self.public_key, self.private_key

    def save_as_pem(self, private_key_file_path: str = "private.pem", public_key_file_path: str = "public.pem"):
        """将公钥保存为 PEM 格式的文件"""
        if self.private_key is None:
            raise ValueError("Private key not set or generated.")
        if self.public_key is None:
            raise ValueError("Public key not set or generated.")

        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        with open(private_key_file_path, "wb") as f:
            f.write(private_pem)

        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        with open(public_key_file_path, "wb") as f:
            f.write(public_pem)

    def get_private_key_pem(self):
        """获取 PEM 格式的私钥"""
        if self.private_key is None:
            raise ValueError("Private key not generated yet.")
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

    def get_public_key_pem(self):
        """获取 PEM 格式的公钥"""
        if self.public_key is None:
            raise ValueError("Public key not generated yet.")
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def encrypt(self, data):
        """使用公钥加密数据"""
        if self.public_key is None:
            raise ValueError("Public key not set or generated.")
        return self.public_key.encrypt(
            data.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def decrypt(self, encrypted_data):
        """使用私钥解密数据"""
        if self.private_key is None:
            raise ValueError("Private key not set or generated.")
        return self.private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        ).decode()


# 示例用法
if __name__ == "__main__":
    encryptor = RSAEncryptor(private_pem_str=PRIVATEKEY, public_pem_str=PUBLICKEY)

    # 生成密钥
    encryptor.generate_keys()

    # 打印密钥（PEM 格式）
    print("Public Key:\n", encryptor.get_public_key_pem().decode())
    print("Private Key:\n", encryptor.get_private_key_pem().decode())

    # 加密和解密示例
    original_data = "Hello, this is a secret message!"
    encrypted = encryptor.encrypt(original_data)
    print("Encrypted Data:", encrypted)

    decrypted = encryptor.decrypt(encrypted)
    print("Decrypted Data:", decrypted)
