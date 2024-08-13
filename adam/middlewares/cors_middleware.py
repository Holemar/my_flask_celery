# -*- coding: utf-8 -*-

"""
Cors middleware
"""

import re
import os
import time
import logging
from flask import request

from ..utils.config_util import config
from .base import Middleware

# api 超时警告时间，单位：秒
API_WARN_TIME = float(os.environ.get('API_TIMEOUT') or 1)
logger = logging.getLogger(__name__)


def get_param():
    """获取参数"""
    try:
        post_data = request.data
        if post_data and isinstance(post_data, (bytes, bytearray)):
            post_data = post_data.decode()
        return post_data
    except:
        return None


class CorsMiddleware(Middleware):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self):
        # before resposne

        beg_time = time.time()
        response = self.get_response()
        time_elapsed = time.time() - beg_time

        if time_elapsed >= API_WARN_TIME:  # 耗时太长
            logger.warning(u'接口耗时太长:%.4f秒 %s URL:%s, 参数: %s 返回:%s',
                           time_elapsed, request.method, request.full_path, get_param(), response)
        else:
            logger.debug('接口请求耗时:%.4f秒 %s URL:%s, 参数: %s 返回:%s',
                         time_elapsed, request.method, request.full_path, get_param(), response)

        # after response
        response.headers.add('X-Elapsed-Time', time_elapsed)  # add elapsed time to response header
        origin = request.headers.get('Origin')
        if origin and (config.X_DOMAINS or config.X_DOMAINS_RE):
            if config.X_DOMAINS is None:
                domains = []
            elif isinstance(config.X_DOMAINS, str):
                domains = [config.X_DOMAINS]
            else:
                domains = config.X_DOMAINS

            if config.X_DOMAINS_RE is None:
                domains_re = []
            elif isinstance(config.X_DOMAINS_RE, str):
                domains_re = [config.X_DOMAINS_RE]
            else:
                domains_re = config.X_DOMAINS_RE

            # precompile regexes and ignore invalids
            domains_re_compiled = []
            for domain_re in domains_re:
                try:
                    domains_re_compiled.append(re.compile(domain_re))
                except re.error:
                    continue

            if config.X_HEADERS is None:
                headers = []
            elif isinstance(config.X_HEADERS, str):
                headers = [config.X_HEADERS]
            else:
                headers = config.X_HEADERS

            if config.X_EXPOSE_HEADERS is None:
                expose_headers = []
            elif isinstance(config.X_EXPOSE_HEADERS, str):
                expose_headers = [config.X_EXPOSE_HEADERS]
            else:
                expose_headers = config.X_EXPOSE_HEADERS

            # The only accepted value for Access-Control-Allow-Credentials header
            # is "true"
            allow_credentials = config.X_ALLOW_CREDENTIALS is True

            if '*' in domains:
                response.headers.add('Access-Control-Allow-Origin', origin)
                response.headers.add('Vary', 'Origin')
            elif any(origin == domain for domain in domains):
                response.headers.add('Access-Control-Allow-Origin', origin)
            elif any(domain.match(origin) for domain in domains_re_compiled):
                response.headers.add('Access-Control-Allow-Origin', origin)
            else:
                response.headers.add('Access-Control-Allow-Origin', '')
            response.headers.add('Access-Control-Allow-Headers', ', '.join(headers))
            response.headers.add('Access-Control-Expose-Headers', ', '.join(expose_headers))
            response.headers.add('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE, OPTIONS')
            response.headers.add('Access-Control-Max-Age', config.X_MAX_AGE)
            if allow_credentials:
                response.headers.add('Access-Control-Allow-Credentials', "true")

        return response
