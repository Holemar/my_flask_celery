# -*- coding:utf-8 -*-
import logging
from celery import current_app
from celery.schedules import crontab
import settings

logger = logging.getLogger(__name__)

# 约定每个定时任务文件都需要定义一个 SCHEDULE 变量，用于定义定时任务(不定义这个变量则不认为是定时任务)
SCHEDULE = {
    # "schedule": 10,  # 每 10 秒执行一次，也可以用 crontab 函数定义定时任务
    'schedule': crontab(minute='*/1'),  # 每分钟执行一次
    "args": (),  # 任务函数参数
    "kwargs": {},  # 任务函数关键字参数
    "options": {},  # 任务选项，比如 定义queue
}


# 约定每个异步任务，都需要定义一个 process 函数，作为任务的执行函数。也可以继承 CeleryTask 类，重写 run 方法。
@current_app.task(name=f'{settings.APP_NAME}.{__name__}', bind=True)
def process(self):
    """
    ping
    """
    logger.info('ping task finished.')
