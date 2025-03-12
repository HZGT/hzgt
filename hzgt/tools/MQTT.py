# -*- coding: utf-8 -*-
import os
import threading
import random
import string
from logging import Logger
from typing import Literal

import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes

from ..log import set_log
from ..Decorator import vargs


def generate_random_clientid():
    part1 = ''.join(random.choices(string.ascii_letters + string.digits, k = 8))
    part2 = ''.join(random.choices(string.ascii_letters + string.digits, k = 4))
    part3 = ''.join(random.choices(string.ascii_letters + string.digits, k = 4))
    return f"{part1}-{part2}-{part3}"


"""
0x00 - 连接已接受（Connection Accepted）：表示服务器接受了客户端的连接请求, 连接建立成功
0x01 - 连接已拒绝, 不支持的协议版本（Connection Refused, Unacceptable Protocol Version）：服务器不支持客户端使用的MQTT协议版本
0x02 - 连接已拒绝, 不合格的客户端标识符（Connection Refused, Identifier Rejected）：客户端提供的标识符（Client ID）不符合服务器的要求, 可能是格式不正确或者与其他客户端冲突
0x03 - 连接已拒绝, 服务端不可用（Connection Refused, Server Unavailable）：服务器当前不可用, 无法处理客户端的连接请求
0x04 - 连接已拒绝, 无效的用户名或密码（Connection Refused, Bad User Name or Password）：客户端提供的用户名或密码无效
0x05 - 连接已拒绝, 未授权（Connection Refused, Not Authorized）：客户端没有被授权连接到服务器
"""
connection_status = {
    0: "连接成功",
    1: "连接被拒绝 - 协议版本不正确",
    2: "连接被拒绝 - 客户端标识符无效",
    3: "连接被拒绝 - 服务器不可用",
    4: "连接被拒绝 - 用户名或密码错误",
    5: "连接被拒绝 - 未授权",
    **{i: "未知返回码" for i in range(6, 256)}
}


class Mqttop:
    def __init__(self, host: str, port: int,
                 user: str = '', passwd: str = '', clientid: str = '',
                 data_length: int = 100,
                 transport: Literal["tcp", "websockets", "unix"] = "tcp", protocol: int = 3,
                 logger: Logger = None):
        """
        调用self.publish()函数发布信息

        protocol:
            - 3 -- MQTTv31
            - 4 -- MQTTv311
            - 5 -- MQTTv5

        :param host: MQTT服务器IP地址
        :param port: MQTT端口

        :param user: 选填, 账号
        :param passwd: 选填, 密码
        :param clientid: 可选, "客户端"用户名 为空将随机

        :param data_length: 缓存数据列表的长度 默认为100
        :param protocol: MQTT协议版本
        
        :param logger: 日志记录器
        """
        self.__data_dict = {}  # 接收到的数据
        self.bool_con_success = False  # 是否连接成功

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
        self.protocol = protocol
        
        if logger is None:
            self.__logger = set_log("hzgt.mqtt", os.path.join("logs", "mqtt.log"), level=2)
        else:
            self.__logger = logger

        if len(self.clientid) == 0 or self.clientid is None:
            self.__client = mqtt.Client(client_id=generate_random_clientid(), transport=transport, protocol=self.protocol)
        else:
            self.__client = mqtt.Client(client_id=self.clientid, transport=transport, protocol=self.protocol)
        self.__logger.info(f"MQTT服务器[协议版本({self.protocol})]连接信息: host[`{self.host}`] port[`{self.port}`] user[`{self.user}`] clientid[`{self.clientid}`]]")

    def __del__(self):
        """
        删除对象时调用__del__()断开连接
        """
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return exc_type, exc_val, exc_tb

    @vargs({"qos": {0, 1, 2}})
    def set_will(self, will_topic: str, will_msg: str, qos: Literal[0, 1, 2] = 0, retain: bool = False):
        """
        设置遗嘱, 需要在连接前设置

        :param will_topic: 遗嘱主题
        :param will_msg: 遗嘱信息
        :param qos: 整数类型, 代表消息的服务质量（Quality of Service）等级
        :param retain: 布尔类型, 用于指定是否将此消息设置为保留消息
        """
        self.__client.will_set(will_topic, will_msg, qos, retain)
        self.__logger.info(f"已设置遗嘱信息: will_topic[`{will_topic}`] will_msg[`{will_msg}`]")

    def start(self):
        """
        启动MQTT连接, 建议使用time.sleep(5)等待连接完成

        :return:
        """
        threading.Thread(target=self.__run, daemon=True).start()  # 开启线程防止阻塞主程序, 使用.close()函数自动关闭该线程

    def connect(self):
        """
        启动MQTT连接, 建议使用time.sleep(5)等待连接完成

        :return:
        """
        return self.start()

    def close(self):
        """
        断开MQTT连接
        """
        # 断开MQTT连接
        self.__client.disconnect()
        # 停止循环
        self.__client.loop_stop()

        if self.bool_con_success:
            self.__logger.info("MQTT连接已关闭")
        self.bool_con_success = False

    def disconnect(self):
        """
        同 self.close() 方法
        :return:
        """
        return self.close()

    # 断开连接事件
    def __on_disconnect(self, client, userdata, rc):
        """
        """
        if self.bool_con_success:
            self.__logger.info(f"MQTT连接已断开 返回码rc={rc}")
        self.bool_con_success = False

    # 连接后事件
    def __on_connect_v3(self, client, userdata, flags, rc):
        """
        """
        if rc == 0:
            # 连接成功
            self.__logger.info(f'MQTT服务器 连接成功!')
            self.bool_con_success = True
        else:
            # 连接失败并显示错误代码
            self.__logger.error(f'连接出错 rc={rc} 错误代码: {connection_status.get(rc, f"未知返回码{rc}")}')
            self.bool_con_success = False

    def __on_connect_v5(self, client, userdata, flags, rc, properties):
        """
        """
        if rc == 0:
            self.__logger.info(f'MQTT服务器 连接成功!')
            self.bool_con_success = True
            self.__logger.info(f"MQTT服务器 返回信息: {properties}")
        else:
            self.__logger.error(f'连接出错 rc={rc} 错误代码: {connection_status.get(rc, f"未知返回码{rc}")}')
            self.bool_con_success = False
            self.__logger.error(f"MQTT服务器 返回信息: {properties}")

    # 接收到数据后事件
    def __on_message(self, client, userdata, msg):
        topic = msg.topic

        datadict = {}
        try:
            user_properties = msg.properties.json().get("UserProperty", [])
            for item in user_properties:
                    k, v = item
                    datadict[k] = v
        except Exception as e:
            pass
        data = [msg.payload, msg.qos, msg.retain, datadict]

        if topic not in self.__data_dict:
            self.__data_dict[topic] = []
        self.__data_dict[topic].append(data)
        if len(self.__data_dict[topic]) >= self.data_length:
            self.__data_dict[topic] = self.__data_dict[topic][-self.data_length:]

    # 订阅主题事件
    # def __on_subscribe(client, userdata, mid, properties, rc):
    #     self.__logger.info(f"订阅主题: {userdata, mid, properties, rc}")

    # 取消订阅主题事件
    # def __on_unsubscribe(client, userdata, mid, properties):
    #     self.__logger.info(f"取消订阅主题: {properties}")

    # 发布信息事件
    # def __on_publish(client, userdata, mid, rc):
    #     self.__logger.info(f"发布信息: {rc}")

    # 启动连接
    def __run(self):
        if self.protocol in (3, 4):
            self.__client.on_connect = self.__on_connect_v3
            self.__client.on_message = self.__on_message
            self.__client.on_disconnect = self.__on_disconnect
        elif self.protocol == 5:
            self.__client.on_connect = self.__on_connect_v5

        # self.__client.on_unsubscribe = self.__on_unsubscribe
        # self.__client.on_subscribe = self.__on_subscribe

        # self.__client.on_publish = self.__on_publish

        # 设置账号密码
        if self.user:
            self.__client.username_pw_set(self.user, password=self.passwd)
        # 连接到服务器
        self.__client.connect(self.host, port=self.port, keepalive=60)
        self.__logger.info(f"MQTT服务器连接中...")
        # 守护连接状态
        self.__client.loop_forever()

    # 订阅信息
    def subscribe(self, subtopic, func=None):
        """
        订阅信息 如果 func 为 None, 则使用默认的回调函数 self.__on_message, 接收到的信息可通过self.getdata()获取

        func函数参数定义(client, userdata, msg)
            - client -- 该回调的 Client 端实例
            - userdata -- 在 Client()或 userdata_set()中设置的私人用户数据
            - msg -- MQTTMessage 的实例 包含成员 topic、payload、qos、retain 的类
        :param subtopic: 主题
        :param func: 主题接收到信息后的事件回调函数
        :return:
        """
        self.__client.subscribe(subtopic)
        if func:
            self.__client.message_callback_add(subtopic, func)
        else:
            self.__client.message_callback_add(subtopic, self.__on_message)

        self.__logger.info(f"订阅主题: `{subtopic}`")

    def unsubscribe(self, subtopic):
        """
        取消订阅信息
        :param subtopic: 主题
        :return:
        """
        self.__client.unsubscribe(subtopic)
        self.__logger.info(f"取消订阅主题: `{subtopic}`")

    # 发布消息
    @vargs({"qos": {0, 1, 2}})
    def publish(self, topic: str, msg: str, qos: Literal[0, 1, 2] = 0,
                retain: bool = False, properties: dict = None, bool_log: bool = True):
        """
        发布信息到指定的MQTT主题
        
        qos:
            - QoS 0：最多一次传递消息可能会丢失或重复, 但发送方只发送一次消息, 不进行确认和重试这种方式开销最小, 适用于对消息丢失不太敏感的场景, 例如环境监测中的非关键数据
            - QoS 1：至少一次传递消息保证至少被传递一次发送方发送消息后会等待接收方的确认, 如果没有收到确认, 会重新发送消息这增加了消息传递的可靠性, 但可能会导致消息重复
            - QoS 2：恰好一次传递这是最高的QoS等级, 保证消息恰好被传递一次, 不会丢失也不会重复发送方和接收方之间有更复杂的交互来确保这种准确性, 适用于对消息准确性要求极高的场景, 如金融交易信息默认值为0, 表示采用QoS 0等级
        retain:
            - 如果为True, MQTT服务器将保留此消息, 新订阅该主题的客户端将立即收到此消息, 即使消息是在客户端订阅之前发布的这在向新连接的客户端提供主题的初始状态时非常有用, 例如设备状态的初始值
            - 如果为False, 消息不会被保留, 只有在消息发布时已订阅该主题的客户端才能接收到消息默认值为False
        bool_log:
            - 如果为True, 当消息成功发送或失败时, 将记录一条信息日志, 包含发送的主题和消息内容
            - 如果为False, 则不进行任何日志记录默认值为True
        
        :param topic: 字符串类型, 代表发布消息的主题这是MQTT消息要发送到的目标主题, 订阅该主题的客户端将能够接收到此消息
        :param msg: 字符串类型, 需要发布的消息内容
        :param qos: 整数类型, 代表消息的服务质量（Quality of Service）等级
        :param retain: 布尔类型, 用于指定是否将此消息设置为保留消息
        :param properties: 字典类型, 可选参数, 仅MQTT协议为MQTTv5[protocol=5]时可用, 用于传递额外的元数据或特定于应用程序的信息
        :param bool_log: 布尔类型, 用于确定是否记录消息发布的日志
        :return: 
        """
        if self.protocol == 5:
            pp = Properties(PacketTypes.PUBLISH)
            for k, v in properties.items():
                pp.UserProperty = (k, v)
            result = self.__client.publish(topic, msg, qos, retain, pp)
        else:
            result = self.__client.publish(topic, msg, qos, retain)
        status = result[0]
        if status == 0 and bool_log:
            self.__logger.debug(f"发送成功 TOPIC[`{topic}`]  MSG[`{repr(msg)}`]")
        elif bool_log:
            self.__logger.error(f"发送失败 TOPIC[`{topic}`]  MSG[`{repr(msg)}`]")

    def reconnect(self):
        """
        尝试重连

        :return: None
        """
        self.close()
        self.start()

    def getdata(self, topic=None, index: int = 0, bool_del: bool = True, bool_all: bool = False):
        """
        获取接收到的数据

        :param topic: 要获取数据的主题, 如果为None则获取所有主题的数据（如果适用）
        :param index: 获取的数据的索引, 默认为0
        :param bool_del: 获取数据时是否删除数据
        :param bool_all: 是否获取所有数据
        :return: list或bytes或dict: 根据情况返回bytes类型的数据或者数据列表或者字典
        """
        if topic is not None and topic in self.__data_dict:
            data_list = self.__data_dict[topic]
            if data_list:
                if not bool_all:  # 获取单个数据
                    if bool_del:  # 获取数据并删除
                        return data_list.pop(index)
                    else:  # 获取数据但不删除
                        return data_list[index]
                else:  # 获取所有数据
                    if bool_del:  # 获取数据并删除
                        temp = data_list
                        self.__data_dict[topic] = []
                        return temp
                    else:  # 获取数据但不删除
                        return data_list
            else:
                return None
        elif topic is None:
            if not bool_all:
                raise ValueError("如果不指定主题且不获取所有数据, 操作不明确, 请指定主题或者设置bool_all为True")
            if bool_del:
                temp = self.__data_dict
                self.__data_dict = {}
                return temp
            else:
                return self.__data_dict
        else:
            return None

