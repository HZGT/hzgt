import inspect
import json
import os
from typing import Any, Dict, Type, TypeVar, get_type_hints, List, Set, Tuple, Union, get_args, get_origin

T = TypeVar('T', bound='AutoConfig')


class AutoConfig:
    """基础类，用于从环境变量自动读取配置值。

    继承此类的子类可以定义带有类型注解的类属性，这些属性会自动从环境变量中读取值。
    如果为属性提供了默认值且环境变量不存在，则使用默认值。
    根据类型注解，会自动将环境变量的字符串值转换为对应类型，包括自定义类类型。

    示例:
        >>> class ConfigModel(AutoConfig):
        >>>     OPENAI_API_KEY: str
        >>>     OPENAI_API_BASE: str = "https://api.siliconflow.cn/v1"
        >>>
        >>> config = ConfigModel()  # 会自动从环境变量读取值
        >>> print(config.OPENAI_API_KEY)
        >>> print(config.OPENAI_API_BASE)


        >>> class DatabaseConfig(AutoConfig):
        >>>     HOST: str = "localhost"
        >>>     PORT: int = 5432
        >>>     USERNAME: str
        >>>     PASSWORD: str
        >>>
        >>> class AppConfig(AutoConfig):
        >>>     DEBUG: bool = False
        >>>     DB_CONFIG: DatabaseConfig
        >>>
        >>> # 环境变量可以这样设置：
        >>> # DB_CONFIG='{"HOST": "db.example.com", "PORT": 5432, "USERNAME": "user", "PASSWORD": "pass"}'
    """

    # 用于防止循环引用导致的无限递归
    _conversion_stack = set()
    __SENSITIVE_WORDS = {
        "access", "api_key", "auth", "cert", "credential",
        "encryption_key", "password", "password_hash", "password_salt",
        "passwd", "private", "pwd", "salt", "secret", "session_token",
        "ssh", "token", "token_type", "refresh_token", "key"
    }

    def __new__(cls: Type[T], _env_override: bool = True, **kwargs) -> T:
        """
        创建类的新实例，从环境变量或提供的参数中读取值。

        Args:
            _env_override: 如果为True，环境变量的值会覆盖提供的kwargs；如果为False，kwargs优先
            **kwargs: 提供给实例的初始值

        Returns:
            类的新实例

        Raises:
            ValueError: 如果必需的属性没有值，或者类型转换失败
        """
        instance = super().__new__(cls)

        # 获取类的所有类型注解
        type_hints = get_type_hints(cls)

        # 保存所有将要设置的属性及其值
        attrs_to_set = {}

        # 遍历类变量
        for name, field_type in type_hints.items():
            # 跳过私有属性和魔法方法
            if name.startswith('_'):
                continue

            # 获取默认值（如果有）
            default_value = getattr(cls, name, None) if hasattr(cls, name) else None
            has_default = hasattr(cls, name)

            # 确定属性值来源的优先级
            # 1. 如果 _env_override=True 且环境变量存在，使用环境变量
            # 2. 如果在 kwargs 中提供了值，使用 kwargs 中的值
            # 3. 如果有默认值，使用默认值
            # 4. 如果以上都不满足，抛出异常

            # 从环境变量中获取值
            env_value = os.environ.get(name) if _env_override else None

            # 从 kwargs 中获取值
            kwarg_value = kwargs.get(name, None)
            has_kwarg = name in kwargs

            # 确定使用哪个值
            if env_value is not None:
                try:
                    value = AutoConfig._convert_value(env_value, field_type)
                except Exception as e:
                    raise ValueError(f"环境变量 '{name}' 的值无法转换为类型 {field_type}: {e}") from None
            elif has_kwarg:
                try:
                    value = AutoConfig._convert_value(kwarg_value, field_type)
                except Exception as e:
                    raise ValueError(f"参数 '{name}' 的值 '{kwarg_value}' 无法转换为类型 {field_type}: {e}") from None
            elif has_default:
                value = default_value
            else:
                raise ValueError(f"属性 '{name}' 未设置且没有默认值")

            # 将属性及其值添加到要设置的列表中
            attrs_to_set[name] = value

        # 设置所有属性
        for name, value in attrs_to_set.items():
            setattr(instance, name, value)

        return instance

    @classmethod
    def _convert_value(cls, value: Any, target_type: Type) -> Any:
        """
        将值转换为目标类型。

        Args:
            value: 要转换的值
            target_type: 目标类型

        Returns:
            转换后的值

        Raises:
            ValueError: 如果无法转换为目标类型
            RecursionError: 如果检测到类型转换循环引用
        """
        # 防止循环引用导致的无限递归
        conversion_key = (id(value), str(target_type))
        if conversion_key in cls._conversion_stack:
            raise RecursionError(f"检测到类型转换的循环引用: {value} -> {target_type}")

        cls._conversion_stack.add(conversion_key)

        try:
            # 如果值已经是目标类型，直接返回
            if isinstance(value, target_type):
                return value

            # 获取原始类型（处理 typing 模块的类型）
            origin_type = get_origin(target_type) or target_type

            # 如果是 Union 类型（包括 Optional），递归尝试每个子类型
            if origin_type is Union:
                args = get_args(target_type)
                # 过滤掉 NoneType
                non_none_args = [arg for arg in args if arg is not type(None)]

                # 如果值是 None 且 NoneType 在 Union 中，返回 None
                if value is None and type(None) in args:
                    return None

                # 尝试每个非 None 类型
                for arg in non_none_args:
                    try:
                        return cls._convert_value(value, arg)
                    except (ValueError, TypeError):
                        continue

                # 如果所有类型都失败
                raise ValueError(f"无法将 '{value}' 转换为任意 {target_type} 类型")

            # 处理容器类型
            if origin_type in (list, List):
                item_type = get_args(target_type)[0]
                if isinstance(value, str):
                    # 尝试解析 JSON 数组
                    try:
                        items = json.loads(value)
                        if isinstance(items, list):
                            return [cls._convert_value(item, item_type) for item in items]
                    except json.JSONDecodeError:
                        # 如果 JSON 解析失败，退回到按逗号分割
                        items = value.split(',')
                        return [cls._convert_value(item.strip(), item_type) for item in items]
                elif isinstance(value, (list, tuple)):
                    return [cls._convert_value(item, item_type) for item in value]

            elif origin_type in (tuple, Tuple):
                args = get_args(target_type)
                if isinstance(value, str):
                    # 尝试解析 JSON 数组
                    try:
                        items = json.loads(value)
                        if isinstance(items, list):
                            if len(items) != len(args) and not (len(args) == 2 and args[1] is Ellipsis):
                                raise ValueError(f"元组长度不匹配：期望 {len(args)}，得到 {len(items)}")

                            if len(args) == 2 and args[1] is Ellipsis:
                                # 处理 Tuple[Type, ...]
                                item_type = args[0]
                                return tuple(cls._convert_value(item, item_type) for item in items)
                            else:
                                return tuple(cls._convert_value(item, arg) for item, arg in zip(items, args))
                    except json.JSONDecodeError:
                        # 如果 JSON 解析失败，退回到按逗号分割
                        items = value.split(',')
                        if len(items) != len(args) and not (len(args) == 2 and args[1] is Ellipsis):
                            raise ValueError(f"元组长度不匹配：期望 {len(args)}，得到 {len(items)}")

                        if len(args) == 2 and args[1] is Ellipsis:
                            # 处理 Tuple[Type, ...]
                            item_type = args[0]
                            return tuple(cls._convert_value(item.strip(), item_type) for item in items)
                        else:
                            return tuple(cls._convert_value(item.strip(), arg) for item, arg in zip(items, args))
                elif isinstance(value, (list, tuple)):
                    if len(value) != len(args) and not (len(args) == 2 and args[1] is Ellipsis):
                        raise ValueError(f"元组长度不匹配：期望 {len(args)}，得到 {len(value)}")

                    if len(args) == 2 and args[1] is Ellipsis:
                        # 处理 Tuple[Type, ...]
                        item_type = args[0]
                        return tuple(cls._convert_value(item, item_type) for item in value)
                    else:
                        return tuple(cls._convert_value(item, arg) for item, arg in zip(value, args))

            elif origin_type in (set, Set):
                item_type = get_args(target_type)[0]
                if isinstance(value, str):
                    # 尝试解析 JSON 数组
                    try:
                        items = json.loads(value)
                        if isinstance(items, list):
                            return {cls._convert_value(item, item_type) for item in items}
                    except json.JSONDecodeError:
                        # 如果 JSON 解析失败，退回到按逗号分割
                        items = value.split(',')
                        return {cls._convert_value(item.strip(), item_type) for item in items}
                elif isinstance(value, (list, tuple, set)):
                    return {cls._convert_value(item, item_type) for item in value}

            elif origin_type is dict or origin_type is Dict:
                if isinstance(value, str):
                    try:
                        dict_value = json.loads(value)
                        if not isinstance(dict_value, dict):
                            raise ValueError(f"JSON 值 '{dict_value}' 不是字典类型")

                        # 如果提供了键值类型，则进行转换
                        type_args = get_args(target_type)
                        if len(type_args) == 2:
                            key_type, val_type = type_args
                            return {cls._convert_value(k, key_type): cls._convert_value(v, val_type)
                                    for k, v in dict_value.items()}
                        return dict_value
                    except json.JSONDecodeError:
                        raise ValueError(f"无法解析为字典") from None
                elif isinstance(value, dict):
                    # 如果提供了键值类型，则进行转换
                    type_args = get_args(target_type)
                    if len(type_args) == 2:
                        key_type, val_type = type_args
                        return {cls._convert_value(k, key_type): cls._convert_value(v, val_type)
                                for k, v in value.items()}
                    return value

            # 处理基本类型
            if target_type is str:
                return str(value)
            elif target_type is int:
                try:
                    return int(value)
                except ValueError:
                    # 尝试将布尔值字符串转为整数
                    if isinstance(value, str) and value.lower() in ('true', 'false'):
                        return 1 if value.lower() == 'true' else 0
                    raise ValueError(f"无法将 '{value}' 转换为 int 类型")
            elif target_type is float:
                return float(value)
            elif target_type is bool:
                if isinstance(value, str):
                    if value.lower() in ('true', 'yes', '1', 'y', 'on'):
                        return True
                    elif value.lower() in ('false', 'no', '0', 'n', 'off'):
                        return False
                    raise ValueError(f"无法将字符串 '{value}' 转换为 bool 类型")
                return bool(value)

            # 处理自定义类类型
            if inspect.isclass(target_type):
                # 检查是否是 AutoConfig 的子类
                if issubclass(target_type, AutoConfig):
                    if isinstance(value, dict):
                        # 如果值是字典，直接传给构造函数，并设置 _env_override=False
                        # 这样嵌套的 AutoConfig 类会优先使用传入的字典值，而不是环境变量
                        return target_type(_env_override=False, **value)
                    elif isinstance(value, str):
                        try:
                            # 尝试将字符串解析为 JSON 对象
                            dict_value = json.loads(value)
                            if isinstance(dict_value, dict):
                                # 设置 _env_override=False，这样嵌套的 AutoConfig 类会优先使用传入的字典值
                                return target_type(_env_override=False, **dict_value)
                            raise ValueError(f"JSON 值 '{dict_value}' 不是字典类型，无法初始化 {target_type.__name__}")
                        except json.JSONDecodeError:
                            raise ValueError(f"无法将字符串解析为字典，无法初始化 {target_type.__name__}") from None

                # 处理其他自定义类
                if isinstance(value, str) and value.strip().startswith('{') and value.strip().endswith('}'):
                    # 看起来是 JSON 字符串，尝试解析
                    try:
                        dict_value = json.loads(value)
                        if isinstance(dict_value, dict):
                            # 分析类的构造函数
                            signature = inspect.signature(target_type.__init__)
                            params = list(signature.parameters.values())

                            # 跳过 self 参数
                            params = params[1:] if params and params[0].name == 'self' else params

                            # 判断参数类型
                            if all(p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD for p in params):
                                # 如果是位置参数，尝试按顺序提取并传递
                                try:
                                    # 先尝试关键字参数方式
                                    return target_type(**dict_value)
                                except TypeError:
                                    # 关键字方式失败，尝试按位置参数顺序提取值
                                    param_names = [p.name for p in params]
                                    param_values = []

                                    # 按照参数顺序提取值
                                    for name in param_names:
                                        if name in dict_value:
                                            param_values.append(dict_value[name])
                                        else:
                                            # 如果缺少必要参数，抛出错误
                                            raise ValueError(
                                                f"缺少初始化 {target_type.__name__} 所需的参数 '{name}'") from None

                                    return target_type(*param_values)
                            else:
                                # 变长参数或关键字参数
                                return target_type(**dict_value)
                    except json.JSONDecodeError:
                        # 不是有效的 JSON，尝试直接传递字符串
                        try:
                            return target_type(value)
                        except Exception as e:
                            raise ValueError(f"无法初始化类 {target_type.__name__}: {e}") from None
                elif isinstance(value, dict):
                    # 字典直接作为参数
                    try:
                        # 分析类的构造函数
                        signature = inspect.signature(target_type.__init__)
                        params = list(signature.parameters.values())

                        # 跳过 self 参数
                        params = params[1:] if params and params[0].name == 'self' else params

                        # 判断参数类型
                        if all(p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD for p in params):
                            # 如果是位置参数，尝试按顺序提取并传递
                            try:
                                # 先尝试关键字参数方式
                                return target_type(**value)
                            except TypeError:
                                # 关键字方式失败，尝试按位置参数顺序提取值
                                param_names = [p.name for p in params]
                                param_values = []

                                # 按照参数顺序提取值
                                for name in param_names:
                                    if name in value:
                                        param_values.append(value[name])
                                    else:
                                        # 如果缺少必要参数，抛出错误
                                        raise ValueError(
                                            f"缺少初始化 {target_type.__name__} 所需的参数 '{name}'") from None

                                return target_type(*param_values)
                        else:
                            # 变长参数或关键字参数
                            return target_type(**value)
                    except Exception as e:
                        raise ValueError(f"无法初始化类 {target_type.__name__}: {e}") from None
                else:
                    # 其他情况，尝试直接使用值初始化
                    try:
                        return target_type(value)
                    except Exception as e:
                        raise ValueError(f"无法将 '{value}' 转换为 {target_type.__name__} 实例") from None

            # 默认情况尝试强制类型转换
            try:
                return target_type(value)
            except (ValueError, TypeError) as e:
                raise ValueError(f"无法将 '{value}' 转换为 {target_type.__name__} 类型") from None

        finally:
            # 无论成功与否，都需要从栈中移除当前转换
            cls._conversion_stack.remove(conversion_key)

    def __repr__(self) -> str:
        """返回模型的字符串表示形式"""
        attrs = []
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                # 对敏感信息（如API密钥）进行掩码处理
                key_lower = key.lower()

                if any(kw in key_lower for kw in self.__SENSITIVE_WORDS):
                    if isinstance(value, str) and len(value) > 8:
                        masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:]
                    else:
                        masked_value = '****'
                    attrs.append(f"{key}='{masked_value}'")
                else:
                    attrs.append(f"{key}={repr(value)}")
        return f"{self.__class__.__name__}({', '.join(attrs)})"


# 使用示例
if __name__ == "__main__":
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

    # 嵌套类类型
    class DatabaseConfig(AutoConfig):
        HOST: str = "localhost"
        PORT: int = 5432
        USERNAME: str
        PASSWORD: str

    class AppConfig(AutoConfig):
        DEBUG: bool = False
        DB_CONFIG: DatabaseConfig

    # 测试简单配置
    simple_config = SimpleConfig()
    print("简单配置:")
    print(simple_config)

    # 测试嵌套配置
    app_config = AppConfig()
    print("\n嵌套配置:")
    print(app_config)
    print(f"数据库主机: {app_config.DB_CONFIG.HOST}")
    print(f"数据库端口: {app_config.DB_CONFIG.PORT}")
    print(f"数据库用户名: {app_config.DB_CONFIG.USERNAME}")
    print(f"数据库密码: {app_config.DB_CONFIG.PASSWORD}")

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
