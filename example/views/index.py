# -*- coding:utf-8 -*-
import os
import time
import logging
from flask import jsonify, request, Blueprint, current_app
from adam.utils.config_util import config
from adam.utils.celery_util import get_pending_msg
from adam.utils.json_util import json_serializable
from adam.utils.celery_util import get_beat, get_workers

bp = Blueprint('rout', __name__)
logger = logging.getLogger(__name__)


@bp.route('/')
def index():
    return current_app.send_static_file('index.html')


@bp.route('/status')
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
        # 参数控制查看内容, 如： http://127.0.0.1:8000/status?url=1&models=1&config=1
        if data.get('route') or data.get('url'):
            message['route'] = list(repr(n) for n in current_app.url_map.iter_rules())
        if data.get('models'):
            message['models'] = list(current_app.models.keys())
        if data.get('config'):
            values = {k: json_serializable(v) for k, v in current_app.config.items()}
            # 内嵌类，需要额外读取
            c_config = current_app.config['CELERY_CONFIG']
            values['CELERY_CONFIG'] = {k: getattr(c_config, k) for k in dir(c_config) if not k.startswith('__')}
            message['config'] = values

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


"""
这是此文件的第二种写法，写完之后还需要注册:
from views import index  # 导入此文件
# app = Flask(__name__)  # 需要注册在 app 实例上
app.register_blueprint(index.bp, url_prefix="")  # 注册蓝图

现在废弃此写法，改成
new Flask 实例时，在 load_views 之后加入
具体写法可以参考 adam/views/index.py

    # 在  flask_app.py  中加入
    with app.app_context():
        from views import index

"""