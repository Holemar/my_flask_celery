# -*- coding:utf-8 -*-
import logging
from celery import current_app
import settings

logger = logging.getLogger(__name__)


@current_app.task(name='my_celery_mq.tasks.fetch', queue=settings.FETCH_TASK_QUEUE, bind=True)  # , priority=0)
def process(self, msg_id, ts):
    """
    执行子任务
    """
    logger.info(f"Start fetch task for message: {msg_id}, ts: {ts}")

