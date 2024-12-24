# -*- coding: utf-8 -*-

"""
License middleware
"""

from flask import request
from datetime import datetime
from flask import current_app as app
from .base import Middleware
from ..exceptions import BaseError


class LicenseLimitMiddleware(Middleware):
    """
    LicenseLimit Middleware, 必须放在token middleware之后.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.endpoints = app.config.get('LICENSE_LIMIT') or []

    def __call__(self):
        # before resposne
        license = None
        endpoint = request.endpoint
        if endpoint in self.endpoints:
            if hasattr(request, 'license') and request.license:
                license = request.license
                if license:
                    if license.expired_at and datetime.now() > license.expired_at:
                        BaseError.license_expired()
                    elif license.limit and license.limit > 0 and license.count and license.count >= license.limit:
                        BaseError.over_limit()

        response = self.get_response()

        if license:
            license.update(inc__count=1)
            response.headers.add('X-LicenseLimit-Count', str(license.count + 1))
            response.headers.add('X-LicenseLimit-Limit', str(license.limit))
            if license.expired_at:
                response.headers.add('X-LicenseLimit-Expire', license.expired_at.isoformat())

        # after response
        return response
