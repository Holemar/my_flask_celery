# -*- coding:utf-8 -*-
import time
import uuid
import logging
from abc import ABC

import settings
from adam.celery_base_task import BaseTask


logger = logging.getLogger(__name__)


class NotifyTask(BaseTask, ABC):
    name = "my_celery_mq.tasks.master_notify"

    def run(self):
        _id = uuid.uuid4()
        _t = int(time.time())
        retries = int(self.request.retries)  # 重试次数
        logger.info(f'NotifyTask task run id: {_id}, ts:{_t}, 重试次数: {retries}')
        # 观察异常情况、重试情况
        if retries <= 2:
            a = 1 / 0
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

