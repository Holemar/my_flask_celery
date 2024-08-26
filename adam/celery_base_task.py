# -*- coding:utf-8 -*-
import os
import time
import socket
import logging

import requests
from celery import current_app, Task


logger = logging.getLogger(__name__)

TASK_TIMEOUT = float(os.environ.get('TASK_TIMEOUT') or 10)  # 异步任务执行超时时间
TASK_MAX_RETRIES = int(os.environ.get('TASK_MAX_RETRIES') or 3)  # 任务重试次数
TASK_RETRY_DELAY = int(os.environ.get('TASK_RETRY_DELAY') or 3)  # 任务重试时，延迟多久执行(单位:秒，每次指数增涨)


class BaseTask(current_app.Task):
    max_retries = 3  # 最大重试次数
    default_retry_delay = 1  # 默认重试间隔(秒)

    # 任务开始前执行
    def before_start(self, task_id, args, kwargs):
        logger.debug(f'BaseTask before_start task_id: {task_id}, args: {args}, kwargs: {kwargs}')

    # 任务失败时执行
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f'BaseTask on_failure task_id: {task_id}, args: {args}, kwargs: {kwargs}, 错误的类型 exc: {exc}, 异常详细信息 einfo: {einfo}')

    # 任务成功时执行
    def on_success(self, retval, task_id, args, kwargs):
        logger.debug(f'BaseTask on_success task_id: {task_id}, args: {args}, kwargs: {kwargs}, 任务执行结果 retval: {retval}')

    # 任务重试时执行
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(f'BaseTask on_retry task_id: {task_id}, args: {args}, kwargs: {kwargs}, 错误的类型 exc: {exc}, 异常详细信息 einfo: {einfo}')

    # 当任务执行完毕
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        logger.debug(f'BaseTask after_return task_id: {task_id}, args: {args}, kwargs: {kwargs}, 任务执行状态 status: {status}, 任务执行结果 retval: {retval}, 异常详细信息 einfo: {einfo}')

    def __call__(self, *args, **kwargs):
        logger.debug(f'BaseTask task __call__ args: {args}, kwargs:{kwargs}')
        start_time = time.time()
        # 让所有的任务函数，都能直接使用 flask.current_app
        from .flask_app import current_app as app
        task_name = self.__module__ or self.name
        try:
            with app.app_context():
                return super().__call__(*args, **kwargs)
        except Exception as err:
            retries = self.request.retries
            countdown = TASK_RETRY_DELAY ** (retries + 1)  # 延迟多久再重试
            # 请求超时,登录异常,不记录error日志
            if isinstance(err, (socket.timeout, requests.exceptions.ReadTimeout, TimeoutError,
                                ConnectionResetError, AttributeError)):
                logger.warning("执行任务出错: %s:%s: %s", task_name, (args[1:], kwargs), err)
            else:
                logger.exception("执行任务出错: %s:%s: %s", task_name, (args[1:], kwargs), err)
            raise self.retry(exc=err, countdown=countdown, max_retries=TASK_MAX_RETRIES)
        finally:
            # 超时日志
            duration = time.time() - start_time
            _args = args[1:] if self else args
            if duration >= TASK_TIMEOUT:  # 耗时太长
                logger.warning('任务耗时太长:%.4f秒, task:%s, 参数: %s', duration, task_name, (_args, kwargs))
            else:
                logger.debug('执行任务耗时:%.4f秒, task:%s, 参数: %s', duration, task_name, (_args, kwargs))



"""
执行顺序：
1. before_start
2. __call__
3. run (或者是 @current_app.task 修饰的函数)
4. on_success / on_failure / on_retry
5. after_return (retry时没有返回值，所以不触发这事件)
"""

