# -*- coding: utf-8 -*-
import os

VERSION = '1.0.0'
APP_NAME = os.environ.get('APP_NAME', 'my_flask_celery')

# debug=true 时，程序修改后 api 服务会自动重启， log 也会变成 debug 级别(默认 info 级别)
DEBUG = os.environ.get('DEBUG', '').lower() in ('true', '1')

CURRENT_DIR, _ = os.path.split(os.path.abspath(__file__))
BASE_DIR = CURRENT_DIR or os.getcwd()  # 当前目录

MONITOR_USERNAME = os.environ.get('MONITOR_USERNAME', 'admin')
MONITOR_PASSWORD = os.environ.get('MONITOR_PASSWORD', 'password123456')

#  中间件，使用 RabbitMQ，pyamqp://username:Password@HOST:Port//v_host
# DEFAULT_BROKER = 'amqp://development:password123456@134.175.100.239:5672//development_host'
# DEFAULT_BROKER = 'redis://:@127.0.0.1:6379/1'  # redis://username:password@host:port/db_number
DEFAULT_BROKER = "mongodb://localhost:27017/my_mq_jobs"  # mongodb://username:password@host:port/database_name
# DEFAULT_BROKER = f"sqlalchemy+sqlite:///{BASE_DIR}/db.sqlite"  # sqlite:///path/to/database.db

# 保存运行结果，使用 RabbitMQ, rpc://username:Password@IP:Port//v_host
# DEFAULT_RESULT_BACKEND = 'rpc://development:password123456@134.175.100.239:5672//development_host'
# DEFAULT_RESULT_BACKEND = 'redis://:@127.0.0.1:6379/1'
# DEFAULT_RESULT_BACKEND = "mongodb://localhost:27017/my_mq_jobs"
DEFAULT_RESULT_BACKEND = ''  # 不保存运行结果(使用 sqlite 作为 clery 数据储存时，没法保存结果)


class CELERY_CONFIG(object):
    broker_url = os.environ.get('BROKER_URL') or DEFAULT_BROKER  # 代理人的地址
    result_backend = os.environ.get('CELERY_RESULT_BACKEND') or DEFAULT_RESULT_BACKEND  # 运行结果存储地址

    task_default_queue = os.environ.get('CELERY_DEFAULT_QUEUE', APP_NAME)  # 默认队列
    result_expires = int(os.environ.get('CELERY_TASK_RESULT_EXPIRES', 3600))  # 任务结果过期时间，单位秒

    timezone = 'Asia/Shanghai'  # 设置时区
    enable_utc = True  # UTC时区换算


FETCH_TASK_QUEUE = os.environ.get('FETCH_TASK_QUEUE') or 'fetch_queue'
NOTIFY_TASK_QUEUE = os.environ.get('NOTIFY_TASK_QUEUE') or 'notify_queue'
# 所有的队列
ALL_QUEUES = (CELERY_CONFIG.task_default_queue, FETCH_TASK_QUEUE, NOTIFY_TASK_QUEUE)


# Database
MONGO_CONNECTIONS = {
    'default': os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/my_flask_celery',
    # 'broker': CELERY_CONFIG.broker_url,  # 如果使用 mongodb 作为中间件，则需要配置这里
    # 'result_backend': CELERY_CONFIG.result_backend
}


# API
JWT_SECRET = os.environ.get('JWT_SECRET', 'befxjbubeg0lacoazvorsokhuofadav1')
JWT_EXPIRES = 24
