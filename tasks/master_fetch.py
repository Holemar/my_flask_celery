# -*- coding:utf-8 -*-
import uuid
import logging
from datetime import datetime
from celery.schedules import crontab

import settings
from celery import current_app
from tasks.fetch import process as fetch_task
from tasks.master_notify import NotifyTask

logger = logging.getLogger(__name__)


# 约定每个定时任务文件都需要定义一个 SCHEDULE 变量，用于定义定时任务(不定义这个变量则不认为是定时任务)
SCHEDULE = {
    "schedule": 5,  # 每 5 秒执行一次，也可以用 crontab 函数定义定时任务
    # 'schedule': crontab(minute='*/1'),  # 每分钟执行一次
}


# 定义任务函数，并使用celery.task装饰器进行装饰； task()参数：
# name:可以显示指定任务的名字；
# serializer：指定序列化的方法；
# bind:一个bool值，设置是否绑定一个task的实例，如果把绑定，task实例会作为参数传递到任务方法中，可以访问task实例的所有的属性，即前面反序列化中那些属性
@current_app.task(name=f'{settings.APP_NAME}.{__name__}', queue=settings.FETCH_TASK_QUEUE, bind=True)  # , priority=0)
def process(self):
    """
    抛出子任务
    :param self: 任务实例( bind=True 时出现)
    使用self.request访问相关的属性，如：self.request.id, self.request.args, self.request.kwargs
    retries = int(self.request.retries)  # 重试次数
    """
    _id = uuid.uuid4()  # 测试这两种类型的异步任务传参
    _t = datetime.now()
    logger.info(f'master_fetch task id: {_id}, ts:{_t}')

    fetch_task.delay([_id], _t)  # 调用 process 函数定义的异步任务
    # NotifyTask().delay([_id], _t)  # 调用继承 CeleryTask 类异步任务(正常写法)
    NotifyTask.delay([_id], _t)  # 调用继承 CeleryTask 类异步任务(基类添加的使用方式，静态函数)
    # NotifyTask.sync([_id], _t)  # 同步调用继承 CeleryTask 类异步任务(基类添加的使用方式，静态函数)，可以直接获取 run 方法的返回值

    # task.delay():这是apply_async方法的别名,但接受的参数较为简单；
    # task.apply_async(args=[arg1, arg2], kwargs={key:value, key:value},
    #     countdown : 设置该任务等待一段时间再执行，单位为s；
    #     eta : 定义任务的开始时间；eta=time.time()+10;
    #     expires : 设置任务时间，任务在过期时间后还没有执行则被丢弃；
    #     retry : 如果任务失败后, 是否重试;使用true或false，默认为true
    #     shadow：重新指定任务的名字str，覆盖其在日志中使用的任务名称；
    #     retry_policy : { # 重试策略.
    #        'max_retries': 3, # 最大重试次数, 默认为 3 次.
    #        'interval_start': 0, # 第一次重试的延迟时间。重试等待的时间间隔秒数, 默认为 0 , 表示直接重试不等待.
    #        'interval_step': 0.5, # 重试间隔递增步长。每次重试让重试间隔增加的秒数, 可以是数字或浮点数, 默认为 0.2
    #        'interval_max': 3, # 重试间隔最大的秒数, 即 通过 interval_step 增大到多少秒之后, 就不在增加了, 可以是数字或者浮点数, 默认为 0.2
    #     },
    # )

    # send_task():可以发送未被注册的异步任务，即没有被celery.task装饰的任务；
    # celery_app.send_task('tasks.add', args=[3,4])  # 参数基本和apply_async函数一样
    # 但是send_task在发送的时候是不会检查tasks.add函数是否存在的，即使为空也会发送成功
    return True

