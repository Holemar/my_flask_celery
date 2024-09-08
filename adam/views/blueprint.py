# -*- coding: UTF-8 -*-
"""
Blueprint, different to Flask one
"""
import os
import logging

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
        self.acl = []

    def decorator(self, routes_key, action, methods, params=None, permissions=None):
        def wrapper(fun):
            self.routes[routes_key][action] = {
                'action': action,
                'methods': methods,
                'function': fun,
                'params': params or {},
                'function_name': fun.__name__
            }
            if permissions:
                self.acl.append(f'{routes_key}@{action}')
            return fun
        return wrapper

    def item_method(self, action, methods, params=None, permissions=None):
        """Like :meth:`Flask.route` but for a blueprint.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the blueprint.
        """
        return self.decorator('item', action, methods, params, permissions)

    def remote_item_method(self, action, methods, params=None, permissions=None):
        """Like :meth:`Flask.route` but for a blueprint.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the blueprint.
        """
        return self.decorator('remote_item', action, methods, params, permissions)

    def static_method(self, action, methods, params=None, permissions=None):
        """Like :meth:`Flask.route` but for a blueprint.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the blueprint.
        """
        return self.decorator('collection', action, methods, params, permissions)
