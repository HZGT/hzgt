import inspect
import json
import os
import sys
from typing import Any, Dict, Type, TypeVar, get_type_hints, List, Set, Tuple, Union, get_args, get_origin

from dotenv import load_dotenv

T = TypeVar('T', bound='AutoConfig')


class ConditionalDefault:
    """根据环境变量值决定使用的默认值包装器

    这个类用于包装多个条件-值对，当环境变量的值满足特定条件时，
    使用对应的默认值而不是原始环境变量值。

    参数:
        *conditions: 可变数量的元组参数，每个元组为 (condition, default_value)
            condition: 条件值(为str类型)或可调用对象（接受环境变量值，返回布尔值）
            default_value: 当条件满足时要使用的值，可以是静态值或可调用对象

    示例:
        ConditionalDefault(
            ("0", "默认值1"),
            (None, "默认值2"),
            (lambda x: x == "", "空字符串时的默认值"),
            (lambda x: len(x) < 5, "短字符串时的默认值")
        )
    """

    def __init__(self, *conditions):
        self.conditions = list(conditions)

    def get_value(self, env_value: Any) -> Any:
        """根据环境变量的值获取对应的默认值

        Args:
            env_value: 环境变量的原始值

        Returns:
            满足条件时返回对应的默认值，否则返回环境变量的原始值
        """
        for condition, default_value in self.conditions:
            # 判断条件是否满足
            if callable(condition):
                # 条件是可调用对象
                try:
                    if condition(env_value):
                        return default_value() if callable(default_value) else default_value
                except Exception as e:
                    raise Exception(f"{e}") from None
            else:
                # 条件是具体值
                if env_value == condition:
                    return default_value() if callable(default_value) else default_value

        # 没有条件满足，返回原始值
        return env_value

    def __repr__(self) -> str:
        return f"ConditionalDefault({', '.join(str(c) for c in self.conditions)})"


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

    """

    # 用于防止循环引用导致的无限递归
    _conversion_stack = set()
    # 敏感词
    __SENSITIVE_WORDS = {
        "access", "api_key", "auth", "cert", "credential",
        "encryption_key", "password", "password_hash", "password_salt",
        "passwd", "private", "pwd", "salt", "secret", "session_token",
        "ssh", "token", "token_type", "refresh_token", "key"
    }
    # 布尔转换
    __TO_BOOL_TRUE = ("true", "t", "yes", "y", "1", "on")
    __TO_BOOL_FALSE = ("false", "f", "no", "n", "0", "off")

    def __new__(cls: Type[T], envpath: str = None, env_override: bool = True, **kwargs) -> T:
        """
        创建类的新实例，从环境变量或提供的参数中读取值。

        Args:
            envpath: .env路径
            env_override: 如果为True，环境变量的值会覆盖提供的kwargs；如果为False，kwargs优先
            **kwargs: 提供给实例的初始值

        Returns:
            类的新实例

        Raises:
            ValueError: 如果必需的属性没有值，或者类型转换失败
        """

        # 加载环境变量
        if envpath:
            load_dotenv(envpath)
        else:
            # 获取主脚本所在目录
            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            env_file_path = os.path.join(script_dir, ".env")
            load_dotenv(env_file_path)

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

            # 从环境变量中获取值
            env_value = os.environ.get(name) if env_override else None

            # 检查环境变量是否为空（None 或空字符串）
            is_env_empty = env_value is None or env_value == ""

            # 从 kwargs 中获取值
            kwarg_value = kwargs.get(name, None)
            has_kwarg = name in kwargs

            # 确定使用哪个值
            # 如果环境变量存在且非空
            if env_value is not None and not is_env_empty:
                # 检查默认值是否是 ConditionalDefault 类型
                if isinstance(default_value, ConditionalDefault):
                    # 使用 ConditionalDefault 处理环境变量值
                    try:
                        raw_value = default_value.get_value(env_value)
                        # 如果 raw_value 等于 env_value，说明没有匹配到条件，使用环境变量值
                        # 否则使用 ConditionalDefault 提供的值
                        if raw_value == env_value:
                            value = cls._convert_value(env_value, field_type, env_value)
                        else:
                            value = cls._convert_value(raw_value, field_type, env_value)
                    except Exception as e:
                        raise ValueError(f"环境变量 '{name}' 的 ConditionalDefault 处理失败: {e}") from None
                else:
                    # 否则直接使用环境变量
                    try:
                        value = cls._convert_value(env_value, field_type, env_value)
                    except Exception as e:
                        raise ValueError(f"环境变量 '{name}' 的值无法转换为类型 {field_type}: {e}") from None
            elif has_kwarg:
                # 使用 kwargs 中的值
                try:
                    value = cls._convert_value(kwarg_value, field_type, None)
                except Exception as e:
                    raise ValueError(f"参数 '{name}' 的值 '{kwarg_value}' 无法转换为类型 {field_type}: {e}") from None
            elif has_default:
                # 使用默认值，检查是否是 ConditionalDefault 类型
                if isinstance(default_value, ConditionalDefault):
                    # 如果是 ConditionalDefault 类型，根据环境变量值获取对应的默认值
                    try:
                        # 传递环境变量的原始值给 ConditionalDefault
                        raw_value = default_value.get_value(env_value if env_value is not None else None)
                        value = cls._convert_value(raw_value, field_type, env_value)
                    except Exception as e:
                        raise ValueError(f"'{name}'值 无法转换为类型 {field_type.__name__}: {e}")
                else:
                    # 否则直接使用默认值
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
    def _convert_value(cls, value: Any, target_type: Type, env_value: Any = None) -> Any:
        """
        将值转换为目标类型。

        Args:
            value: 要转换的值
            target_type: 目标类型
            env_value: 环境变量的原始值（用于 ConditionalDefault 处理）

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
            # 如果值是 ConditionalDefault 类型，先获取其值
            if isinstance(value, ConditionalDefault):
                # 使用环境变量的原始值（如果提供了）或传递的值
                if env_value is not None:
                    raw_value = value.get_value(env_value)
                else:
                    raw_value = value.get_value(value)
                # 递归调用 _convert_value 处理获取的值
                return cls._convert_value(raw_value, target_type, env_value)

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
                        return cls._convert_value(value, arg, env_value)
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
                            return [cls._convert_value(item, item_type, env_value) for item in items]
                    except json.JSONDecodeError:
                        # 如果 JSON 解析失败，退回到按逗号分割
                        items = value.split(',')
                        return [cls._convert_value(item.strip(), item_type, env_value) for item in items]
                elif isinstance(value, (list, tuple)):
                    return [cls._convert_value(item, item_type, env_value) for item in value]

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
                                return tuple(cls._convert_value(item, item_type, env_value) for item in items)
                            else:
                                return tuple(cls._convert_value(item, arg, env_value) for item, arg in zip(items, args))
                    except json.JSONDecodeError:
                        # 如果 JSON 解析失败，退回到按逗号分割
                        items = value.split(',')
                        if len(items) != len(args) and not (len(args) == 2 and args[1] is Ellipsis):
                            raise ValueError(f"元组长度不匹配：期望 {len(args)}，得到 {len(items)}")

                        if len(args) == 2 and args[1] is Ellipsis:
                            # 处理 Tuple[Type, ...]
                            item_type = args[0]
                            return tuple(cls._convert_value(item.strip(), item_type, env_value) for item in items)
                        else:
                            return tuple(
                                cls._convert_value(item.strip(), arg, env_value) for item, arg in zip(items, args))
                elif isinstance(value, (list, tuple)):
                    if len(value) != len(args) and not (len(args) == 2 and args[1] is Ellipsis):
                        raise ValueError(f"元组长度不匹配：期望 {len(args)}，得到 {len(value)}")

                    if len(args) == 2 and args[1] is Ellipsis:
                        # 处理 Tuple[Type, ...]
                        item_type = args[0]
                        return tuple(cls._convert_value(item, item_type, env_value) for item in value)
                    else:
                        return tuple(cls._convert_value(item, arg, env_value) for item, arg in zip(value, args))

            elif origin_type in (set, Set):
                item_type = get_args(target_type)[0]
                if isinstance(value, str):
                    # 尝试解析 JSON 数组
                    try:
                        items = json.loads(value)
                        if isinstance(items, list):
                            return {cls._convert_value(item, item_type, env_value) for item in items}
                    except json.JSONDecodeError:
                        # 如果 JSON 解析失败，退回到按逗号分割
                        items = value.split(',')
                        return {cls._convert_value(item.strip(), item_type, env_value) for item in items}
                elif isinstance(value, (list, tuple, set)):
                    return {cls._convert_value(item, item_type, env_value) for item in value}

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
                            return {
                                cls._convert_value(k, key_type, env_value): cls._convert_value(v, val_type, env_value)
                                for k, v in dict_value.items()}
                        return dict_value
                    except json.JSONDecodeError:
                        raise ValueError(f"无法解析为字典") from None
                elif isinstance(value, dict):
                    # 如果提供了键值类型，则进行转换
                    type_args = get_args(target_type)
                    if len(type_args) == 2:
                        key_type, val_type = type_args
                        return {cls._convert_value(k, key_type, env_value): cls._convert_value(v, val_type, env_value)
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
                    if value.lower() in cls.__TO_BOOL_TRUE:
                        return True
                    elif value.lower() in cls.__TO_BOOL_FALSE:
                        return False
                    raise ValueError(f"无法将字符串 '{value}' 转换为 bool 类型")
                return bool(value)

            # 处理自定义类类型
            if inspect.isclass(target_type):
                # 检查是否是 AutoConfig 的子类
                if issubclass(target_type, AutoConfig):
                    if isinstance(value, dict):
                        # 如果值是字典，直接传给构造函数，并设置 env_override=False
                        # 这样嵌套的 AutoConfig 类会优先使用传入的字典值，而不是环境变量
                        return target_type(env_override=False, **value)
                    elif isinstance(value, str):
                        try:
                            # 尝试将字符串解析为 JSON 对象
                            dict_value = json.loads(value)
                            if isinstance(dict_value, dict):
                                # 设置 env_override=False，这样嵌套的 AutoConfig 类会优先使用传入的字典值
                                return target_type(env_override=False, **dict_value)
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
                    if isinstance(value, str) and len(value) > 10:
                        masked_value = value[:4] + '*' * 4 + value[-2:]
                    else:
                        masked_value = '****'
                    attrs.append(f"{key}='{masked_value}'")
                else:
                    attrs.append(f"{key}={repr(value)}")
        return f"{self.__class__.__name__}({', '.join(attrs)})"
