# -*- coding:utf-8 -*-

import os
import sys
import ssl
import json
import socket
import logging
from urllib import request, parse

# 导入环境
CURRENT_DIR, _ = os.path.split(os.path.abspath(__file__))
CURRENT_DIR = CURRENT_DIR or os.getcwd()  # 当前目录
SOURCE_PATH = os.path.abspath(os.path.dirname(os.path.dirname(CURRENT_DIR)))  # 上上一层目录，认为是源目录

if SOURCE_PATH not in sys.path:
    sys.path.append(SOURCE_PATH)

# 日志配置
LOGGER_FORMAT = "[%(asctime)s] [%(funcName)s:%(lineno)s] %(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOGGER_FORMAT)

TIMEOUT = 120
context = ssl._create_unverified_context()
ssl._create_default_https_context = ssl._create_unverified_context
socket.setdefaulttimeout(TIMEOUT)

host = 'http://127.0.0.1:8000'
HEADERS = {'Authorization': "XXX"}


def send(url, param=None, method='GET', timeout=TIMEOUT, headers=None, send_json=False, return_json=False):
    """
    发出请求获取网页内容(会要求服务器使用gzip压缩返回结果,也会提交文件等内容,需要服务器支持这些功能)
    :param {string} url: 要获取内容的网页地址(GET请求时可直接将请求参数写在此url上)
    :param {dict|string} param: 要提交到网页的参数(get请求时会拼接到 url 上)
    :param {string} method: 提交方式,如 GET、 POST
    :param {int} timeout: 请求超时时间(单位:秒,设为 None 则是不设置超时时间)
    :param {dict} headers: 请求的头部信息
    :param {bool} send_json: 请求参数是否json形式传输
    :param {bool} return_json: 返回结果是否json形式
    :return {string}: 返回获取的页面内容字符串
    """
    method = method.strip().upper()
    url = get_url(url)
    headers = {} if headers is None else headers

    # get 方式的参数处理, 参数拼接
    if method == 'GET' and param:
        url += "&" if "?" in url else "?"
        if isinstance(param, dict):
            param = {k: (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, separators=(',', ':'))) for k, v
                     in param.items()}
            param = parse.urlencode(param)
        param = param.decode() if isinstance(param, (bytes, bytearray)) else str(param)
        url += param
        param = None
    # 请求参数
    elif send_json:
        if param and not isinstance(param, (bytes, str)):
            param = json.dumps(param)
            param = bytes(param, 'utf8')
        if not headers.get('Content-Type'):
            headers.update({'Content-Type': 'application/json'})
    elif param and isinstance(param, dict):
        param = {k: (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, separators=(',', ':'))) for k, v in
                 param.items()}
        param = parse.urlencode(param)
        param = bytes(param, 'utf8')
    # 返回结果
    if return_json and 'Accept' not in headers:
        headers.update({'Accept': 'application/json'})
    # 加上默认 header
    for k, v in HEADERS.items():
        headers.setdefault(k, v)
    # 模拟浏览器
    headers.setdefault('Accept', 'application/json, text/plain, */*')
    # headers.setdefault('Accept-Encoding', 'gzip, deflate, sdch')
    headers.setdefault('Accept-Language', 'zh-CN,zh;q=0.8')
    headers.setdefault('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36')

    try:
        req = request.Request(url=url, data=param, headers=headers, method=method)
        if url.lower().startswith('https'):
            response = request.urlopen(req, timeout=timeout, context=context)
        else:
            response = request.urlopen(req, timeout=timeout)
        status_code = response.getcode()  # 响应状态码,不是 200 时直接就报异常了
        res = response.read()
        response.close()
    except request.HTTPError as e:
        status_code = e.code
        res = e.read()
    except Exception as e:
        logging.exception(e)
        status_code = 0
        res = None

    try:
        res = res.decode('utf-8') if res else None
    except:
        pass
    if len(f"{headers}") <= 200:
        logging.info(f"{method} 请求url:{url}, headers:{headers}, param:{param}, 状态码:{status_code}, 返回:{res}")
    else:
        logging.info(f"{method} 请求url:{url}, param:{param}, 状态码:{status_code}, 返回:{res}")
    if return_json and res:
        res = json.loads(res)
    return res


def download_file(url, param=None, method='GET', file_path=None, headers=None, send_json=False, timeout=TIMEOUT):
    """文件下载"""
    if file_path:
        file_path = os.path.abspath(file_path)
        # 如果文件已经存在，则不必再写
        if os.path.exists(file_path) and os.path.getsize(file_path) > 1: return
        file_dir = os.path.dirname(file_path)
        # 没有文件的目录，则先创建目录，避免因此报错
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir)

    try:
        url = get_url(url)

        # get 方式的参数处理, 参数拼接
        if method == 'GET' and param:
            url += "&" if "?" in url else "?"
            if isinstance(param, dict):
                param = {k: (v if isinstance(v, str) else json.dumps(v)) for k, v in param.items()}
                param = parse.urlencode(param)
            param = param.decode() if isinstance(param, (bytes, bytearray)) else str(param)
            url += param
            param = None
        # 请求参数
        elif send_json:
            if param and not isinstance(param, (bytes, str)):
                param = json.dumps(param)
                param = bytes(param, 'utf8')
            if not headers.get('Content-Type'):
                headers.update({'Content-Type': 'application/json'})
        elif param and isinstance(param, dict):
            param = {k: (v if isinstance(v, str) else json.dumps(v)) for k, v in param.items()}
            param = parse.urlencode(param)
            param = bytes(param, 'utf8')

        req = request.Request(url=url, data=param, headers=headers, method=method)
        if url.lower().startswith('https'):
            response = request.urlopen(req, timeout=timeout, context=context)
        else:
            response = request.urlopen(req, timeout=timeout)
        res_headers = response.headers
        file_name = None
        if res_headers and not file_path:
            try:
                disposition = res_headers.get("Content-Disposition", '')
                if disposition and ';' in disposition:
                    disposition = disposition.split(";")[1]
                    if "filename=" in disposition:
                        file_name = disposition.split("filename=")[1]
                    elif "filename*=UTF-8" in disposition:
                        file_name = disposition.split("filename*=UTF-8")[1]
                    if file_name:
                        file_name = parse.unquote(file_name.replace('"', '').replace("'", ''))  # 去掉单双引号
                        file_path = './' + file_name
            except:
                pass
        if not file_path:
            file_name = url.split('/')[-1]
            file_name = file_name.split('?')[0]
            file_path = './' + file_name
        with open(file_path, "wb") as f:
            f.write(response.read())
        logging.info('... download_file ... %s, %s', file_path, url)
        return True
    except Exception as e:
        # 请求异常,认为返回不正确
        logging.exception(u"download_file error: %s  url:%s, param:%s, file_path:%s", e, url, param, file_path)


def get(url, param=None, headers=None, **kwargs):
    """发送get请求"""
    return send(url, param=param, method='GET', headers=headers, **kwargs)


def post(url, param=None, headers=None, **kwargs):
    """发送post请求"""
    if 'send_json' not in kwargs:
        kwargs['send_json'] = True
    return send(url, param=param, method='POST', headers=headers, **kwargs)


def put(url, param=None, headers=None, **kwargs):
    """发送post请求"""
    if 'send_json' not in kwargs:
        kwargs['send_json'] = True
    return send(url, param=param, method='PUT', headers=headers, **kwargs)


def delete(url, param=None, headers=None, **kwargs):
    """发送post请求"""
    return send(url, param=param, method='DELETE', headers=headers, **kwargs)


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
