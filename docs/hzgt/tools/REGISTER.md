# Func_Register 和 Class_Register 类

## 功能说明
Func_Register 是一个函数注册器类，用于注册和管理函数。Class_Register 是一个类注册器类，用于注册和管理类。

## Func_Register 类

### 初始化方法

### `__init__(self, *args, **kwargs)`

**参数说明：**
- `*args` (tuple): 可变位置参数
- `**kwargs` (dict): 可变关键字参数

**返回值：**
- 无

**示例：**
```python
from hzgt.tools import Func_Register

# 创建函数注册器
func_reg = Func_Register()
```

### 主要方法

#### `__call__(self, target)`

**功能：** 使注册器可调用，用于装饰器语法

**参数说明：**
- `target` (callable or str): 函数对象或注册名

**返回值：**
- `callable`: 注册的函数对象

#### `register(self, target)`

**功能：** 将函数添加至注册器中

**参数说明：**
- `target` (callable or str): 函数对象或注册名

**返回值：**
- `callable`: 注册的函数对象

**示例：**
```python
# 方法1：直接注册函数
@func_reg
@func_reg.register
def hello():
    print("Hello")

# 方法2：指定注册名
@func_reg("greeting")
@func_reg.register("greeting")
def hello():
    print("Hello")
```

#### `__setitem__(self, key, value)`

**功能：** 设置注册项

**参数说明：**
- `key` (str): 注册名
- `value` (callable): 函数对象

**返回值：**
- 无

#### `__getitem__(self, key)`

**功能：** 获取注册的函数

**参数说明：**
- `key` (str): 注册名

**返回值：**
- `callable`: 注册的函数对象

#### `__contains__(self, key)`

**功能：** 检查注册名是否存在

**参数说明：**
- `key` (str): 注册名

**返回值：**
- `bool`: 注册名是否存在

#### `keys(self)`

**功能：** 获取所有注册名

**参数说明：**
- 无

**返回值：**
- `dict_keys`: 注册名集合

#### `values(self)`

**功能：** 获取所有注册的函数

**参数说明：**
- 无

**返回值：**
- `dict_values`: 函数对象集合

#### `items(self)`

**功能：** 获取所有注册项

**参数说明：**
- 无

**返回值：**
- `dict_items`: 注册项键值对集合

## Class_Register 类

### 初始化方法

### `__init__(self, registry_name, *args, **kwargs)`

**参数说明：**
- `registry_name` (str): 注册器名称
- `*args` (tuple): 可变位置参数
- `**kwargs` (dict): 可变关键字参数

**返回值：**
- 无

**示例：**
```python
from hzgt.tools import Class_Register

# 创建类注册器
class_reg = Class_Register("MyClassRegistry")
```

### 主要方法

#### `__setitem__(self, key, value)`

**功能：** 设置注册项

**参数说明：**
- `key` (str): 注册名
- `value` (callable): 类对象

**返回值：**
- 无

#### `__call__(self, target)`

**功能：** 使注册器可调用，用于装饰器语法

**参数说明：**
- `target` (callable or str): 类对象或注册名

**返回值：**
- `callable`: 注册的类对象

#### `register(self, target)`

**功能：** 注册类

**参数说明：**
- `target` (callable or str): 类对象或注册名

**返回值：**
- `callable`: 注册的类对象

**示例：**
```python
# 方法1：直接注册类
@class_reg
@class_reg.register
class MyClass:
    pass

# 方法2：指定注册名
@class_reg("MyClassAlias")
@class_reg.register("MyClassAlias")
class MyClass:
    pass
```

#### `__getitem__(self, key)`

**功能：** 获取注册的类

**参数说明：**
- `key` (str): 注册名

**返回值：**
- `callable`: 注册的类对象

#### `__contains__(self, key)`

**功能：** 检查注册名是否存在

**参数说明：**
- `key` (str): 注册名

**返回值：**
- `bool`: 注册名是否存在

#### `keys(self)`

**功能：** 获取所有注册名

**参数说明：**
- 无

**返回值：**
- `dict_keys`: 注册名集合

#### `items(self)`

**功能：** 获取所有注册项

**参数说明：**
- 无

**返回值：**
- `dict_items`: 注册项键值对集合