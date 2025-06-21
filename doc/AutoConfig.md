
---
`类[class]: AutoConfig()`
---

`AutoConfig` 类提供了自动获取配置的功能.

The `AutoConfig` class provides the ability to automatically obtain configuration.

---
- [使用示例](#examples)
---

### examples
### 使用示例[Examples]

```python
import os
from hzgt import AutoConfig

"""
基础类，用于从环境变量自动读取配置值。  
继承此类的子类可以定义带有类型注解的类属性，
这些属性会自动从环境变量中读取值。 
如果为属性提供了默认值且环境变量不存在，则使用默认值。 
根据类型注解，会自动将环境变量的字符串值转换为对应类型，包括自定义类类型。
"""

# 设置环境变量进行测试
os.environ["OPENAI_API_KEY"] = "sk-123456"
os.environ["OPENAI_API_BASE"] = "https://api.siliconflow.cn/v1"
os.environ["DB_CONFIG"] = '{"HOST": "db.example.com", "PORT": 5432, "USERNAME": "user", "PASSWORD": "pass"}'
os.environ["LOCATION"] = '{"x": 10, "y": 20}'

# 简单类型
class SimpleConfig(AutoConfig):
    OPENAI_API_KEY: str
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    MAX_TOKENS: int = 100
    DEBUG: bool = False

# 测试简单配置
simple_config = SimpleConfig()
print("简单配置:")
print(simple_config)

# =-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=
# 嵌套类类型
class DatabaseConfig(AutoConfig):
    HOST: str = "localhost"
    PORT: int = 5432
    USERNAME: str
    PASSWORD: str

class AppConfig(AutoConfig):
    DEBUG: bool = False
    DB_CONFIG: DatabaseConfig
    
# 测试嵌套配置
app_config = AppConfig()
print("\n嵌套配置:")
print(app_config)
print(f"数据库主机: {app_config.DB_CONFIG.HOST}")
print(f"数据库端口: {app_config.DB_CONFIG.PORT}")
print(f"数据库用户名: {app_config.DB_CONFIG.USERNAME}")
print(f"数据库密码: {app_config.DB_CONFIG.PASSWORD}")

#=-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-==-=-=-=-=-=-=-=-=
# 非 AutoConfig 类
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Point({self.x}, {self.y})"

class GeoConfig(AutoConfig):
    LOCATION: Point

# 非 AutoConfig 类
geo_config = GeoConfig()
print("\n非 AutoConfig 类:")
print(geo_config)
print(f"位置: x={geo_config.LOCATION.x}, y={geo_config.LOCATION.y}")
```



