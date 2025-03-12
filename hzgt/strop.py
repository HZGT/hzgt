# -*- coding: utf-8 -*-

import sys
import inspect

from .sc import SCError
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


@vargs({"m": {0, 1, 4, 5, 7, 8}, "f": {0, 1, 2, 3, 4, 5, 6, 7}, "b": {0, 1, 2, 3, 4, 5, 6, 7}})
def restrop(text, m='', f=1, b=''):
    """
    返回 颜色配置后的字符串

    mode 模式
        * 0  -  默认
        * 1  -  高亮
        * 4  -  下滑
        * 5  -  闪烁
        * 7  -  泛白
        * 8  -  隐藏

    fore 字体颜色 back 背景颜色
        * 0  -  黑
        * 1  -  红
        * 2  -  绿
        * 3  -  黄
        * 4  -  蓝
        * 5  -  紫
        * 6  -  青
        * 7  -  灰

    :param text: str
    :param m: mode 模式
    :param f: fore 字体颜色
    :param b: back 背景颜色
    :return: str
    """
    try:
        str_mode = '%s' % STYLE['mode'][m] if STYLE['mode'][m] else ''
        str_fore = '%s' % STYLE['fore'][f] if STYLE['fore'][f] else ''
        str_back = '%s' % STYLE['back'][b] if STYLE['back'][b] else ''
    except Exception as err:
        raise SCError(err, "请检查参数输入") from None

    style = ';'.join([s for s in [str_mode, str_fore, str_back] if s])
    style = '\033[%sm' % style if style else ''
    end = '\033[%sm' % STYLE['default']['end'] if style else ''

    return '%s%s%s' % (style, text, end)


def restrop_list(str_list: list, mfb_list: list):
    """
    返回 字符串列表进行颜色配置后的字符串\n
    (m, f, b)进行颜色配置\n
    ()表示不进行颜色配置

    + mode 模式简记
        * 0 默认
        * 1 高亮
        * 4 下滑
        * 5 闪烁
        * 7 泛白
        * 8 隐藏

    + fore back 颜色简记
        * 0 黑
        * 1 红
        * 2 绿
        * 3 黄
        * 4 蓝
        * 5 紫
        * 6 青
        * 7 灰

    args:
        from hzgt import restrop_list

        p = restrop_list(['欢迎', '来到', '我', '的世界'], [(0, 1, 0), (0, 2, 0), (0, 7, 0), (1, 2, 0)])

        print(p)

    :param str_list: 字符串列表
    :param mfb_list: 颜色配置列表
    :return: _str: 经过颜色配置后的字符串
    """
    _str = ''
    for s, mfb in zip(str_list, mfb_list):
        if mfb == () or mfb == -1:
            _str = _str + s
            continue
        if type(mfb) == int:
            _str = _str + restrop(s, f=mfb)
            continue
        _str = _str + restrop(s, m=mfb[0], f=mfb[1], b=mfb[2])
    if len(str_list) > len(mfb_list):
        _str = _str + ''.join(str_list[len(mfb_list):])
    return _str


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
