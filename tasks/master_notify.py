# -*- coding:utf-8 -*-
import time
import uuid
import logging
from abc import ABC

from celery import current_app, Task
import settings


logger = logging.getLogger(__name__)


class NotifyTask(Task, ABC):
    name = "my_celery_mq.tasks.master_notify"
    max_retries = 3
    default_retry_delay = 1

    # 任务开始前执行
    def before_start(self, task_id, args, kwargs):
        logger.info(f'NotifyTask before_start task_id: {task_id}, args: {args}, kwargs: {kwargs}')

    # 任务失败时执行
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f'NotifyTask on_failure task_id: {task_id}, args: {args}, kwargs: {kwargs}, 错误的类型 exc: {exc}, 异常详细信息 einfo: {einfo}')

    # 任务成功时执行
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f'NotifyTask on_success task_id: {task_id}, args: {args}, kwargs: {kwargs}, 任务执行结果 retval: {retval}')

    # 任务重试时执行
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.error(f'NotifyTask on_retry task_id: {task_id}, args: {args}, kwargs: {kwargs}, 错误的类型 exc: {exc}, 异常详细信息 einfo: {einfo}')

    # 当任务执行完毕
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        logger.info(f'NotifyTask after_return task_id: {task_id}, args: {args}, kwargs: {kwargs}, 任务执行状态 status: {status}, 任务执行结果 retval: {retval}, 异常详细信息 einfo: {einfo}')

    def __call__(self, *args, **kwargs):
        logger.info(f'NotifyTask task __call__ args: {args}, kwargs:{kwargs}')
        return super().__call__(*args, **kwargs)

    def run(self):
        _id = uuid.uuid4()
        _t = int(time.time())
        retries = int(self.request.retries)  # 重试次数
        logger.info(f'NotifyTask task run id: {_id}, ts:{_t}, 重试次数: {retries}')
        # 观察异常情况、重试情况
        if retries <= 2:
            raise self.retry(exc=RuntimeError('看看异常怎么处理'), countdown=self.default_retry_delay, max_retries=self.max_retries)
        else:
            return True


''' NotifyTask.run 函数可以代替下面写法
@current_app.task(base=NotifyTask, name='my_celery_mq.tasks.master_notify', queue=settings.NOTIFY_TASK_QUEUE, bind=True)  # , priority=0)
def process(self):
    _id = uuid.uuid4()
    _t = int(time.time())
    retries = int(self.request.retries)  # 重试次数
    logger.info(f'master_notify task id: {_id}, ts:{_t}, 重试次数: {retries}')
    # 观察异常情况、重试情况
    if retries <= 2:
        raise self.retry(exc=RuntimeError('看看异常怎么处理'), countdown=self.default_retry_delay, max_retries=self.max_retries)
    else:
        return True
# '''

