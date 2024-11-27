# -*- coding:utf-8 -*-
import logging
from celery import current_app
from celery.schedules import crontab
import settings

logger = logging.getLogger(__name__)


# 约定每个异步任务的函数，都需要使用 @celery.task 装饰器，作为任务的执行函数。也可以继承 CeleryTask 类，重写 run 方法。
@current_app.task(
    name=f'{settings.APP_NAME}.{__name__}',  # 约定的任务名，需确保唯一性
    bind=True,  # 绑定任务实例，使得任务可以访问任务实例的属性和方法(不绑定则函数内无法使用 self 参数)
    # 如果需要定时执行，可以设置 schedule 属性(不定义这个属性则不认为是定时任务，自动加载时约定的属性名，并非原生属性)，如：
    schedule=crontab(minute='*/1'),  # 每分钟执行一次
    # schedule=1,  # 每 10 秒执行一次，也可以用 crontab 函数定义定时任务
)
def process(self):
    """
    ping
    """
    logger.info('ping task finished.')
