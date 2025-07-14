# 版本
from .__version import __version__
version = __version__

# 字符串操作
from hzgt.core import pic, restrop

# 字节单位转换
from hzgt.core import bitconv

# 获取文件大小
from hzgt.core import getfsize, ensure_file

# 装饰器 gettime获取函数执行时间
from hzgt.core import gettime, vargs

# 日志
from hzgt.core import set_log

# 自动配置类
from hzgt.core import AutoConfig


__all__ = [
    # sqlcore
    "version",
    "pic", "restrop",
    "bitconv", "getfsize", "ensure_file",
    "gettime", "vargs",
    "set_log",
    "AutoConfig",
]

