# -*- coding: utf-8 -*-

"""
auth middleware
"""

from flask import current_app as app, abort
from .base import Middleware


class TokenMiddleware(Middleware):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self):
        auth_chains = app.auth_backends or []
        for auth in auth_chains:
            auth.get_credential()

        # 获取response
        return self.get_response()
