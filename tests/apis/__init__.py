# -*- coding:utf-8 -*-
"""
本目录直接发起请求，查看真正的接口返回值(包括本地及远程接口)
"""

import ssl
import socket
from adam.utils.http_util import get_html
from tests import SOURCE_PATH

TIMEOUT = 120
context = ssl._create_unverified_context()
ssl._create_default_https_context = ssl._create_unverified_context
socket.setdefaulttimeout(TIMEOUT)

host = 'http://127.0.0.1:8000'
HEADERS = {'Authorization': "XXX"}


def add_default_headers(headers=None):
    """添加默认 header"""
    headers = headers or {}
    for k, v in HEADERS.items():
        headers.setdefault(k, v)
    return headers


def get(url, param=None, headers=None, **kwargs):
    """发送get请求"""
    url = get_url(url)
    headers = add_default_headers(headers)
    return get_html(url, data=param, method='GET', headers=headers, **kwargs)


def post(url, param=None, headers=None, **kwargs):
    """发送post请求"""
    url = get_url(url)
    if 'send_json' not in kwargs:
        kwargs['send_json'] = True
    headers = add_default_headers(headers)
    return get_html(url, data=param, method='POST', headers=headers, **kwargs)


def put(url, param=None, headers=None, **kwargs):
    """发送post请求"""
    url = get_url(url)
    if 'send_json' not in kwargs:
        kwargs['send_json'] = True
    headers = add_default_headers(headers)
    return get_html(url, data=param, method='PUT', headers=headers, **kwargs)


def delete(url, param=None, headers=None, **kwargs):
    """发送post请求"""
    url = get_url(url)
    headers = add_default_headers(headers)
    return get_html(url, data=param, method='DELETE', headers=headers, **kwargs)


# api 地址补丁，适配本机及线上请求地址
def get_url(url):
    """获取对应的url，“/”开头的会自动拼接上本站 host，其它的直接返回"""
    global host
    if not url:
        return host
    if url.lower().startswith(('http://', 'https://')):
        return url
    if url.startswith('/') or host.endswith('/'):
        return '%s%s' % (host, url)
    return '%s/%s' % (host, url)


def set_host(new_host):
    """设置访问域名"""
    global host
    host = new_host
