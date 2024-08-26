# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import socket
import logging
import inspect
import importlib

from celery import Celery
from celery import current_app, Task
from celery.schedules import crontab

from models.work_status import WorkStatus
from .import_util import import_submodules, discovery_items_in_package
from .str_util import base64_decode, decode2str
from .json_util import load_json
from .config_util import config
from .db_util import get_mongo_db, get_redis_client


# 上次写入检测信息时间，避免频繁操作
LAST_RUN = None
# beat/worker记录超时时间，beat每分钟会运行一次
TIME_OUT = 360

HOST_NAME = socket.gethostname()
PID = os.getpid()  # 当前进程ID

logger = logging.getLogger(__name__)


def custom_send_task(self, *args, **kwargs):
    """celery 发任务补丁,每个beat及worker子任务执行前都经过它"""
    logger.debug(f'celery.Celery.send_task args:{args}, kwargs:{kwargs}')
    set_run()
    return self._old_send_task(*args, **kwargs)


# 打补丁的方式来监控 beat 和 worker，虽然比较难看，但 flower 那种使用线程不断轮询的方式也不见得好多少。
# 这种方式的弊端是，一个长任务的执行中途(远远超过了这里的超时时间)，会没统计到。
if not hasattr(Celery, '_old_send_task'):
    _old_send_task = getattr(Celery, 'send_task')
    setattr(Celery, '_old_send_task', _old_send_task)
    setattr(Celery, 'send_task', custom_send_task)


'''
from celery.task import Task

def custom_task_call(self, *args, **kwargs):
    """celery 执行任务补丁，主要是worker主任务执行前经过它"""
    set_run()
    return self._old_call(*args, **kwargs)

# __call__ 函数补丁，会导致出错重试机制失效，故去掉
_old_call = getattr(Task, '__call__')
setattr(Task, '_old_call', _old_call)
setattr(Task, '__call__', custom_task_call)
setattr(Task, '_Task__call__', custom_task_call)
'''


def get_argv_queue(argv):
    """获取运行参数中指定的Q值"""
    if '-Q' not in argv:
        return 'ALL_QUEUES'
    index = argv.index('-Q')
    param = argv[index + 1]
    queues = param.split(',')
    if set(queues) == set(config.ALL_QUEUES):
        return 'ALL_QUEUES'
    return param


def set_run():
    """设置运行状态
    任务需要长时间运行(超过这里设置的TIME_OUT)，则需要在过期前设置此进程的运行状态，避免任务执行太久导致误认为僵死(会有系统定时任务重启僵死进程)
    """
    global LAST_RUN, TIME_OUT
    if LAST_RUN is None or (time.time() - LAST_RUN) > (TIME_OUT / 3):
        LAST_RUN = time.time()
        # beat 正常运行
        if 'beat' in sys.argv:
            WorkStatus.now_run('celery_beat')
        # worker 正常运行
        elif 'worker' in sys.argv:
            queues = get_argv_queue(sys.argv)
            WorkStatus.now_run(f'celery_worker:{queues}:{HOST_NAME}_{PID}')


def get_workers():
    """获取worker正常运行的数量"""
    keys = WorkStatus.run_names('celery_worker:', TIME_OUT)
    result = {}
    for key in keys:
        key = decode2str(key)  # redis 返回 byte 类型，兼容一下
        queue = key.split(':')[1]
        if queue not in result:
            result[queue] = 1
        else:
            result[queue] += 1
    return result


def get_beat():
    """获取beat运行状态，运行正常则返回OK，否则返回ERROR"""
    res = WorkStatus.is_run('celery_beat', TIME_OUT)
    return 'OK' if res else 'ERROR'


def set_base_task():
    """重新赋予基类"""
    from ..celery_base_task import BaseTask
    current_app.Task = BaseTask


def load_task(path):
    """
    load class tasks
    """
    set_base_task()  # 重新赋予基类，必须在task注册之前，才可以使task继承基类

    package_name = path.replace('/', '.')
    package = importlib.import_module(package_name)
    customize_tasks = discovery_items_in_package(package,
                                                 lambda x: inspect.isclass(x) and x != Task and issubclass(x, Task))
    for _n, _task_cls in customize_tasks:
        logger.debug('Loading Task (CLS): %s', _n)
        _task = _task_cls()
        current_app.register_task(_task)

    modules = import_submodules(path)
    for k, _cls in modules.items():
        if hasattr(_cls, 'process'):
            logger.debug('Loading Task (PRC): %s', k)
            current_app.register_task(_cls.process)


def parse_cron(cron):
    """
    parse cron format to celery cron
    http://www.nncron.ru/help/EN/working/cron-format.htm
    <Minute> <Hour> <Day_of_the_Month> <Month_of_the_Year> <Day_of_the_Week>
    """
    if not isinstance(cron, str):
        return cron
    if ' ' in cron:
        minute, hour, day_of_month, month_of_year, day_of_week = cron.split(' ')
        return crontab(minute=minute, hour=hour, day_of_month=day_of_month, day_of_week=day_of_week,
                       month_of_year=month_of_year)
    elif cron.isdigit():  # 数字表示秒数，每隔多少秒执行一次
        return int(cron)


def load_task_schedule(path):
    if not os.path.exists(path):
        return
    schedule = {}
    with open(path, 'r', encoding='utf-8') as reader:
        rules = json.load(reader)
        for r_task in rules:
            name = r_task.pop('name')
            cron = parse_cron(r_task.pop('schedule'))
            # 过滤掉下划线开头的 key，用于备注
            new_task = {k: v for k, v in r_task.items() if not k.startswith('_')}
            new_task['schedule'] = cron
            schedule[name] = new_task  # 保留原始配置(允许配置更多参数)
    current_app.conf.beat_schedule = schedule


def delete_repeat_task():
    """删除重复的任务(任务可能太久没执行完，从而再次抛出导致重复)"""
    from ..flask_app import current_app as app
    broker_url = app.celery.conf.broker_url
    queues = config.ALL_QUEUES
    limit_tasks = config.LIMIT_TASK

    if broker_url.startswith('mongodb://'):
        db = get_mongo_db(broker_url)
        for key in queues:
            size = db.messages.find({"queue": key}).count()
            # 任务数量不多的情况下，认为没有堆积
            if size < limit_tasks:
                continue
            else:
                delete_mongodb_repeat_task(db, key, size)
    elif broker_url.startswith('redis://'):
        conn = get_redis_client(broker_url)
        for key in queues:
            size = conn.llen(key)
            # 任务数量不多的情况下，认为没有堆积
            if size < limit_tasks:
                continue
            else:
                delete_redis_repeat_task(conn, key, size)
    # 使用 RabbitMQ
    elif broker_url.startswith(('amqp://', 'pyamqp://', 'rpc://')):
        pass  # todo: 未实现


def delete_redis_repeat_task(conn, queue, total):
    """删除指定queue的重复任务
    :param conn: 作为celery broker的 redis 数据库连接
    :param queue: queue 名称
    :param total: 积累的任务数量
    """
    param_set = set()
    for index in range(total):
        res = conn.lpop(queue)
        # 没有数据了
        if res is None:
            break
        # conn.lindex(key, index)
        result = load_json(res)
        body = base64_decode(result.get("body"))
        # 参数完全相同的，认为是重复子任务。
        if body in param_set:
            logger.warning('删除重复任务:%s, %s', body, res)
            continue
        # 不重复的任务，放回队列后面
        else:
            param_set.add(body)
            conn.rpush(queue, res)
        del body
        del res
        del result
    del param_set


def delete_mongodb_repeat_task(db, queue, total):
    """删除指定queue的重复任务
    :param db: 作为celery broker的 mongodb 数据库连接
    :param queue: queue 名称
    :param total: 积累的任务数量
    """
    param_set = set()
    limit = 100  # 每次处理的数量
    page = (total + limit - 1) // limit  # 共需分多少批次(分页算法的页数)
    # 分批执行。这里使用倒序页码，是为了避免正序时删除前面的导致后面分页改变
    for page_index in range(page, -1, -1):
        start_index = page_index * limit
        queue_tasks = db.messages.find({"queue": queue}).skip(start_index).limit(limit)
        delete_ids = set()
        for d in queue_tasks:
            payload = d.get('payload')
            result = load_json(payload)
            body = base64_decode(result.get("body"))
            # 参数完全相同的，认为是重复子任务。
            if body in param_set:
                logger.warning('删除重复子任务:%s, %s', body, payload)
                delete_ids.add(d.get("_id"))
        if delete_ids:
            db.messages.remove({"queue": queue, "_id": {'$in': list(delete_ids)}})


def get_pending_msg():
    """获取正在准备执行的worker任务数量"""
    from ..flask_app import current_app as app
    total_msg = 0  # 总任务数
    queues = config.ALL_QUEUES
    messages = {key: 0 for key in queues}  # 各队列的任务数
    for key in queues:
        queue_info2 = app.celery.connection().channel().queue_declare(key, passive=True)
        message_count = queue_info2.message_count
        total_msg += message_count
        messages[key] = message_count

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

