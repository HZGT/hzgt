# -*- coding: utf-8 -*-

import sys
import locale
import getpass

import logging

CURRENT_SYSTEM_DEFAULT_ENCODING: str = sys.getdefaultencoding()  # 当前系统所使用的默认字符编码
DEFAULT_ENCODING: str = locale.getpreferredencoding()  # 获取用户设定的系统默认编码

PLATFORM: str = sys.platform  # 获取操作系统类型
CURRENT_USERNAME: str = getpass.getuser()  # 获取当前用户名
PYTHON_VERSION: tuple = sys.version_info[:3]  # 获取python的版本

LOG_LEVEL: dict = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

STYLE: dict[str, dict[int, int]] = {
    'mode': {  # 显示模式
        0: 0,  # 默认设置
        1: 1,  # 粗体高亮
        2: 2,  # 弱化
        3: 3,  # 斜体
        4: 4,  # 下划线
        5: 5,  # 闪烁
        6: 6,  # 闪烁
        7: 7,  # 反白显示
        8: 8,  # 前景隐藏
        9: 9,  # 删除线
        21: 21,  # 双下划线
        52: 52,  # 外边框
        53: 53,  # 上划线
    },

    'fore': {  # 前景色
        0: 30,  # 黑色
        1: 31,  # 红色
        2: 32,  # 绿色
        3: 33,  # 黄色
        4: 34,  # 蓝色
        5: 35,  # 紫红色
        6: 36,  # 青蓝色
        7: 37,  # 灰白色
        8: 38,  # 设置颜色模式
        9: 39,  # 默认字体颜色
    },

    'back': {  # 背景
        0: 40,  # 黑色
        1: 41,  # 红色
        2: 42,  # 绿色
        3: 43,  # 黄色
        4: 44,  # 蓝色
        5: 45,  # 紫红色
        6: 46,  # 青蓝色
        7: 47,  # 灰白色
        8: 48,  # 设置颜色模式
        9: 49,  # 默认字体颜色
        },

    'end':
        {
            0: 0,
        },
}
