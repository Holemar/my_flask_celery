# -*- coding: utf-8 -*-
"""
使用 pulsar 作为消息队列的工具类
"""

import logging

import pulsar
from .config_util import config
from .bson_util import bson_dumps, bson_loads

LOGGER = logging.getLogger(__name__)

CLIENT = None
PRODUCER = None
CONSUMER = None


def get_client():
    """获取 Pulsar 客户端(创建 Client 相对来说是比较“重”的操作，官方建议在应用的整个生命周期内只创建一个 Client 实例)"""
    global CLIENT
    if CLIENT is None:
        CLIENT = pulsar.Client(config.PULSAR_URL)
    return CLIENT


def get_producer():
    """获取 Pulsar 生产者"""
    global PRODUCER
    if PRODUCER is None:
        client = get_client()
        PRODUCER = client.create_producer(config.PULSAR_TOPIC)
    return PRODUCER


def get_consumer():
    """获取 Pulsar 消费者"""
    global CONSUMER
    if CONSUMER is None:
        client = get_client()
        CONSUMER = client.subscribe(config.PULSAR_TOPIC, 'my-sub',
                                    consumer_type=pulsar.ConsumerType.Failover)
    return CONSUMER


def send_message(task_name, args=None, kwargs=None, user_id=None, company_id=None, queue=None, priority=0):
    """发送消息到 Pulsar 队列
    约定的消息结构：
    {
        'task': '任务名称',
        'args': [],  # 任务参数
        'kwargs': {},  # 任务参数
        'queue': '队列名称',
        'priority': 0,  # 优先级(值越高表示任务优先级越高，通常推荐范围是 0 到 255 的整数值，不写则默认为 0)
        'user_id': None,  # str 类型的 用户id
        'company_id': None,  # str 类型的 公司id
    }
    """
    message = bson_dumps({
        'task': task_name,
        'args': args or [],
        'kwargs': kwargs or {},
        'user_id': user_id,
        'company_id': company_id,
        'queue': queue,
        'priority': priority,
    })
    producer = get_producer()
    result = producer.send(message.encode('utf-8'))
    # producer.close()
    return result


def receive_message(timeout_millis=None):
    """接收 Pulsar 消息队列中的消息
    timeout_millis: int, optional
        If specified, the receiver will raise an exception if a message is not available within the timeout.
    """
    consumer = get_consumer()
    msg = None
    try:
        msg = consumer.receive(timeout_millis=timeout_millis)
        if msg is None:
            return None
        message = msg.data().decode('utf-8')
        data = bson_loads(message)
        # 消息处理成功后，发送确认，避免重复消费
        consumer.acknowledge(msg)
        return data
    except pulsar.Timeout:
        # 若超时，则返回 None
        return None
    except Exception as e:
        LOGGER.exception(f'Pulsar message processing error: {e}')
        # 若处理过程中出错，负确认，Broker 将在超时后重发消息
        consumer.negative_acknowledge(msg)


def run_task(data):
    """执行 Pulsar 队列中的任务"""
    from ..celery_base_task import BaseTask
    task_name = data.get('task')
    args = data.get('args')
    kwargs = data.get('kwargs')
    user_id = data.get('user_id')
    company_id = data.get('company_id')
    queue = data.get('queue')
    priority = data.get('priority')
    # 处理任务
    tasks = BaseTask.tasks
    task = tasks.get(task_name)
    if task is None:
        LOGGER.error(f'Task {task_name} not found')
        return None
    result = task.apply_async(args=args, kwargs=kwargs, queue=queue, priority=priority)
    # 处理完成后，返回处理结果
    return result
