# fileop.py 文档

## 导航目录

- [bitconv()](#bitconv)
- [getfsize()](#getfsize)
- [ensure_file()](#ensure_file)
- [generate_filename()](#generate_filename)

## 函数说明

### bitconv()

**功能**：字节单位转换，将字节大小转换为更易读的单位（如KB、MB、GB等）。

**参数**：
- `fsize`：大小（字节）

**返回值**：`tuple` - 包含转换后的大小（保留两位小数）和单位

**使用示例**：
```python
from hzgt import bitconv

print(bitconv(1024))      # 输出：(1.0, 'KB')
print(bitconv(1048576))   # 输出：(1.0, 'MB')
```

### getfsize()

**功能**：获取目录、文件或URL指向的资源的总大小，并进行单位转换。

**参数**：
- `filepath`：目录路径、文件路径或URL
- `timeout`：URL文件请求超时时间，默认为5秒

**返回值**：`tuple` - 转换后的大小和单位元组，如(6.66, 'MB')。失败时报错

**使用示例**：
```python
from hzgt import getfsize

# 获取本地文件大小
print(getfsize("example.txt"))

# 获取目录大小
print(getfsize("/path/to/directory"))

# 获取URL资源大小
print(getfsize("https://example.com/file.zip"))
```

### ensure_file()

**功能**：确保文件及其目录存在。如果目录或文件不存在，则创建它们。增强对Windows系统同名文件冲突的处理。

**参数**：
- `file_path`：文件路径

**返回值**：`None`

**使用示例**：
```python
from hzgt import ensure_file

# 确保文件及其目录存在
ensure_file("/path/to/new/directory/file.txt")
```

### generate_filename()

**功能**：生成文件名，避免双重扩展，支持自定义后缀。

**参数**：
- `name`：基础名称（当 fname 未提供时使用）
- `fname`：可选的自定义文件名
- `suffix`：期望的文件后缀（必须以点开头，默认为 .log）

**返回值**：`str` - 正确的文件名（确保以指定的 suffix 结尾）

**使用示例**：
```python
from hzgt import generate_filename

# 使用基础名称生成文件名
print(generate_filename("test"))          # 输出：test.log

# 使用自定义文件名
print(generate_filename("test", "data.txt"))  # 输出：data.log

# 使用自定义后缀
print(generate_filename("test", suffix=".csv"))  # 输出：test.csv
```
