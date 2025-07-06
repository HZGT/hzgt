# -*- coding: utf-8 -*-

import inspect
import linecache
import re

from hzgt.core.CONST import STYLE
from hzgt.core.Decorator import vargs


def pic(*args, bool_header=False, bool_show=True):
    """
    输出 变量名 | 变量类型 | 值
    支持跨行调用，优化参数名称提取

    :param args: 不定数量
    :param bool_header: 是否显示列名
    :param bool_show: 是否直接打印
    :return: list[tuple[Any, str, Any]] (变量名, 变量类型, 值) 不定数量
    """

    def extract_arguments():
        stacks = inspect.stack()
        caller_frame = stacks[2].frame
        filename = caller_frame.f_code.co_filename
        lineno = caller_frame.f_lineno

        # 获取多行代码上下文
        lines = linecache.getlines(filename)
        start_line = max(0, lineno - 3)
        end_line = min(len(lines), lineno + 3)
        context = ''.join(lines[start_line:end_line])

        # 定位函数调用起始位置
        pattern = re.compile(rf'pic\s*\(', re.DOTALL)
        match = pattern.search(context)
        if not match:
            return [f'arg{i}' for i in range(len(args))]

        start_pos = match.end()
        # 括号匹配提取参数部分
        stack = []
        args_str = ""
        for char in context[start_pos:]:
            if char == '(' or char == '[' or char == '{':
                stack.append(char)
            elif char == ')' or char == ']' or char == '}':
                if stack:
                    stack.pop()
                if not stack and char == ')':
                    break
            args_str += char

        # 优化参数分割：按逗号分割但考虑括号嵌套
        stack = []
        arguments = []
        current_arg = []
        for char in args_str:
            if char in '([{':
                stack.append(char)
                current_arg.append(char)
            elif char in ')]}':
                if stack:
                    stack.pop()
                current_arg.append(char)
            elif char == ',' and not stack:
                arguments.append(''.join(current_arg).strip())
                current_arg = []
            else:
                current_arg.append(char)

        if current_arg:
            arguments.append(''.join(current_arg).strip())

        return arguments

    try:
        strvns = extract_arguments()
        # 清理参数名称：移除多余换行和空格
        strvns = [re.sub(r'\s+', ' ', name).strip() for name in strvns]
        if len(strvns) != len(args):
            strvns = [f'arg{i}' for i in range(len(args))]
    except Exception:
        strvns = [f'arg{i}' for i in range(len(args))]

    maxlenname = max(len(max(strvns, key=len, default='')), 4)
    typevns = [type(arg).__name__ for arg in args]
    maxlentype = max(len(max(typevns, key=len, default='')), 4)

    _temp_list = []
    for name, arg in zip(strvns, args):
        type_name = type(arg).__name__
        _temp_list.append((name, type_name, arg))

        if not bool_show:
            continue

        if bool_header:
            header = (
                f"{'Name'.ljust(maxlenname)} | "
                f"{'Type'.ljust(maxlentype)} | "
                f"Value"
            )
            print(header)
            print('-' * (maxlenname + maxlentype + 15))
            bool_header = False

        value_str = str(arg)
        if '\n' in value_str:
            value_str = value_str.replace('\n', '\\n')

        row = (
            f"{name.ljust(maxlenname)} | "
            f"{type_name.ljust(maxlentype)} | "
            f"{value_str}"
        )
        print(row)

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
    :param frgb: RGB颜色数组, 用于RGB字体颜色显示, 如果frgb有值, 则优先使用frgb
    :param brgb: RGB颜色数组, 用于RGB字体颜色显示, 如果brgb有值, 则优先使用brgb
    :return: str 颜色配置后的字符串

    """
    try:
        # 处理模式
        str_mode = f"{STYLE['mode'][m]}" if STYLE['mode'].get(m) else ''

        # 处理前景色：优先使用 frgb
        if frgb is not None:
            if not is_valid_rgb_tuple(frgb):
                raise ValueError(f"`frgb={frgb}` 颜色参数无效")
            str_fore = f'38;2;{frgb[0]};{frgb[1]};{frgb[2]}'
        else:
            # 使用预设前景色
            str_fore = f"{STYLE['fore'][f]}" if STYLE['fore'].get(f) else ''

        # 处理背景色：优先使用 brgb
        if brgb is not None:
            if not is_valid_rgb_tuple(brgb):
                raise ValueError(f"`brgb={brgb}` 颜色参数无效")
            str_back = f'48;2;{brgb[0]};{brgb[1]};{brgb[2]}'
        else:
            # 使用预设背景色
            str_back = f"{STYLE['back'][b]}" if STYLE['back'].get(b) else ''

    except ValueError as err:
        raise ValueError(err) from None
    except Exception as err:
        raise RuntimeError(f"配置颜色时出错: {err}") from None

    # 组装样式
    style_parts = [s for s in [str_mode, str_fore, str_back] if s]
    style_code = ';'.join(style_parts)

    # 创建 ANSI 转义序列
    start_seq = f'\033[{style_code}m' if style_code else ''
    end_seq = f'\033[{STYLE["end"][0]}m' if start_seq else ''

    return f'{start_seq}{text}{end_seq}'
