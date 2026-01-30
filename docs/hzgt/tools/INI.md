# INI.py 文档

## 导航目录

- [readini()](#readini)
- [saveini()](#saveini)

## 函数说明

### readini()

**功能**：读取 ini 文件并返回嵌套字典。

**参数**：
- `inifile`：ini 文件路径
- `encoding`：编码，默认 utf-8

**返回值**：`dict` - ini 文件对应的嵌套字典

**使用示例**：

```python
from hzgt.tools import readini

# 读取 ini 文件
config = readini("config.ini")
print(config)

# 读取指定编码的 ini 文件
config = readini("config.ini", encoding="gbk")
print(config)
```

### saveini()

**功能**：保存嵌套字典为 ini 文件。

**参数**：
- `savename`：保存文件名，可不包含后缀名 .ini
- `iniconfig`：嵌套字典
- `section_prefix`：ini文件的 section 部分前缀，默认为空[即不添加前缀]
- `bool_space`：等号前后是否添加空格，默认为 True[即默认添加空格]
- `encoding`：编码，默认 utf-8

**返回值**：`None`

**使用示例**：

```python
from hzgt.tools import saveini

# 定义配置字典
config = {
    "Server": {
        "host": "127.0.0.1",
        "port": 8080,
        "debug": True
    },
    "Database": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "password",
        "database": "mydb"
    }
}

# 保存为 ini 文件
saveini("config.ini", config)

# 保存为 ini 文件，添加 section 前缀
saveini("config_with_prefix.ini", config, section_prefix="App")

# 保存为 ini 文件，不添加空格
saveini("config_no_space.ini", config, bool_space=False)
```

**完整使用示例**：

```python
from hzgt.tools import readini, saveini

# 定义配置字典
config = {
    "Server": {
        "host": "127.0.0.1",
        "port": 8080,
        "debug": True
    },
    "Database": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "password",
        "database": "mydb"
    }
}

# 保存配置
saveini("app_config.ini", config)
print("配置已保存到 app_config.ini")

# 读取配置
loaded_config = readini("app_config.ini")
print("\n加载的配置:")
print(loaded_config)

# 修改配置
loaded_config["Server"]["port"] = 9090
loaded_config["Server"]["debug"] = False

# 保存修改后的配置
saveini("app_config_updated.ini", loaded_config)
print("\n修改后的配置已保存到 app_config_updated.ini")
```

**INI 文件格式示例**：

保存后的 `app_config.ini` 文件内容：

```ini
[Server]
host = 127.0.0.1
port = 8080
debug = True

[Database]
host = localhost
port = 3306
user = root
password = password
database = mydb
```