# -*- coding:utf-8 -*-
import logging
from celery import current_app

logger = logging.getLogger(__name__)


@current_app.task(name='my_celery_mq.tasks.ping', priority=9)
def process():
    """
    ping
    """
    logger.info('ping task finished.')
