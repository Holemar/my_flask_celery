#!python
# -*- coding:utf-8 -*-

import os
import os.path
import ssl
import json
import logging
from http.client import IncompleteRead
from urllib import request, parse

from .str_util import gzip_decode, zlib_decode, decode2str


__all__ = ('get_html', 'get_zip_response', 'download_file', 'get_host', 'get_request_params')


context = ssl._create_unverified_context()
ssl._create_default_https_context = ssl._create_unverified_context

# http请求超时时间
TIMEOUT = 30
# 提交请求的最大次数。(1表示只提交一次,失败也不再重复提交； 2表示允许重复提交2次,即第一次失败时再来一次,3表示允许重复提交3次...)
http_repeat_time = 3
# 请求头(伪装成浏览器)
base_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    # 'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    # 'Connection': 'keep-alive',
    # 'Proxy-Connection': 'keep-alive',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"macOS"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Sec-Ch-Ua': 'Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    # 'Referrer Policy': 'strict-origin-when-cross-origin',
}


def get_html(url, headers=None, return_response=False, use_zip=False, repeat_time=http_repeat_time,
             method='GET', data=None, timeout=TIMEOUT, force_header=False, send_json=False, return_json=False, **kwarge):
    """发送请求获取网页内容
    :param {string} url: 请求地址
    :param {dict} headers: 请求头
    :param {bool} return_response: 是否返回 response, 是则返回 response ，否则返回页面内容。默认返回页面内容。
    :param {bool|str} use_zip : 使用的压缩模式,值可为: gzip, deflate (值为 False 时不压缩,默认:不压缩)
    :param {int} repeat_time : 重试次数
    :param {string} method: 请求方式
    :param {dict|str} data: 请求参数
    :param {int} timeout : 超时时间(秒)
    :param {bool} force_header : 强行指定请求体的头部信息，不再自动添加
    :param {bool} send_json: 请求参数是否json形式传输
    :param {bool} return_json: 返回结果是否json形式
    """
    # 处理请求头
    _headers = change_send_header(url, headers, force_header=force_header, send_json=send_json, use_zip=use_zip,
                                  return_json=return_json)
    # 请求参数处理
    url, data = change_send_data(url, method, data, send_json=send_json)

    # 允许出错时重复提交多次,只要设置了 repeat_time 的次数
    req, response = None, None
    res, status_code = None, 0
    while repeat_time > 0:
        try:
            req = request.Request(url=url, headers=_headers, method=method or 'GET', data=data)
            if url.lower().startswith('https'):
                response = request.urlopen(req, timeout=timeout, context=context)
            else:
                response = request.urlopen(req, timeout=timeout)
            if return_response and response:
                return response
            else:
                status_code = response.getcode()  # 响应状态码,不是 200 时直接就报异常了
                page_html = get_zip_response(response)
                res = decode2str(page_html)  # 正常返回时，不再重试
                response.close()
                if return_json and res:
                    res = json.loads(res)
                '''
                if len(f"{headers}") <= 200:
                    logging.info(f"{method} 请求url:{url}, headers:{headers}, param:{data}, 状态码:{status_code}, 返回:{res}")
                else:
                    logging.info(f"{method} 请求url:{url}, param:{data}, 状态码:{status_code}, 返回:{res}")
                # '''
                return res
        except IncompleteRead as e:
            res = e.partial
        except request.HTTPError as e:
            status_code = e.code
            res = e.read()
        except Exception as e:
            # 请求异常,认为返回不正确
            repeat_time -= 1
            if req and hasattr(req, 'redirect_dict'):
                url = list(req.redirect_dict.keys())[0]
                if repeat_time <= 0:
                    logging.error(u"http url:%s error: %s", url, e)
                    return url
                _headers['Host'] = get_host(url)  # 设host
                _headers['Authority'] = get_host(url).strip('/').lower()  # 设host
                logging.warning(u"http url:%s error: %s", req.full_url, e)
            else:
                logging.error(u"http error: %s  url:%s, 参数:%s", e, url, data)

    logging.error('获取不到网页内容, 状态码:%s, url:%s, 返回:%s', status_code, url, res)
    if return_response:
        return response
    return ''


def change_send_header(url, headers, force_header=False, send_json=False, use_zip=False, return_json=False):
    """设置请求头"""
    _headers = base_headers.copy()
    _headers.setdefault('Host', get_host(url))  # 设host
    _headers.setdefault('Authority', get_host(url).strip('/').lower())  # 设host
    if headers:
        if force_header:
            _headers = headers
        else:
            _headers.update(headers)
    if use_zip:
        _headers['Accept-Encoding'] = 'gzip, deflate'
    if send_json and not _headers.get('Content-Type'):
        _headers.update({'Content-Type': 'application/json'})
    # 返回结果
    if return_json and 'Accept' not in headers:
        _headers.update({'Accept': 'application/json'})
    return _headers


def change_send_data(url, method, data, send_json=False):
    """
    修改请求参数，将字典类型的数据转为json格式
    :param {string} url: 请求地址
    :param {string} method: 请求方式
    :param {dict} data: 请求参数
    :param {bool} send_json: 是否发送json格式的参数
    :return: 修改后的请求参数
    """
    # get 方式的参数处理, 参数拼接
    method = method or 'GET'
    if method.upper() == 'GET' and data:
        url += "&" if "?" in url else "?"
        if isinstance(data, dict):
            data = {k: (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, separators=(',', ':'))) for k, v
                    in data.items()}
            data = parse.urlencode(data)
        data = data.decode() if isinstance(data, (bytes, bytearray)) else str(data)
        url += data
        data = None
    # 请求参数
    elif send_json:
        if data is not None and not isinstance(data, (bytes, str)):
            data = json.dumps(data)
    elif data and isinstance(data, dict):
        data = {k: (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, separators=(',', ':'))) for k, v in
                data.items()}
        data = parse.urlencode(data)
    if data is not None and isinstance(data, str):
        data = bytes(data, 'utf8')
    return url, data


def get_zip_response(response):
    """获取压缩后的 response
    :param response: 原始 response
    :return: 解压后的 html 内容
    """
    page_html = response.read()
    if not page_html:
        return None
    # 解压
    encoding = response.headers.get('Content-Encoding')
    if encoding and encoding in ('gzip', 'deflate'):
        if encoding == 'gzip':
            page_html = gzip_decode(page_html)
        elif encoding == 'deflate':
            page_html = zlib_decode(page_html)
        elif encoding == 'br':
            import brotli  # pip install brotli==1.1.0
            page_html = brotli.decompress(page_html)
        elif encoding == 'zstd':
            import zstd
            page_html = zstd.decompress(page_html)
    return page_html


def download_file(url, data=None, method='GET', file_path=None, headers=None, force_header=False, check_fun=None,
                  send_json=False, timeout=TIMEOUT):
    """文件下载"""
    global http_repeat_time
    if file_path:
        file_path = os.path.abspath(file_path)
        # 如果文件已经存在，则不必再写
        if os.path.exists(file_path) and os.path.getsize(file_path) > 1: return
        file_dir = os.path.dirname(file_path)
        # 没有文件的目录，则先创建目录，避免因此报错
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir)
    # 处理请求头
    _headers = change_send_header(url, headers, force_header=force_header, send_json=send_json)
    # 请求参数处理
    url, data = change_send_data(url, method, data, send_json=send_json)

    repeat_time = http_repeat_time
    # 允许出错时重复提交多次,只要设置了 repeat_time 的次数
    while repeat_time > 0:
        try:
            req = request.Request(url=url, data=data, headers=_headers, method=method)
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
            file_io = response.read()
            # 检测是否正确的下载内容
            if check_fun and not check_fun(file_io):
                return False
            with open(file_path, "wb") as f:
                f.write(file_io)
            logging.info('... download_file ... %s, %s', file_path, url)
            return True
        except Exception as e:
            # 请求异常,认为返回不正确
            repeat_time -= 1
            logging.error(u"download_file error: %s  url:%s, file_path:%s", e, url, file_path)


def get_host(url):
    """从请求地址中，取出 host
    :param url: 请求地址
    :return host
    """
    us = url.split('/')
    return us[2]


def get_request_params(url):
    """
    获取url里面的参数,以字典的形式返回
    :param {string} url: 请求地址
    :return {dict}: 以字典的形式返回请求里面的参数
    """
    result = {}
    if isinstance(url, (bytes, bytearray)):
        url = decode2str(url)
    if not isinstance(url, str):
        if isinstance(url, dict):
            return url
        else:
            return result

    # li = re.findall(r'\w+=[^&]*', url) # 为了提高效率，避免使用正则
    i = url.find('?')
    if i != -1:
        url = url[i + 1:]
    li = url.split('&')

    if not li:
        return result

    for ns in li:
        if not ns: continue
        (key, value) = ns.split('=', 1) if ns.find('=') != -1 else (ns, '')
        value = value.replace('+', ' ')  # 空格会变成加号
        result[key] = parse.unquote(value)  # 值需要转码

    return result
