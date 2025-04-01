# -*- coding:utf-8 -*-
import os
import time
import socket
import logging
import asyncio
import inspect

import requests
from celery import current_app, Task


logger = logging.getLogger(__name__)

TASK_TIMEOUT = float(os.environ.get('TASK_TIMEOUT') or 10)  # 异步任务执行超时时间
TASK_MAX_RETRIES = int(os.environ.get('TASK_MAX_RETRIES') or 3)  # 任务重试次数
TASK_RETRY_DELAY = int(os.environ.get('TASK_RETRY_DELAY') or 3)  # 任务重试时，延迟多久执行(单位:秒，每次指数增涨)
TASK_COUNTDOWN = int(os.environ.get('TASK_COUNTDOWN') or 1)  # 异步任务，延迟多少秒执行


class BaseTask(current_app.Task):
    max_retries = 3  # 最大重试次数
    default_retry_delay = 1  # 默认重试间隔(秒)
    event_loop = None  # 事件循环
    tasks = {}  # 任务字典

    ''' 用到的再拿出来，没有用到的先注释掉
    def before_start(self, task_id, args, kwargs):
        """任务开始前执行"""
        logger.debug(f'BaseTask before_start task_id: {task_id}, args: {args}, kwargs: {kwargs}')

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时执行"""
        logger.error(f'BaseTask on_failure task_id: {task_id}, args: {args}, kwargs: {kwargs}, 错误的类型 exc: {exc}, 异常详细信息 einfo: {einfo}')

    def on_success(self, retval, task_id, args, kwargs):
        """任务成功时执行"""
        logger.debug(f'BaseTask on_success task_id: {task_id}, args: {args}, kwargs: {kwargs}, 任务执行结果 retval: {retval}')

    # 任务重试时执行
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """任务重试时执行"""
        logger.warning(f'BaseTask on_retry task_id: {task_id}, args: {args}, kwargs: {kwargs}, 错误的类型 exc: {exc}, 异常详细信息 einfo: {einfo}')

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """任务执行完毕"""
        logger.debug(f'BaseTask after_return task_id: {task_id}, args: {args}, kwargs: {kwargs}, 任务执行状态 status: {status}, 任务执行结果 retval: {retval}, 异常详细信息 einfo: {einfo}')
    '''

    @classmethod
    def _get_event_loop(cls):
        """获取事件循环"""
        # 创建新的事件循环，避免复用已有 loop 导致问题
        if cls.event_loop is None:
            cls.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(cls.event_loop)
        return cls.event_loop

    @classmethod
    def delay(cls, *args, **kwargs):
        """提供直接异步执行的静态函数"""
        obj = cls()
        return obj.apply_async(args=args, kwargs=kwargs, countdown=TASK_COUNTDOWN)

    @classmethod
    def sync(cls, *args, **kwargs):
        """提供直接同步执行的静态函数"""
        obj = cls()
        return obj._run_fun(obj.run, *args, **kwargs)

    @classmethod
    def _run_fun(cls, fun, *args, **kwargs):
        """执行函数"""
        # 这里先执行，是因为 inspect.iscoroutinefunction(fun) 判断不出来 async 函数，
        # 同理 inspect.isgeneratorfunction(fun) 也判断不出来 yield 生成器函数。 使用 inspect.unwrap 解包也没用。
        res = fun(*args, **kwargs)

        # async 异步函数
        if inspect.iscoroutine(res):
            # return asyncio.run(res)
            loop = cls._get_event_loop()
            return loop.run_until_complete(res)

        # yield 生成器函数(途中各 yield 语句返回的值会被拼接到一起，最后以 list 形式一起返回)
        if inspect.isgenerator(res):
            results = []
            while True:
                try:
                    value = next(res)
                    results.append(value)
                except StopIteration as e:
                    value = e.value or None
                    if value is not None:
                        results.append(value)
                    return results

        return res

    def __call__(self, *args, **kwargs):
        from .flask_app import current_app as app
        from .utils.celery_util import set_run
        logger.debug(f'BaseTask task __call__ args: {args}, kwargs:{kwargs}')
        start_time = time.time()
        # 让所有的任务函数，都能直接使用 flask.current_app
        task_name = self.__module__ or self.name
        try:
            with app.app_context():
                set_run()
                # return super().__call__(*args, **kwargs)
                return self._run_fun(super().__call__, *args, **kwargs)
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

    @classmethod
    def send_pulsar(cls, *args, user_id=None, company_id=None, queue=None, priority=0, **kwargs):
        """发送消息到 pulsar 队列"""
        from .utils.pulsar_util import send_message
        obj = cls()
        return send_message(task_name=obj.name, args=args, kwargs=kwargs, user_id=user_id, company_id=company_id,
                            queue=queue or obj.queue, priority=priority or obj.priority)



"""
执行顺序：
1. before_start
2. __call__
3. run (或者是 @current_app.task 修饰的函数)
4. on_success / on_failure / on_retry
5. after_return (retry时没有返回值，所以不触发这事件)
"""

