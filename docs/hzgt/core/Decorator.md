# Decorator.py 文档

## 导航目录

- [dual_support()](#dual_support)
- [vargs()](#vargs)
- [gettime()](#gettime)

## 装饰器说明

### dual_support()

**功能**：通用适配器，使任何装饰器都支持两种调用方式：`@decorator` 和 `@decorator()`。

**参数**：
- `decorator_factory`：装饰器工厂函数

**返回值**：`function` - 增强后的装饰器函数

**使用示例**：
```python
from hzgt import dual_support

@dual_support
def my_decorator(param1=1, param2=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            print(f"Decorator called with params: {param1}, {param2}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 两种调用方式都支持
@my_decorator
def function1():
    pass

@my_decorator(param1=10, param2=20)
def function2():
    pass
```

### vargs()

**功能**：根据其有效集合验证函数参数。

**参数**：
- `valid_params`：字典，键为参数名称，值为有效值的集合或列表

**返回值**：`function` - 带参数验证的装饰器函数

**使用示例**：
```python
from hzgt import vargs

@vargs({'mode': {'read', 'write', 'append'}, 'type': {'text', 'binary'}})
def process_data(mode, type):
    print(f"Processing data in {mode} mode and {type} type")

# 正常执行
process_data(mode="read", type="text")

# 抛出ValueError
# process_data(mode='delete', type='binary')
```

### gettime()

**功能**：打印函数执行的时间，包括开始时间、结束时间和总耗时。

**参数**：
- `precision`：时间精度，范围为 0 到 9，默认为 6
- `date_format`：时间格式，默认为 '%Y-%m-%d %H:%M:%S.%f'

**返回值**：`function` - 带时间统计的装饰器函数

**使用示例**：
```python
from hzgt import gettime

# 无参数使用
@gettime
def slow_function():
    import time
    time.sleep(1)

# 带参数使用
@gettime(precision=3, date_format='%Y-%m-%d %H:%M:%S')
def another_slow_function():
    import time
    time.sleep(0.5)

# 调用函数
slow_function()
another_slow_function()

# 输出示例：
# 开始时间 2026-01-28 12:00:00.000000 module.slow_function
# 结束时间 2026-01-28 12:00:01.001234 module.slow_function 总耗时 1.001234 s
```