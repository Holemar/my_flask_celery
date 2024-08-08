# -*- coding:utf-8 -*-
import os
import time
import logging
from flask import jsonify, request, Blueprint, current_app
from adam.config_util import config
from adam.celery_util import get_pending_msg

bp = Blueprint('rout', __name__)
logger = logging.getLogger(__name__)


@bp.route('/')
def index():
    return current_app.send_static_file('index.html')


@bp.route('/status')
def status():
    """用于查看程序运行状态。任务堆积情况等"""
    start_time = time.time()
    message = {'beat': 'ERROR', 'status': 'ERROR', 'pendMsg': 0, 'version': config.VERSION}
    try:
        data = request.args
        if data.get('route') or data.get('url'):
            message['route'] = list(repr(n) for n in current_app.url_map.iter_rules())
        if data.get('models'):
            message['models'] = list(current_app.models.keys())
        message['pendMsg'], message['tasks'] = get_pending_msg()
        # 版本更新时间
        message['update_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(__file__)))
        message['now'] = time.strftime('%Y-%m-%d %H:%M:%S')  # 系统时间,用来核对系统时间是否正确
        message['duration'] = time.time() - start_time  # 本接口查询耗时
    except Exception as e:
        logger.exception("Get status raise error {}".format(str(e)))
        message['error'] = str(e)
    finally:
        return jsonify(message)


@bp.route('/<path:filename>')
def serve_static(filename):
    """静态文件访问"""
    return current_app.send_static_file(filename)
