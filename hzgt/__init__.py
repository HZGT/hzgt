# 版本
from .__version import __version__
version = __version__

# 字符串操作
from hzgt.core import *


__all__ = [
    "version",
    "pic", "restrop",
    "bitconv", "getfsize", "ensure_file",
    "gettime", "vargs",
    "set_log",
    "AutoConfig",
]

