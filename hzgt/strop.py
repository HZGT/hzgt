import sys

from .sc import SCError
from .CONST import STYLE


def getmidse(_string, start_string, end_string):
    """
    返回 所有在start_string和end_string之间的字符串组成的list

    :param _string: 字符串

    :param start_string: 起始字符串

    :param end_string: 结束字符串

    :returns: list
    """

    if _string == "":
        raise SCError("字符串为空...", "请填充字符串")
    if start_string == '' or end_string == '':
        raise SCError("分隔符为空...", "请填充分隔符")

    start_index = 0
    result = []
    while True:
        start_index = _string.find(start_string, start_index)
        if start_index == -1:
            break
        start_index += len(start_string)
        end_index = _string.find(end_string, start_index)
        if end_index == -1:
            break
        substring = _string[start_index:end_index]
        result.append(substring)
        start_index = end_index + len(end_string)
    return result


def perr(Err: Exception, ExtraMsg: str= '',Bool_Proceed: bool=True):
    """
    在try|except的except中使用

    简化报错,  默认--继续执行

    :param Bool_Proceed: 是否继续执行  [1继续执行 0退出程序]
    """

    except_type, except_value, except_traceback = sys.exc_info()
    except_file = except_traceback.tb_frame.f_code.co_filename
    except_line = except_traceback.tb_lineno

    errdict = {"报错-文件行数": f"{except_file}:{except_line}",
               "报错-类型信息": repr(except_type.__name__) + '  '+ repr(except_value)}
    if ExtraMsg:
        errdict["额外-信息提示"] = ExtraMsg
    for k, v in errdict.items():
        print(restrop(k, f=5), restrop(v))
    if not Bool_Proceed:
        exit()


def pic(*args):
    """
    输出 变量名 | 变量类型 | 值

    不建议直接使用常量，如"1, 2, 3", (1, 2, 3), [1, 2, 3]. 否则将导致变量名显示错误

    :param args: str "变量名" 不定数量
    """
    def RetrieveName(var): # 获取变量名称
        import inspect
        stacks = inspect.stack()  # 获取函数调用链
        try:
            callFunc = stacks[1].function  # 获取最顶层的函数名
            code = stacks[2].code_context[0]
            startIndex = code.index(callFunc)
            startIndex = code.index("(", startIndex + len(callFunc)) + 1
            return code[startIndex:-2].strip(), var
        except:
            return None

    str_vns, vars = RetrieveName(args)  # 获取变量名以及对应的值
    strvns = str_vns.replace(" ", '').split(",")
    lenname = max(len(max(strvns, key=len, default='')), 4)  # 获取变量名称长度最大值
    typevns = [str(type(var).__name__) for var in args]
    lentype = max(len(max(typevns, key=len, default='')), 4)  # 获取类型名称长度最大值

    try:
        print(f"{reputstr('Name', length=lenname)} \t|\t "
              f"{reputstr('Type', length=lentype)} \t|\t "
              f"Value")
        for str_vn, var in zip(strvns, vars):
            print(restrop(reputstr(str_vn, length=lenname)), '\t|\t',
                  restrop(reputstr(str(type(var).__name__), length=lentype), f=5), '\t|\t',
                  restrop(var, f=3))
    except Exception as err:
        raise SCError("变量未定义")


def restrop(text, m='', f=1, b=''):
    """
    返回 颜色配置后的字符串

    mode       模式简记
    ------------------------------
    0默认-1高亮-4下滑-5闪烁-7泛白-8隐藏

    fore back  颜色简记
    ------------------------------
    0黑-1红-2绿-3黄-4蓝-5紫-6青-7灰

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
        raise SCError(err, "请检查参数输入")

    style = ';'.join([s for s in [str_mode, str_fore, str_back] if s])
    style = '\033[%sm' % style if style else ''
    end = '\033[%sm' % STYLE['default']['end'] if style else ''

    return '%s%s%s' % (style, text, end)


def restrop_list(str_list: list, mfb_list: list):
    """
    返回 字符串列表进行颜色配置后的字符串

    ()表示不进行颜色配置

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
