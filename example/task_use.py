# -*- coding:utf-8 -*-
import time
import uuid
import logging

from celery import current_app
from celery.schedules import crontab

import settings
from adam.celery_base_task import BaseTask

logger = logging.getLogger(__name__)


# 这里是继承 CeleryTask 类的异步任务写法，需要重写 run 方法。
class NotifyTask(BaseTask):
    name = f'{settings.APP_NAME}.{__name__}.NotifyTask'  # 约定的任务名，需确保唯一性
    queue = settings.NOTIFY_TASK_QUEUE  # 定义任务所在的 queue，不定义则使用默认 queue
    # 如果需要定时执行，可以设置 schedule 属性(不定义这个属性则不认为是定时任务，自动加载时约定的属性名，并非原生属性)，如：
    schedule = crontab(minute='*/1')  # 每分钟执行一次
    # schedule = 10  # 每 10 秒执行一次

    def run(self, _id=None, _t=None):
        _id = _id or uuid.uuid4()
        _t = _t or int(time.time())
        retries = int(self.request.retries)  # 重试次数
        logger.info(f'NotifyTask task run id: {_id}, ts:{_t}, 重试次数: {retries}')

        # 异步任务的调用1 (使用 process 函数写法的异步任务)
        from tasks.ping import process as fetch_task
        fetch_task.delay([_id], _t)  # 异步调用(不能直接获取结果)
        fetch_task([_id], _t)  # 同步调用，可以直接获取函数的返回值

        # 异步任务的调用2 (继承 CeleryTask 类写法的异步任务)
        from tasks.etl_convert import ConvertTask
        ConvertTask().delay([_id], _t)  # 异步调用(原生写法)
        ConvertTask.delay([_id], _t)  # 异步调用(基类添加的使用方式，静态函数)(不能直接获取结果)
        ConvertTask.sync([_id], _t)  # 同步调用(基类添加的使用方式，静态函数)，可以直接获取 run 方法的返回值

        return True
        # if retries <= 2: a = 1 / 0  # 观察异常情况、重试情况


# ''' NotifyTask.run 函数可以代替下面写法
@current_app.task(
    # base=NotifyTask,
    bind=True,
    name=f'{settings.APP_NAME}.{__name__}.notify_process',
    queue=settings.NOTIFY_TASK_QUEUE,  # 定义队列名称
    # schedule=10,  # 每 10 秒执行一次
    schedule=crontab(minute='*/1')  # 每分钟执行一次
)
def notify_process(self, ids=None, ts=None):
    _id = ids or uuid.uuid4()
    _t = ts or int(time.time())
    retries = int(self.request.retries)  # 重试次数
    logger.info(f'master_notify task id: {_id}, ts:{_t}, 重试次数: {retries}')

