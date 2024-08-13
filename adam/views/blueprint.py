# -*- coding: UTF-8 -*-
"""
Blueprint, different to Flask one
"""
import os
import logging

from mongoengine import Document
from werkzeug.exceptions import HTTPException
from flask import request

logger = logging.getLogger(__name__)
SUCCESS_CODE = int(os.environ.get('SUCCESS_CODE', 200))  # 成功的返回码
SUCCESS_MESSAGE = os.environ.get('SUCCESS_MESSAGE', 'success')  # 成功的返回值


def return_data(code=None, message=None, data=None):
    """
    响应数据
    """
    result = {
        'code': code or SUCCESS_CODE,
        'message': message or SUCCESS_MESSAGE,
    }
    if data is not None:
        result['data'] = data
    return result


class Blueprint(object):
    def __init__(self, name):
        self.name = name
        self.routes = {'item': {}, 'collection': {}, 'remote_item': {}}

    def decorator(self, routes_key, action, methods, params=None):
        def wrapper(fun):
            self.routes[routes_key][action] = {
                'action': action,
                'methods': methods,
                'function': fun,
                'params': params or {},
                'function_name': fun.__name__
            }
            return run_api(fun)
        return wrapper

    def item_method(self, action, methods, params=None):
        """Like :meth:`Flask.route` but for a blueprint.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the blueprint.
        """
        return self.decorator('item', action, methods, params)

    def remote_item_method(self, action, methods, params=None):
        """Like :meth:`Flask.route` but for a blueprint.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the blueprint.
        """
        return self.decorator('remote_item', action, methods, params)

    def static_method(self, action, methods, params=None):
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
        try:
            res = fun(*args, **kwargs)
            # 强行封装成统一格式
            if isinstance(res, (list, dict)) and 'code' not in res:
                res = return_data(data=res)
            elif isinstance(res, Document):
                res = return_data(data=res)
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
    return wrapper
