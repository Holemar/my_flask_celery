# -*- coding: utf-8 -*-


class Middleware(object):
    """
    Middleware
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self):
        response = self.get_response()
        return response
