import os
import sys

# 版本
from .__version import __version__
version = __version__

# 字符串操作
from .strop import pic, restrop, restrop_list

# 字节单位转换
from .fileop import bit_conversion

# 获取文件大小
from .fileop import get_file_size

# 装饰器 gettime获取函数执行时间
from .Decorator import gettime, log_func, vargs

# 文件 / github仓库 / 视频 下载
from .download.download import downloadmain

# 日志
from .log import set_log

# from .tools import *

__all__ = [
    "version",
    "pic", "restrop", "restrop_list",
    "bit_conversion", "get_file_size",
    "gettime", "log_func", "vargs",
    "downloadmain",
    "set_log"
]

