# 版本
from .__version import __version__
version = __version__

# 字符串操作
from .strop import pic, restrop

# 字节单位转换
from .fileop import bit_conversion

# 获取文件大小
from .fileop import get_file_size

# 装饰器 gettime获取函数执行时间
from .Decorator import gettime, vargs

# 日志
from .log import set_log

# 自动配置类
from .AutoConfig import AutoConfig

__all__ = [
    "version",
    "pic", "restrop",
    "bit_conversion", "get_file_size",
    "gettime", "vargs",
    "set_log",
    "AutoConfig"
]

