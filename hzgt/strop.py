# -*- coding: utf-8 -*-

import inspect

from .CONST import STYLE
from .Decorator import vargs


def pic(*args, bool_header=False, bool_show=True):
    """
    输出 变量名 | 变量类型 | 值

    不建议多行 否则将导致变量匹配不完全

    :param args: 不定数量
    :param bool_header: 是否显示列名
    :param bool_show: 是否直接打印
    :return: list[tuple[Any, str, Any]] (变量名, 变量类型, 值) 不定数量
    """

    def match_nested(input_str):
        stack = []
        result = []
        current = ''
        for char in input_str:
            if char in '([{':
                if not stack:  # 如果stack为空，表示我们开始了一个新的结构
                    if current:  # 如果当前有非结构内容，先保存
                        result.append(current)
                        current = ''
                stack.append(char)
                current += char
            elif char in ')]}':
                current += char
                stack.pop()
                if not stack:  # 结构结束，保存
                    result.append(current)
                    current = ''
            else:
                current += char
        if current:  # 处理最后一个元素
            result.append(current)
        return [item.strip(', ') for item in result if item.strip(', ')]

    def RetrieveName(var):  # 获取变量名称
        stacks = inspect.stack()  # 获取函数调用链
        callFunc = stacks[1].function  # 获取最顶层的函数名
        code = stacks[2].code_context[0]
        startIndex = code.index(callFunc)
        startIndex = code.index("(", startIndex + len(callFunc)) + 1
        return match_nested(code[startIndex:-2].strip()), var

    strvns, vars = RetrieveName(args)  # 获取变量名列表以及对应的值

    maxlenname = max(len(max(strvns, key=len, default='')), 4)  # 获取变量名称长度最大值
    typevns = [str(type(var).__name__) for var in args]
    maxlentype = max(len(max(typevns, key=len, default='')), 4)  # 获取类型名称长度最大值

    _temp_list = []
    for str_vn, var in zip(strvns, vars):
        _stn = str(type(var).__name__)
        _temp_list.append((str_vn, _stn, var))
        if bool_show:
            if bool_header:
                print(f"{reputstr('Name', length=maxlenname)} \t|\t "
                      f"{reputstr('Type', length=maxlentype)} \t|\t "
                      f"Value")
                bool_header = False
            print(restrop(reputstr(str_vn, length=maxlenname)), '\t|\t',
                  restrop(reputstr(_stn, length=maxlentype), f=5), '\t|\t',
                  restrop(var, f=3))
    return _temp_list


def is_valid_rgb_tuple(t):
    """
    判断 t 是否为 RGB 元组
    """
    # 检查输入是否为RGB元组
    if not isinstance(t, tuple):
        return False
    # 检查元组长度是否为3
    if len(t) != 3:
        return False
    # 遍历每个元素进行检查
    for num in t:
        # 检查元素类型是否为整数（严格检查，排除布尔值）
        if type(num) is not int:
            return False
        # 检查数值范围是否在0~255之间
        if num < 0 or num > 255:
            return False
    return True


@vargs({"m": set(STYLE["mode"].keys()), "f": set(STYLE["fore"].keys()), "b": set(STYLE["back"].keys())})
def restrop(text, m: int = 0, f: int = 1, b: int = 0,
            frgb: tuple[int, int, int] = None, brgb: tuple[int, int, int] = None):
    """
    返回 颜色配置后的字符串.

    当 `f` = 8 时, `frgb` 参数可用, 传入 RGB 颜色元组, 将配置RGB前景颜色

    当 `b` = 8 时, `brgb` 参数可用, 传入 RGB 颜色元组, 将配置RGB背景颜色

    m mode 模式
        * 0  - 默认
        * 1  - 粗体高亮
        * 2  - 暗色弱化
        * 3  - 斜体 (部分终端支持)
        * 4  - 下滑线
        * 5  - 缓慢闪烁 (未广泛支持，shell有效)
        * 6  - 快速闪烁 (未广泛支持，shell有效)
        * 7  - 反色
        * 8  - 前景隐藏文本 (未广泛支持，shell有效)
        * 9  - 删除线
        * 21 - 双下划线 (部分终端支持)
        * 52 - 外边框 [颜色随字体颜色变化] (部分终端支持)
        * 53 - 上划线 (部分终端支持)

    f fore 字体颜色
    b back 背景颜色
        * 0  - 黑
        * 1  - 红
        * 2  - 绿
        * 3  - 黄
        * 4  - 蓝
        * 5  - 紫
        * 6  - 青
        * 7  - 灰
        * 8  - 设置颜色功能
        * 9  - 默认

    :param text: str
    :param m: mode 模式
    :param f: fore 字体颜色
    :param b: back 背景颜色
    :param frgb: RGB颜色数组, 当 f = 8 时有效, 用于RGB字体颜色显示
    :param brgb: RGB颜色数组, 当 b = 8 时有效, 用于RGB字体颜色显示
    :return: str 颜色配置后的字符串
    """
    try:
        str_mode = '%s' % STYLE['mode'][m] if STYLE['mode'][m] else ''

        if f == 8:
            if not is_valid_rgb_tuple(frgb):
                raise ValueError("`frgb` 不是有效的 RGB 颜色元组")
            str_fore = '38;2;%d;%d;%d' % (frgb[0], frgb[1], frgb[2])
        else:
            str_fore = '%s' % STYLE['fore'][f] if STYLE['fore'][f] else ''

        if b == 8:
            if not is_valid_rgb_tuple(brgb):
                raise ValueError("`brgb` 不是有效的 RGB 颜色元组")
            str_back = '48;2;%d;%d;%d' % (brgb[0], brgb[1], brgb[2])
        else:
            str_back = '%s' % STYLE['back'][b] if STYLE['back'][b] else ''

    except ValueError as err:
        raise Exception(str(err) + "  请检查 `frgb` `brgb`参数输入") from None
    except KeyError as err:
        raise Exception(str(err) + "  请检查 `m` `f` `b` 参数输入") from None
    except Exception as err:
        raise Exception(str(err) + "  请检查参数输入") from None

    style = ';'.join([s for s in [str_mode, str_fore, str_back] if s])
    style = '\033[%sm' % style if style else ''
    end = '\033[%sm' % STYLE['end'][0] if style else ''

    return '%s%s%s' % (style, text, end)


def reputstr(string, length=0):
    """
    文本对齐

    :param string: 字符串
    :param length: 对齐长度
    :return:
    """
    if length == 0:
        return string

    slen = len(string)
    re = string
    if isinstance(string, str):
        placeholder = ' '  # 半角
    else:
        placeholder = u'　'  # 全角
    while slen < length:
        re += placeholder
        slen += 1
    return re
