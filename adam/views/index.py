# -*- coding:utf-8 -*-
import os
import time
import logging
from flask import jsonify, request, current_app
from .blueprint import return_data
from ..utils.config_util import config
from ..utils.json_util import json_serializable
from ..utils.celery_util import get_pending_msg, get_beat, get_workers, get_beat_schedule

logger = logging.getLogger(__name__)


@current_app.route('/')
def index():
    return current_app.send_static_file('index.html')


@current_app.route('/index/<path:filename>')
def front_page(filename):
    """与前端做约定，前端页面请求的路径为 /index/xxx """
    return current_app.send_static_file('index.html')


@current_app.route('/test')
def test():
    time.sleep(0.1)
    return {"code": 0, "message": "success"}


@current_app.route('/status')
def status():
    """用于查看程序运行状态。任务堆积情况等"""
    start_time = time.time()
    message = {'beat': 'ERROR', 'workers': 0, 'pend_message': 0, 'version': config.VERSION}
    try:
        message['beat'] = get_beat()
        workers = get_workers()
        message['workers'] = sum(list(workers.values()))
        message['queue_workers'] = workers
        message['pend_message'], message['tasks'] = get_pending_msg()
        # 版本更新时间
        message['update_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(__file__)))
        message['now'] = time.strftime('%Y-%m-%d %H:%M:%S')  # 系统时间,用来核对系统时间是否正确

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

        message['duration'] = time.time() - start_time  # 本接口查询耗时
    except Exception as e:
        logger.exception("Get status raise error {}".format(str(e)))
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
