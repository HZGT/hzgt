# strop.py 文档

## 导航目录

- [pic()](#pic)
- [restrop()](#restrop)

## 函数说明

### pic()

**功能**：输出变量名、变量类型和值，支持跨行调用，优化参数名称提取。

**参数**：
- `*args`：不定数量的参数
- `bool_header`：是否显示列名，默认为 False
- `bool_show`：是否直接打印，默认为 True

**返回值**：`list[tuple[Any, str, Any]]` - 包含（变量名, 变量类型, 值）的列表

**使用示例**：
```python
from hzgt import pic

name = "Alice"
age = 30
pic(name, age, bool_header=True)
# 输出：
# Name  | Type | Value
# -------------------
# name  | str  | Alice
# age   | int  | 30
```

### restrop()

**功能**：返回带有颜色配置的字符串，支持多种显示模式和颜色设置。

**参数**：
- `text`：要添加颜色的字符串
- `m`：模式，默认为 0（默认模式）
  - 0: 默认
  - 1: 粗体高亮
  - 2: 暗色弱化
  - 3: 斜体（部分终端支持）
  - 4: 下滑线
  - 5: 缓慢闪烁（未广泛支持，shell有效）
  - 6: 快速闪烁（未广泛支持，shell有效）
  - 7: 反色
  - 8: 前景隐藏文本（未广泛支持，shell有效）
  - 9: 删除线
  - 21: 双下划线（部分终端支持）
  - 52: 外边框 [颜色随字体颜色变化]（部分终端支持）
  - 53: 上划线（部分终端支持）
- `f`：字体颜色，默认为 1（红色）
  - 0: 黑
  - 1: 红
  - 2: 绿
  - 3: 黄
  - 4: 蓝
  - 5: 紫
  - 6: 青
  - 7: 灰
  - 8: 设置颜色功能
  - 9: 默认
- `b`：背景颜色，默认为 0（黑色）
- `frgb`：RGB颜色数组，用于RGB字体颜色显示，如果frgb有值，则优先使用frgb
- `brgb`：RGB颜色数组，用于RGB背景颜色显示，如果brgb有值，则优先使用brgb

**返回值**：`str` - 带有颜色配置的字符串

**使用示例**：
```python
from hzgt import restrop

# 红色文本
print(restrop("Hello World", f=1))

# 绿色文本，黄色背景
print(restrop("Hello World", f=2, b=3))

# 使用RGB颜色
print(restrop("Hello World", frgb=(255, 100, 100)))
```