# -*- coding: UTF-8 -*-
"""
Blueprint, different to Flask one
"""


class Blueprint(object):
    def __init__(self, name):
        self.name = name
        self.routes = {'item': {}, 'collection': {}, 'remote_item': {}}

    def register_item_method(self, action, methods, params=None):
        """Like :meth:`Flask.route` but for a blueprint.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the blueprint.
        """
        def decorator(f):
            self.routes['item'][action] = {
                'action': action,
                'methods': methods,
                'function': f,
                'params': params or {},
                'function_name': f.__name__
            }
            return f
        return decorator

    def register_remote_item_method(self, action, methods, params=None):
        """Like :meth:`Flask.route` but for a blueprint.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the blueprint.
        """
        def decorator(f):
            self.routes['remote_item'][action] = {
                'action': action,
                'methods': methods,
                'function': f,
                'params': params or {},
                'function_name': f.__name__
            }
            return f
        return decorator

    def register_static_method(self, action, methods, params=None):
        """Like :meth:`Flask.route` but for a blueprint.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the blueprint.
        """
        def decorator(f):
            self.routes['collection'][action] = {
                'action': action,
                'methods': methods,
                'function': f,
                'params': params or {},
                'function_name': f.__name__
            }
            return f
        return decorator
