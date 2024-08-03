# -*- coding:utf-8 -*-
import logging

from celery import current_app, Task


logger = logging.getLogger(__name__)


class BaseTask(current_app.Task):
    max_retries = 3  # 最大重试次数
    default_retry_delay = 1  # 默认重试间隔(秒)

    # 任务开始前执行
    def before_start(self, task_id, args, kwargs):
        logger.info(f'BaseTask before_start task_id: {task_id}, args: {args}, kwargs: {kwargs}')

    # 任务失败时执行
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f'BaseTask on_failure task_id: {task_id}, args: {args}, kwargs: {kwargs}, 错误的类型 exc: {exc}, 异常详细信息 einfo: {einfo}')

    # 任务成功时执行
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f'BaseTask on_success task_id: {task_id}, args: {args}, kwargs: {kwargs}, 任务执行结果 retval: {retval}')

    # 任务重试时执行
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.error(f'BaseTask on_retry task_id: {task_id}, args: {args}, kwargs: {kwargs}, 错误的类型 exc: {exc}, 异常详细信息 einfo: {einfo}')

    # 当任务执行完毕
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        logger.info(f'BaseTask after_return task_id: {task_id}, args: {args}, kwargs: {kwargs}, 任务执行状态 status: {status}, 任务执行结果 retval: {retval}, 异常详细信息 einfo: {einfo}')

    def __call__(self, *args, **kwargs):
        logger.info(f'BaseTask task __call__ args: {args}, kwargs:{kwargs}')
        return super().__call__(*args, **kwargs)


'''
执行顺序：
1. before_start
2. __call__
3. run (或者是 @current_app.task 修饰的函数)
4. on_success / on_failure / on_retry
5. after_return (retry时没有返回值，所以不触发这事件)
# '''

