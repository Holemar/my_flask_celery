# -*- coding: UTF-8 -*-
"""
Blueprint, different to Flask one
"""
import os
import time
import logging

from werkzeug.exceptions import HTTPException
from flask import request


# api 超时警告时间，单位：秒
API_WARN_TIME = float(os.environ.get('API_TIMEOUT') or 1)
logger = logging.getLogger(__name__)


class Blueprint(object):
    """view的各接口过滤器"""

    def __init__(self, name):
        self.name = name
        self.routes = {'item': {}, 'collection': {}, 'remote_item': {}}

    def decorator(self, routes_key, action, methods, params=None):
        def wrapper(f):
            self.routes[routes_key][action] = {
                'action': action,
                'methods': methods,
                'function': f,
                'params': params or {},
                'function_name': f.__name__
            }
            return run_api(f)

        return wrapper

    def register_item_method(self, action, methods, params=None):
        """Like :meth:`Flask.route` but for a blueprint.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the blueprint.
        """
        return self.decorator('item', action, methods, params)

    def register_remote_item_method(self, action, methods, params=None):
        """Like :meth:`Flask.route` but for a blueprint.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the blueprint.
        """
        return self.decorator('remote_item', action, methods, params)

    def register_static_method(self, action, methods, params=None):
        """Like :meth:`Flask.route` but for a blueprint.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the blueprint.
        """
        return self.decorator('collection', action, methods, params)


def get_param():
    """获取参数"""
    try:
        post_data = request.data
        if post_data and isinstance(post_data, (bytes, bytearray)):
            post_data = post_data.decode()
        return post_data
    except:
        return None


def run_api(fun):
    """接口执行异常捕获"""

    def wrapper(*args, **kwargs):
        res = None
        start_time = time.time()
        # 正式执行函数
        try:
            res = fun(*args, **kwargs)
            return res
        except HTTPException as e:
            logger.exception("请求异常 %s %s: %s: %s，参数:%s",
                             request.method, request.full_path, e, e.description, get_param())
            if e.response:
                return e.get_response()
            else:
                raise
        except Exception as e:
            logger.exception("请求异常 %s %s: %s，参数:%s", request.method, request.full_path, e, get_param())
            raise
        finally:
            # 超时日志
            duration = time.time() - start_time
            if duration >= API_WARN_TIME:  # 耗时太长
                logger.warning(u'接口耗时太长:%.4f秒 %s URL:%s, 参数: %s 返回:%s',
                                duration, request.method, request.full_path, get_param(), res)
            else:
                logger.debug('接口请求耗时:%.4f秒 %s URL:%s, 参数: %s 返回:%s',
                             duration, request.method, request.full_path, get_param(), res)

    return wrapper
