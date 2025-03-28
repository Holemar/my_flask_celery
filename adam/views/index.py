# -*- coding:utf-8 -*-
import os
import time
import logging

from flask import jsonify, request, current_app
from .blueprint import return_data
from ..utils.config_util import config
from ..utils.json_util import json_serializable
from ..utils.celery_util import get_pending_msg, get_beat, get_workers, get_beat_schedule, delete_repeat_task, clear_tasks

LOGGER = logging.getLogger(__name__)
PUBLISH_TIME = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())  # 发布时间


@current_app.route('/')
def index():
    return current_app.send_static_file('index.html')


@current_app.route(f'/{config.URL_PREFIX}/status')
def status():
    """用于查看程序运行状态。任务堆积情况等"""
    start_time = time.time()
    message = {'beat': 'ERROR', 'workers': 0, 'pend_message': 0, 'version': config.VERSION}
    try:
        # 版本更新时间
        message['update_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(__file__)))
        message['publish_time'] = PUBLISH_TIME  # 发布时间
        message['now'] = time.strftime('%Y-%m-%d %H:%M:%S')  # 系统时间,用来核对系统时间是否正确
        # message['argv'] = sys.argv  # 系统启动参数
        # 任务队列情况
        message['beat'] = get_beat()
        workers = get_workers()
        message['workers'] = sum(list(workers.values()))
        message['queue_workers'] = workers
        message['pend_message'], message['tasks'] = get_pending_msg()

        data = request.args
        # 参数控制查看内容, 如： http://127.0.0.1:8000/status?url=1&models=1&config=1&beat=1
        if data.get('route') or data.get('url'):  # 查看所有的 api 路由
            message['route'] = list(repr(n) for n in current_app.url_map.iter_rules())
        # 查看所有的数据库 model
        if data.get('models'):
            message['models'] = list(current_app.models.keys())
        # 查看所有的配置 (settings + default_settings)
        if data.get('config'):  # 查看所有的配置
            values = {k: json_serializable(v) for k, v in current_app.config.items()}
            # 内嵌类，需要额外读取
            c_config = current_app.config['CELERY_CONFIG']
            values['CELERY_CONFIG'] = {k: getattr(c_config, k) for k in dir(c_config) if not k.startswith('__')}
            message['config'] = values
        # 查看所有的 beat 定时任务配置
        if data.get('beat'):
            message['beat_schedule'] = get_beat_schedule()
        # 清除重复任务
        if data.get('delete_repeat_task'):
            delete_repeat_task()
        # 清除所有任务
        if data.get('clear_tasks'):
            clear_tasks()

        message['duration'] = time.time() - start_time  # 本接口查询耗时
    except Exception as e:
        LOGGER.exception("Get status raise error {}".format(str(e)))
        message['error'] = str(e)
    finally:
        return jsonify(message)


@current_app.route('/<path:filename>')
def serve_static(filename):
    """静态文件访问"""
    return current_app.send_static_file(filename)


@current_app.errorhandler(404)
def page_not_found(e):
    """404出错，区分前后端"""
    url = request.full_path
    prefix = config.URL_PREFIX
    if not prefix or url.startswith(f'/{prefix}/'):
        return return_data(code=404, message=str(e))
    else:
        return current_app.send_static_file('index.html')


@current_app.errorhandler(500)
def internal_server_error(e):
    """程序执行错误"""
    return return_data(code=500, message=str(e))
