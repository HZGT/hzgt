import sys
import locale
import getpass


CURRENT_SYSTEM_DEFAULT_ENCODING = sys.getdefaultencoding()
# 当前系统所使用的默认字符编码
DEFAULT_ENCODING = locale.getpreferredencoding()
# 获取用户设定的系统默认编码

PLATFORM = sys.platform
# 获取操作系统类型
CURRENT_USERNAME = getpass.getuser()
# 获取当前用户名
PYTHON_VERSION = sys.version_info[:3]
# 获取python的版本

def INSTALLCMD(library: str):
    """
    返回需要安装包的cmd命令
    :param library: str 第三方库
    :return:
    """
    _cmd = ['pip', 'install', '']
    if PYTHON_VERSION[0] == 3 and 'linux' in PLATFORM:
        _cmd[0] = 'pip3'
    _cmd[2] = library
    return "%s %s %s" % (_cmd[0], _cmd[1], _cmd[2])


STYLE = {
    'mode':
        {  # 显示模式
            "": 0,

            'mormal': 0,  # 终端默认设置
            "0": 0,
            0: 0,

            'bold': 1,  # 高亮显示
            "1": 1,
            1: 1,

            'underline': 4,  # 使用下划线
            "4": 4,
            4: 4,

            'blink': 5,  # 闪烁
            "5": 5,
            5: 5,

            'invert': 7,  # 反白显示
            "7": 7,
            7: 7,

            'hide': 8,  # 不可见
            "8": 8,
            8: 8,
        },

    'fore':
        {  # 前景色
            '': '',  # 默认字体颜色

            'black': 30,  # 黑色
            "30": 30,
            0: 30,
            30: 30,

            'red': 31,  # 红色
            "31": 31,
            1: 31,
            31: 31,

            'green': 32,  # 绿色
            "32": 32,
            2: 32,
            32: 32,

            'yellow': 33,  # 黄色
            "33": 33,
            3: 33,
            33: 33,

            'blue': 34,  # 蓝色
            "34": 34,
            4: 34,
            34: 34,

            'purple': 35,  # 紫红色
            "35": 35,
            5: 35,
            35: 35,

            'cyan': 36,  # 青蓝色
            "36": 36,
            6: 36,
            36: 36,

            'white': 37,  # 灰白色
            '37': 37,
            7: 37,
            37: 37,
        },

    'back':
        {  # 背景
            '': 40,  # 默认背景黑色

            'black': 40,  # 黑色
            "40": 40,
            0: 40,
            40: 40,

            'red': 41,  # 红色
            "41": 41,
            1: 41,
            41: 41,

            'green': 42,  # 绿色
            "42": 42,
            2: 42,
            42: 42,

            'yellow': 43,  # 黄色
            "43": 43,
            3: 43,
            43: 43,

            'blue': 44,  # 蓝色
            "44": 44,
            4: 44,
            44: 44,

            'purple': 45,  # 紫红色
            "45": 45,
            5: 45,
            45: 45,

            'cyan': 46,  # 青蓝色
            "46": 46,
            6: 46,
            46: 46,

            'white': 47,  # 灰白色
            "47": 47,
            7: 47,
            47: 47,
        },

    'default':
        {
            'end': 0,
        },
}
