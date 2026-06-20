# -*- coding: utf-8 -*-
import random
import string
import threading
import time
from dataclasses import dataclass, field
from logging import Logger
from typing import Literal, Dict, Optional, Any, Union, List

import paho.mqtt.client as mqtt
from paho.mqtt.enums import MQTTProtocolVersion
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties

from ..core.Decorator import vargs
from ..core.log import set_log

"""
0x00 - 连接已接受(Connection Accepted): 表示服务器接受了客户端的连接请求, 连接建立成功
0x01 - 连接已拒绝, 不支持的协议版本(Connection Refused, Unacceptable Protocol Version): 服务器不支持客户端使用的MQTT协议版本
0x02 - 连接已拒绝, 不合格的客户端标识符(Connection Refused, Identifier Rejected): 客户端提供的标识符(Client ID)不符合服务器的要求, 可能是格式不正确或者与其他客户端冲突
0x03 - 连接已拒绝, 服务端不可用(Connection Refused, Server Unavailable): 服务器当前不可用, 无法处理客户端的连接请求
0x04 - 连接已拒绝, 无效的用户名或密码(Connection Refused, Bad User Name or Password): 客户端提供的用户名或密码无效
0x05 - 连接已拒绝, 未授权(Connection Refused, Not Authorized): 客户端没有被授权连接到服务器
"""


@dataclass
class MqttMessage:
    """
    MQTT 消息封装类, 支持索引访问、迭代和字符串表示.
    """
    topic: str
    payload: bytes
    qos: int
    retain: bool
    properties: Dict[str, Any]          # 存储所有 MQTT 5.0 属性(键为属性名, 值为对应类型的值)
    raw_properties: Optional[Properties] = None  # 原始 Properties 对象(仅 V5 有效)
    timestamp: float = field(default_factory=time.time)

    # ---------- 索引访问 ----------
    def __getitem__(self, index: int):
        # 索引映射: 0->topic, 1->payload, 2->qos, 3->retain, 4->properties, 5->timestamp
        if index == 0:
            return self.topic
        elif index == 1:
            return self.payload
        elif index == 2:
            return self.qos
        elif index == 3:
            return self.retain
        elif index == 4:
            return self.properties
        elif index == 5:
            return self.timestamp
        else:
            raise IndexError(f"Index 的值应为 0-5, 但 Index 为 {index}")

    def __len__(self) -> int:
        return 6

    # ---------- 迭代器(支持解包和循环)----------
    def __iter__(self):
        yield self.topic
        yield self.payload
        yield self.qos
        yield self.retain
        yield self.properties
        yield self.timestamp

    # ---------- 字符串表示 ----------
    def __str__(self) -> str:
        return (f"MqttMessage(topic={self.topic!r}, payload={self.payload!r}, "
                f"qos={self.qos}, retain={self.retain}, "
                f"properties={self.properties}, timestamp={self.timestamp:.3f})")


class Mqttop:
    # ---------- MQTT 5.0 属性定义 ----------
    # 标准属性名(与 paho 库属性名一致)
    PROPERTY_NAMES = {
        "PayloadFormatIndicator",
        "MessageExpiryInterval",
        "ContentType",
        "ResponseTopic",
        "CorrelationData",
        "SubscriptionIdentifier",
        "SessionExpiryInterval",
        "AssignedClientIdentifier",
        "ServerKeepAlive",
        "AuthenticationMethod",
        "AuthenticationData",
        "RequestProblemInformation",
        "WillDelayInterval",
        "RequestResponseInformation",
        "ResponseInformation",
        "ServerReference",
        "ReasonString",
        "ReceiveMaximum",
        "TopicAliasMaximum",
        "TopicAlias",
        "MaximumQoS",
        "RetainAvailable",
        "UserProperty",
        "MaximumPacketSize",
        "WildcardSubscriptionAvailable",
        "SubscriptionIdentifiersAvailable",
        "SharedSubscriptionAvailable",
    }

    # 友好名称映射(方便用户使用简短键名)
    FRIENDLY_NAMES = {
        "payload_format": "PayloadFormatIndicator",
        "message_expiry": "MessageExpiryInterval",
        "content_type": "ContentType",
        "response_topic": "ResponseTopic",
        "correlation_data": "CorrelationData",
        "subscription_id": "SubscriptionIdentifier",
        "session_expiry": "SessionExpiryInterval",
        "assigned_client": "AssignedClientIdentifier",
        "server_keepalive": "ServerKeepAlive",
        "auth_method": "AuthenticationMethod",
        "auth_data": "AuthenticationData",
        "req_problem": "RequestProblemInformation",
        "will_delay": "WillDelayInterval",
        "req_response": "RequestResponseInformation",
        "response_info": "ResponseInformation",
        "server_ref": "ServerReference",
        "reason": "ReasonString",
        "receive_max": "ReceiveMaximum",
        "topic_alias_max": "TopicAliasMaximum",
        "topic_alias": "TopicAlias",
        "max_qos": "MaximumQoS",
        "retain_avail": "RetainAvailable",
        "user_property": "UserProperty",
        "max_packet": "MaximumPacketSize",
        "wildcard_sub": "WildcardSubscriptionAvailable",
        "sub_id_avail": "SubscriptionIdentifiersAvailable",
        "shared_sub_avail": "SharedSubscriptionAvailable",
    }

    __CONNECTION_STATUS = {
        0: "连接成功",
        1: "连接被拒绝 - 协议版本不正确",
        2: "连接被拒绝 - 客户端标识符无效",
        3: "连接被拒绝 - 服务器不可用",
        4: "连接被拒绝 - 用户名或密码错误",
        5: "连接被拒绝 - 未授权",
        **{i: "未知返回码" for i in range(6, 256)}
    }

    __protocol = {
        3: MQTTProtocolVersion.MQTTv31,
        4: MQTTProtocolVersion.MQTTv311,
        5: MQTTProtocolVersion.MQTTv5
    }

    @staticmethod
    def __generate_random_clientid():
        part1 = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        part2 = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
        part3 = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
        return f"{part1}-{part2}-{part3}"

    def __init__(self, host: str, port: int,
                 user: str = '', passwd: str = '', clientid: str = '',
                 data_length: int = 100,
                 transport: Literal["tcp", "websockets", "unix"] = "tcp", protocol: Literal[3, 4, 5] = 3,
                 logger: Logger = None):
        """
        调用 self.publish() 函数发布信息

        + protocol:
            - 3 -- MQTTv31
            - 4 -- MQTTv311
            - 5 -- MQTTv5

        :param host: MQTT服务器IP地址
        :param port: MQTT端口
        :param user: 选填, 账号
        :param passwd: 选填, 密码
        :param clientid: 可选, "客户端"用户名 为空将随机
        :param data_length: 缓存数据列表的长度 默认为100
        :param protocol: MQTT协议版本 支持 3(v31) 4(v311) 5(v5)
        :param logger: 日志记录器
        """
        if protocol not in self.__protocol.keys():
            raise ValueError(f"protocol 协议版本错误, 参数必须为 {list(self.__protocol.keys())} 之一")

        self._data_dict = {}          # 接收到的数据缓存, 由锁保护
        self._data_lock = threading.Lock()  # 保护 _data_dict 的线程锁
        self._conn_lock = threading.Lock()  # 保护连接状态的线程锁
        self._bool_con_success = False      # 实际连接状态存储

        if host:
            self.host = host
        else:
            raise ValueError("host 主机地址为空")
        if port:
            self.port = int(port)
        else:
            raise ValueError("port 端口未配置")
        self.clientid = str(clientid)
        self.user = str(user)
        self.passwd = str(passwd)

        self.data_length = data_length if data_length > 0 else 100
        self.protocol = self.__protocol[protocol]

        if logger is None:
            self.__logger = set_log("hzgt.mqtt", fpath="logs", fname="mqtt", level=2)
        else:
            self.__logger = logger

        if len(self.clientid) == 0 or self.clientid is None:
            self.__client = mqtt.Client(client_id=self.__generate_random_clientid(),
                                        transport=transport, protocol=self.protocol)
        else:
            self.__client = mqtt.Client(client_id=self.clientid, transport=transport, protocol=self.protocol)
        self.__logger.info(f"MQTT服务器[协议版本({self.protocol})]连接信息: host[`{self.host}`] port[`{self.port}`] "
                           f"user[`{self.user}`] clientid[`{self.clientid}`]]")

    @property
    def bool_con_success(self) -> bool:
        """线程安全的连接状态读取"""
        with self._conn_lock:
            return self._bool_con_success

    @bool_con_success.setter
    def bool_con_success(self, value: bool):
        """线程安全的连接状态写入"""
        with self._conn_lock:
            self._bool_con_success = value

    def __del__(self):
        """删除对象时调用 __del__() 断开连接，捕获所有异常以避免干扰垃圾回收"""
        try:
            self.close()
        except Exception:
            # 在 __del__ 中忽略所有异常，避免干扰解释器
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ---------- 遗嘱 ----------
    @vargs({"qos": {0, 1, 2}})
    def set_will(self, will_topic: str, will_msg: str, qos: Literal[0, 1, 2] = 0, retain: bool = False,
                 properties: Optional[Dict[str, Any]] = None):
        """
        设置遗嘱, 需要在连接前设置.

        :param will_topic: 遗嘱主题
        :param will_msg: 遗嘱信息(字符串)
        :param qos: QoS 等级
        :param retain: 是否为保留消息
        :param properties: MQTT 5.0 遗嘱属性字典(键名支持标准名或友好名)
        """
        props = None
        if self.protocol == self.__protocol[5] and properties:
            props = self._create_properties(PacketTypes.WILLMESSAGE, properties)
        self.__client.will_set(will_topic, will_msg, qos, retain, properties=props)
        self.__logger.info(f"已设置遗嘱信息: will_topic[`{will_topic}`] will_msg[`{will_msg}`]")

    # ---------- 连接管理 ----------
    def start(self):
        """启动MQTT连接(非阻塞)"""
        threading.Thread(target=self.__run, daemon=True).start()

    def connect(self):
        """同 start()"""
        return self.start()

    def close(self):
        """断开MQTT连接, 停止网络循环, 释放资源. """
        try:
            self.__client.loop_stop()
        except Exception as e:
            self.__logger.debug(f"停止网络循环时出现异常(可忽略): {e}")

        try:
            self.__client.disconnect()
        except Exception as e:
            self.__logger.debug(f"断开连接时出现异常(可能已经断开): {e}")

        if self.bool_con_success:
            self.__logger.info("MQTT连接已关闭")
        self.bool_con_success = False

    def disconnect(self):
        """同 close()"""
        return self.close()

    def reconnect(self):
        """尝试重连: 先关闭当前连接, 再重新启动. """
        self.close()
        time.sleep(0.1)  # 确保资源释放
        self.start()

    # ---------- 回调函数 ----------
    def __on_disconnect_v3(self, client, userdata, rc):
        """
        断开连接回调(MQTT v3.1 / v3.1.1)
        """
        if self.bool_con_success:
            self.__logger.info(f"MQTT连接已断开, rc={rc}")
        self.bool_con_success = False

    def __on_disconnect_v5(self, client, userdata, reason_code, properties):
        """
        断开连接回调(MQTT v5.0)
        """
        if self.bool_con_success:
            log_msg = f"MQTT连接已断开, reason_code={reason_code}"
            if properties:
                try:
                    props_dict = properties.json()
                    log_msg += f", properties={props_dict}"
                except Exception:
                    log_msg += f", properties={properties}"
            self.__logger.info(log_msg)
        self.bool_con_success = False

    def __on_connect_v3(self, client, userdata, flags, rc):
        if rc == 0:
            self.__logger.info('MQTT服务器 连接成功!')
            self.bool_con_success = True
        else:
            self.__logger.error(f'连接出错 rc={rc} 错误代码: {self.__CONNECTION_STATUS.get(rc, f"未知返回码{rc}")}')
            self.bool_con_success = False

    def __on_connect_v5(self, client, userdata, flags, rc, properties):
        if rc == 0:
            self.__logger.info('MQTT服务器 连接成功!')
            self.bool_con_success = True
            try:
                props_dict = properties.json() if properties else {}
                self.__logger.info(f"MQTT服务器 返回信息: {props_dict}")
            except Exception:
                self.__logger.info(f"MQTT服务器 返回信息: {properties}")
        else:
            self.__logger.error(f'连接出错 rc={rc} 错误代码: {self.__CONNECTION_STATUS.get(rc, f"未知返回码{rc}")}')
            self.bool_con_success = False
            try:
                props_dict = properties.json() if properties else {}
                self.__logger.error(f"MQTT服务器 返回信息: {props_dict}")
            except Exception:
                self.__logger.error(f"MQTT服务器 返回信息: {properties}")

    def _cache_message(self, msg):
        """将收到的消息缓存到 _data_dict 中(线程安全), 并提取所有属性. """
        topic = msg.topic
        prop_dict = {}
        raw_props = None

        if hasattr(msg, 'properties') and msg.properties:
            raw_props = msg.properties
            try:
                prop_data = msg.properties.json()

                # 处理 UserProperty
                if "UserProperty" in prop_data:
                    user_props = prop_data.pop("UserProperty")
                    if isinstance(user_props, list):
                        converted = {}
                        for item in user_props:
                            if isinstance(item, (list, tuple)) and len(item) == 2:
                                key, val = item
                                converted[str(key)] = str(val)
                        if converted:
                            prop_dict["UserProperty"] = converted
                    else:
                        prop_dict["UserProperty"] = user_props

                # 其他属性直接赋值
                for key, value in prop_data.items():
                    prop_dict[key] = value

            except Exception as e:
                self.__logger.debug(f"解析消息属性失败: {e}")

        message_obj = MqttMessage(
            topic=topic,
            payload=msg.payload,
            qos=msg.qos,
            retain=msg.retain,
            properties=prop_dict,
            raw_properties=raw_props
        )

        with self._data_lock:
            if topic not in self._data_dict:
                self._data_dict[topic] = []
            self._data_dict[topic].append(message_obj)
            if len(self._data_dict[topic]) > self.data_length:
                self._data_dict[topic] = self._data_dict[topic][-self.data_length:]

    def __on_message(self, client, userdata, msg):
        self._cache_message(msg)

    def __run(self):
        """在独立线程中运行网络循环(非阻塞). """
        if self.protocol in (self.__protocol[3], self.__protocol[4]):
            self.__client.on_connect = self.__on_connect_v3
            self.__client.on_disconnect = self.__on_disconnect_v3
        elif self.protocol == self.__protocol[5]:
            self.__client.on_connect = self.__on_connect_v5
            self.__client.on_disconnect = self.__on_disconnect_v5

        self.__client.on_message = self.__on_message

        if self.user:
            self.__client.username_pw_set(self.user, password=self.passwd)

        try:
            self.__client.connect(self.host, port=self.port, keepalive=60)
            self.__logger.info("MQTT服务器连接中...")
            self.__client.loop_start()
        except Exception as e:
            self.__logger.error(f"连接或启动循环失败: {e}")
            self.bool_con_success = False
            # **修复**: 不再抛出异常，线程正常结束，主线程可通过 bool_con_success 检查状态

    # ---------- 订阅/取消订阅 ----------
    def subscribe(self, subtopic: str, func=None, use_cache: bool = True,
                  qos: Literal[0, 1, 2] = 0,
                  properties: Optional[Dict[str, Any]] = None):
        """
        订阅信息.

        如果 func 为 None, 则使用默认回调 self.__on_message, 消息可通过 getdata() 获取.

        func 函数参数定义 (client, userdata, msg)
            - client -- Client 端实例
            - userdata -- 私人用户数据
            - msg -- MQTTMessage 实例

        :param subtopic: 主题(可含通配符)
        :param func: 自定义回调函数
        :param use_cache: 是否同时存入内部缓存(可通过 getdata() 获取)
        :param qos: 订阅服务质量等级 (0, 1, 2)
        :param properties: MQTT 5.0 订阅属性(键名支持标准名或友好名), 例如 {"SubscriptionIdentifier": 123}
        """
        props = None
        if self.protocol == self.__protocol[5] and properties:
            props = self._create_properties(PacketTypes.SUBSCRIBE, properties)

        if func is None:
            callback = self.__on_message
        else:
            if use_cache:
                def wrapper(client, userdata, msg):
                    self._cache_message(msg)
                    func(client, userdata, msg)
                callback = wrapper
            else:
                callback = func

        self.__client.message_callback_add(subtopic, callback)
        # **修复**: 传入 qos 参数
        if props:
            self.__client.subscribe(subtopic, qos=qos, options=None, properties=props)
        else:
            self.__client.subscribe(subtopic, qos=qos)
        self.__logger.info(f"订阅主题: `{subtopic}`, qos={qos}")

    def unsubscribe(self, subtopic, properties: Optional[Dict[str, Any]] = None):
        """
        取消订阅信息

        :param subtopic: 主题
        :param properties: MQTT 5.0 取消订阅属性(可选)
        """
        props = None
        if self.protocol == self.__protocol[5] and properties:
            props = self._create_properties(PacketTypes.UNSUBSCRIBE, properties)

        if props:
            self.__client.unsubscribe(subtopic, properties=props)
        else:
            self.__client.unsubscribe(subtopic)
        self.__logger.info(f"取消订阅主题: `{subtopic}`")

    # ---------- 发布消息 ----------
    @vargs({"qos": {0, 1, 2}})
    def publish(self, topic: str, msg: str, qos: Literal[0, 1, 2] = 0,
                retain: bool = False, properties: Optional[Dict[str, Any]] = None,
                bool_log: bool = True):
        """
        发布信息到指定的MQTT主题.

        + qos: 0/1/2, 服务质量等级
        + retain: 是否为保留消息
        + bool_log: 是否记录发送日志
        + properties: MQTT 5.0 发布属性, 支持键名(标准名或友好名)及对应类型的值.
            例如:
                {
                    "message_expiry": 3600,
                    "content_type": "application/json",
                    "user_property": {"key1": "val1", "key2": "val2"},
                    "CorrelationData": b"123"
                }
            所有属性均会正确传递给 paho 库.

        :param topic: 主题
        :param msg: 消息内容(字符串)
        :param qos: QoS
        :param retain: 保留标志
        :param properties: 属性字典(仅 V5 有效)
        :param bool_log: 是否记录日志
        """
        props = None
        if self.protocol == self.__protocol[5] and properties:
            props = self._create_properties(PacketTypes.PUBLISH, properties)

        if props:
            result = self.__client.publish(topic, msg, qos, retain, properties=props)
        else:
            result = self.__client.publish(topic, msg, qos, retain)

        status = result[0]
        if status == 0 and bool_log:
            self.__logger.debug(f"发送成功 TOPIC[`{topic}`]  MSG[`{repr(msg)}`]")
        elif bool_log:
            self.__logger.error(f"发送失败 TOPIC[`{topic}`]  返回码: {result}")

    # ---------- 数据获取 ----------
    def getdata(self, topic: Optional[str] = None, index: int = 0,
                bool_del: bool = True, bool_all: bool = False) -> Union[Optional[MqttMessage], List[MqttMessage], Dict[str, List[MqttMessage]]]:
        """
        获取接收到的数据(线程安全).

        **返回值类型说明**：
        - 当 `topic` 非 None 且 `bool_all=False` 时，返回单个 `MqttMessage` 对象或 `None`（无数据）。
        - 当 `topic` 非 None 且 `bool_all=True` 时，返回该主题下的所有消息列表（可能为空列表）。
        - 当 `topic` 为 None 且 `bool_all=True` 时，返回一个字典，键为主题，值为该主题的消息列表。
        - 当 `topic` 为 None 且 `bool_all=False` 时，抛出 `ValueError`。

        返回的 `MqttMessage` 对象支持索引解包为 `(topic, payload, qos, retain, properties, timestamp)`。

        :param topic: 要获取数据的主题。若为 None，则必须设置 bool_all=True。
        :param index: 当 bool_all=False 时，获取列表中的第 index 条消息(默认 0)。
        :param bool_del: 获取数据时是否从缓存中删除。
        :param bool_all: 是否获取该主题下的全部消息(若 topic 为 None，则获取所有主题的全部数据)。
        :return: 单个 MqttMessage、消息列表或字典，具体见上述说明。
        """
        with self._data_lock:
            if topic is not None:
                if topic not in self._data_dict:
                    return None
                data_list = self._data_dict[topic]
                if not data_list:
                    return None
                if not bool_all:
                    if bool_del:
                        return data_list.pop(index)
                    else:
                        return data_list[index]
                else:
                    if bool_del:
                        temp = data_list[:]
                        self._data_dict[topic] = []
                        return temp
                    else:
                        return data_list
            else:
                if not bool_all:
                    raise ValueError("如果不指定主题且不获取所有数据, 操作不明确. 请指定主题或设置 bool_all=True. ")
                if bool_del:
                    temp = self._data_dict.copy()
                    self._data_dict.clear()
                    return temp
                else:
                    return self._data_dict.copy()

    def clear_data(self, topic: Optional[str] = None):
        """清空缓存数据(线程安全). """
        with self._data_lock:
            if topic is None:
                self._data_dict.clear()
            elif topic in self._data_dict:
                self._data_dict[topic] = []

    # ---------- 属性构建工具 ----------
    def _create_properties(self, packet_type: int, prop_dict: Dict[str, Any]) -> Properties:
        """
        将友好名称的字典转换为 paho 的 Properties 对象。
        现在为实例方法，以便访问 logger。
        """
        props = Properties(packet_type)
        user_prop_pairs = []  # 收集所有 UserProperty 键值对

        for raw_key, value in prop_dict.items():
            # 友好名转换
            key = self.FRIENDLY_NAMES.get(raw_key, raw_key)
            if key not in self.PROPERTY_NAMES:
                # **修复**: 对未知键发出警告
                self.__logger.warning(f"未知的 MQTT 属性键: '{raw_key}' (映射为 '{key}'), 已忽略")
                continue

            if key == "UserProperty":
                # 支持 dict 或 list of tuples
                if isinstance(value, dict):
                    for k, v in value.items():
                        user_prop_pairs.append((str(k), str(v)))
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, (tuple, list)) and len(item) == 2:
                            user_prop_pairs.append((str(item[0]), str(item[1])))
                # 其他类型忽略
            else:
                try:
                    setattr(props, key, value)
                except Exception as e:
                    # **修复**: 记录 debug 级别日志
                    self.__logger.debug(f"设置属性 {key}={value} 失败: {e}")

        # 一次性将列表赋值给 UserProperty
        if user_prop_pairs:
            props.UserProperty = user_prop_pairs

        return props
