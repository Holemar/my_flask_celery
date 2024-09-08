# -*- coding: utf-8 -*-
import os
import json
import logging
import inspect
import importlib

from celery import current_app, Task
from celery.schedules import crontab
from adam.utils.config_util import config


logger = logging.getLogger(__name__)


def get_value(item):
    keys = dir(item)
    values = {}
    for k in keys:
        v = getattr(item, k)
        if not isinstance(v, (int, str, bool, float, list, dict)):
            v = repr(v)
        values[k] = v
    return values


def get_pending_msg():
    """获取正在准备执行的worker任务数量"""
    from adam.flask_app import current_app as app
    total_msg = 0  # 总任务数
    queues = config.ALL_QUEUES
    messages = {key: 0 for key in queues}  # 各队列的任务数
    for key in queues:
        queue_info2 = app.celery.connection().channel().queue_declare(key, passive=True)
        message_count = queue_info2.message_count
        total_msg += message_count
        messages[key] = message_count

    """
    # 查看任务状态
    connection = app.celery.connection()
    logger.warning(f'connection:{connection}, {get_value(connection)}')
    channel = connection.channel()
    logger.warning(f'channel:{channel}, {get_value(channel)}')
    logger.warning(f'queues_collection:{channel.queues_collection}, {get_value(channel.queues_collection)}')
    logger.warning(f'routing_collection:{channel.routing_collection}, {get_value(channel.routing_collection)}')
    logger.warning(f'state:{channel.state}, {get_value(channel.state)}')
    events = app.celery.events
    logger.warning(f'events:{events}, {get_value(events)}')


    # @see: celery.app.control.Inspect
    control = app.celery.control
    # control = current_app.control  # 连接失败
    inspect = control.inspect()
    state = app.celery.events.State()

    task = state.tasks
    logger.warning(f'task:{dict(task)}')

    # 查看worker状态。返回工作节点的统计信息，如活动任务数、完成任务数等
    worker_stats = inspect.stats()
    logger.warning(f'worker_stats:{worker_stats}')
    # 查看当前运行的任务
    active_tasks = inspect.active()
    logger.warning(f'active_tasks:{active_tasks}')
    # 查看当前接收但未执行的任务(已预订任务的信息)
    reserved_tasks = inspect.reserved()
    logger.warning(f'reserved_tasks:{reserved_tasks}')
    # 查看queues(活动队列的信息)
    active_queues = inspect.active_queues()
    logger.warning(f'active_queues:{active_queues}')
    # 检查工作节点的在线状态
    worker_status = control.ping(timeout=1)
    logger.warning(f'worker_status:{worker_status}')
    # 返回已注册任务的信息
    registered_tasks = inspect.registered()
    logger.warning(f'registered_tasks:{registered_tasks}')
    # 返回计划中的任务的信息
    scheduled_tasks = inspect.scheduled()
    logger.warning(f'scheduled_tasks:{scheduled_tasks}')
    # 返回已撤销任务的信息
    revoked_tasks = inspect.revoked()
    logger.warning(f'revoked_tasks:{revoked_tasks}')
    # 查询worker的配置信息
    worker_conf = inspect.conf()
    logger.warning(f'worker_conf:{worker_conf}')
    # 返回工作节点的报告信息
    worker_reports = inspect.report()
    logger.warning(f'worker_reports:{worker_reports}')
    # """


    """
    broker_url = app.celery.conf.broker_url
    if broker_url.startswith('mongodb://'):
        db = get_mongo_db(broker_url)
        # total_msg = db.messages.count_documents()
        for key in queues:
            size = db.messages.count_documents({"queue": key})
            total_msg += size
            messages[key] = size
    elif broker_url.startswith('redis://'):
        conn = get_redis_client(broker_url)
        for key in queues:
            size = conn.llen(key)
            total_msg += size
            messages[key] = size
    # 使用 RabbitMQ
    elif broker_url.startswith(('amqp://', 'pyamqp://', 'rpc://')):
        pass  # todo: 未实现
    """

    return total_msg, messages



'''
from celery import Celery

app = Celery('your_celery_app_name')
inspect = app.control.inspect([worker])

# 检查工作节点的在线状态
worker_status = inspect.ping()

# 返回工作节点的统计信息，如活动任务数、完成任务数等
worker_stats = inspect.stats()

# 返回活动任务的信息
active_tasks = inspect.active()

# 返回已注册任务的信息
registered_tasks = inspect.registered()

# 返回计划中的任务的信息
scheduled_tasks = inspect.scheduled()

# 返回已预订任务的信息
reserved_tasks = inspect.reserved()

# 返回已撤销任务的信息
revoked_tasks = inspect.revoked()

# 返回活动队列的信息
active_queues = inspect.active_queues()

# 查询worker的配置信息
worker_conf = inspect.conf()

# 返回工作节点的报告信息
worker_reports = inspect.report()

# 查询特定任务的信息
task_info = inspect.query_task(task_id)




from celery import Celery

app = Celery('your_celery_app_name')

result = app.AsyncResult(task_id)

# 获取任务状态
state = result.state

# 获取任务结果
result = result.result

# 返回一个布尔值，检查任务是否已经完成
is_ready = result.ready()

# 返回一个布尔值，检查任务是否成功完成
is_successful = result.successful()

# 返回一个布尔值，检查任务是否执行失败
is_failed = result.failed()

# 返回一个字符串，获取任务的错误追溯信息
traceback = result.traceback

# 返回一个AsyncResult对象，获取任务的父任务
parent_task = result.parent

# 返回一个列表，包含任务的子任务的AsyncResult对象，获取任务的子任务
child_tasks = result.children

# 返回一个字典，获取任务的其他信息
info = result.info

# 获取任务的结果，可以指定超时时间和是否向上传播异常
result = result.get(timeout=10, propagate=False)

# 忘记任务，将任务从结果存储中删除。一旦任务被遗忘，将无法查询其状态和结果
result.forget()

'''