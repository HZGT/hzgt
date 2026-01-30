# autoconfig.py 文档

## 导航目录

- [ConditionalDefault](#conditionaldefault)
- [AutoConfig](#autoconfig)

## 类说明

### ConditionalDefault

**功能**：根据环境变量值决定使用的默认值包装器。

**参数**：
- `*conditions`：可变数量的元组参数，每个元组为 (condition, default_value)
  - `condition`：条件值(为str类型)或可调用对象（接受环境变量值，返回布尔值）
  - `default_value`：当条件满足时要使用的值，可以是静态值或可调用对象

**方法**：
- `get_value(env_value)`：根据环境变量的值获取对应的默认值
  - `env_value`：环境变量的原始值
  - 返回：满足条件时返回对应的默认值，否则返回环境变量的原始值

**使用示例**：
```python
from hzgt import ConditionalDefault

# 定义条件默认值
conditional_default = ConditionalDefault(
    ("0", "默认值1"),
    (None, "默认值2"),
    (lambda x: x == "", "空字符串时的默认值"),
    (lambda x: len(x) < 5, "短字符串时的默认值")
)

# 测试不同环境变量值
print(conditional_default.get_value("0"))  # 输出：默认值1
print(conditional_default.get_value(None))  # 输出：默认值2
print(conditional_default.get_value(""))   # 输出：空字符串时的默认值
print(conditional_default.get_value("hi"))  # 输出：短字符串时的默认值
print(conditional_default.get_value("hello world"))  # 输出：hello world
```

### AutoConfig

**功能**：基础类，用于从环境变量自动读取配置值。继承此类的子类可以定义带有类型注解的类属性，这些属性会自动从环境变量中读取值。

**构造方法参数**：
- `envpath`：.env路径
- `env_override`：如果为True，环境变量的值会覆盖提供的kwargs；如果为False，kwargs优先
- `**kwargs`：提供给实例的初始值

**使用示例**：

```python
from hzgt import AutoConfig

# 基本配置类
class ConfigModel(AutoConfig):
    OPENAI_API_KEY: str
    OPENAI_API_BASE: str = "https://api.siliconflow.cn/v1"
    DEBUG: bool = False

# 嵌套配置类
class DatabaseConfig(AutoConfig):
    HOST: str = "localhost"
    PORT: int = 5432
    USERNAME: str
    PASSWORD: str

class AppConfig(AutoConfig):
    DEBUG: bool = False
    DB_CONFIG: DatabaseConfig

# 使用示例
config = ConfigModel()  # 从环境变量读取值
print(config.OPENAI_API_KEY)
print(config.OPENAI_API_BASE)

# 从字典初始化嵌套配置
db_config_dict = {
    "HOST": "db.example.com",
    "PORT": 5432,
    "USERNAME": "admin",
    "PASSWORD": "secret"
}

app_config = AppConfig(
    DEBUG=True,
    DB_CONFIG=db_config_dict
)
print(app_config.DEBUG)
print(app_config.DB_CONFIG.HOST)
```

**类型转换支持**：
- 基本类型：str, int, float, bool
- 容器类型：list, tuple, set, dict
- 自定义类类型，包括嵌套的AutoConfig子类
- 布尔值转换支持多种格式："true", "t", "yes", "y", "1", "on" 为True；"false", "f", "no", "n", "0", "off" 为False

**环境变量加载**：
- 自动从当前目录的.env文件加载环境变量
- 支持指定自定义.env文件路径
- 支持通过kwargs覆盖环境变量值（当env_override=False时）