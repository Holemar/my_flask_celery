# -*- coding: utf-8 -*-
import os
import json
import logging
import inspect
import importlib

from celery import Celery, current_app, Task
from celery.schedules import crontab
from utils.import_util import import_submodules, discovery_items_in_package


logger = logging.getLogger(__name__)

'''
def custom_send_task(self, *args, **kwargs):
    """celery 发任务补丁,每个beat及worker子任务执行前都经过它"""
    logger.info(f'celery.Celery.send_task args:{args}, kwargs:{kwargs}')
    return self._old_send_task(*args, **kwargs)

if not hasattr(Celery, '_old_send_task'):
    _old_send_task = getattr(Celery, 'send_task')
    setattr(Celery, '_old_send_task', _old_send_task)
    setattr(Celery, 'send_task', custom_send_task)
# '''


def set_base_task():
    """重新赋予基类"""
    from utils.celery_base_task import BaseTask
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
    with open(path, 'r') as reader:
        rules = json.load(reader)
        for r_task in rules:
            name = r_task.pop('name')
            task = r_task.pop('task')
            cron = parse_cron(r_task['cron'])
            schedule[name] = r_task  # 保留原始配置(允许配置更多参数)
            schedule[name]['task'] = task
            schedule[name]['schedule'] = cron
    current_app.conf.beat_schedule = schedule
