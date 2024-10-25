# -*- coding:utf-8 -*-
"""
string Utility
"""
import re
import sys
import gzip
import zlib
import json
import base64


# string encoding, try to encode str or decode bytes by this list
DECODE_CODING_LIST = ['utf-8', 'gbk', 'big5', 'gb18030', 'Shift_JIS', 'EUC-JP']
ENCODE_CODING_LIST = ['big5', 'gb18030', 'Shift_JIS', 'EUC-JP', 'utf-8']
default_code = sys.getdefaultencoding()
if default_code not in DECODE_CODING_LIST:
    DECODE_CODING_LIST.append(default_code)
if default_code not in ENCODE_CODING_LIST:
    ENCODE_CODING_LIST[-1:-1] = [default_code]


def decode2str(content, **kwargs):
    """change str, bytes or bytearray to str"""
    if content is None:
        return None
    if isinstance(content, (bytes, bytearray)):
        try:
            return content.decode()
        # 特殊类型编码，尝试解码
        except UnicodeDecodeError as e:
            return to_utf8_str(content)
    return content


def encode2bytes(content):
    """change str to bytes"""
    if content is None:
        return None
    if isinstance(content, str):
        try:
            return content.encode()
        # 特殊类型编码，尝试解码
        except UnicodeEncodeError as e:
            return to_utf8_bytes(content)
    return content


def to_utf8_str(content):
    """change str, bytes or bytearray to utf-8 str"""
    if content is None:
        return None
    if isinstance(content, (bytes, bytearray)):
        # unicode-escape
        if '\\u' in str(content):
            try:
                return content.decode('unicode-escape').encode().decode()
            except (UnicodeEncodeError, UnicodeDecodeError) as e:
                pass
        # try code list
        for encoding in DECODE_CODING_LIST:
            try:
                value = content.decode(encoding)
                if encoding == 'utf-8':
                    return value
                else:
                    return value.encode().decode()  # change to utf-8 string
            except (UnicodeEncodeError, UnicodeDecodeError) as e:
                pass
        # If that fails, ignore error messages
        return content.decode("utf-8", "ignore")
    elif isinstance(content, str):
        # unicode-escape
        try:
            try_s = [ord(a) for a in content if ord(a) <= 256]
            if len(try_s) == len(content):
                return bytes(try_s).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            pass
        # try code list
        for encoding in ENCODE_CODING_LIST:
            try:
                value = content.encode(encoding)
                return value.decode()
            except (UnicodeEncodeError, UnicodeDecodeError) as e:
                pass
        # If that fails, ignore error messages
        return content.encode('utf-8', 'ignore').decode()
    return content


def to_utf8_bytes(content):
    """change str to utf-8 bytes"""
    if content is None:
        return None
    if isinstance(content, str):
        # unicode-escape
        try_s = [ord(a) for a in content if ord(a) <= 256]
        if len(try_s) == len(content):
            return bytes(try_s)
        # try code list
        for encoding in ENCODE_CODING_LIST:
            try:
                value = content.encode(encoding)
                if encoding == 'utf-8':
                    return value
                else:
                    return value.decode().encode()  # change to utf-8 bytes
            except (UnicodeEncodeError, UnicodeDecodeError) as e:
                pass
        # If that fails, ignore error messages
        content = content.encode('utf-8', 'ignore')
    return content


def base64_encode(s):
    """使用base64加密"""
    s = encode2bytes(s)
    res = base64.b64encode(s)
    return decode2str(res)


def base64_decode(s):
    """使用base64解码"""
    s = encode2bytes(s)
    res = base64.b64decode(s)
    return decode2str(res)


def gzip_encode(content):
    """
    使用 gzip 压缩字符串
    :param {string} content: 明文字符串
    :return {string}: 压缩后的字符串
    """
    if not isinstance(content, (str, bytes, bytearray)):
        from .json_util import json_serializable
        content = json.dumps(json_serializable(content))
    if isinstance(content, str):
        content = encode2bytes(content)
    return gzip.compress(content)


def gzip_decode(content):
    """
    使用 gzip 解压字符串
    :param {string} content: 压缩后的字符串
    :return {string}: 解压出来的明文字符串
    """
    content = encode2bytes(content)
    res = gzip.decompress(content)
    return decode2str(res)


def zlib_encode(content):
    """
    使用 zlib 压缩字符串
    :param {string} content: 明文字符串
    :return {string}: 压缩后的字符串
    """
    if not isinstance(content, (str, bytes, bytearray)):
        from .json_util import json_serializable
        content = json.dumps(json_serializable(content))
    if isinstance(content, str):
        content = encode2bytes(content)
    return zlib.compress(content, zlib.Z_BEST_COMPRESSION)


def zlib_decode(content):
    """
    使用 zlib 解压字符串
    :param {string} content: 压缩后的字符串
    :return {string}: 解压出来的明文字符串
    """
    content = encode2bytes(content)
    res = zlib.decompress(content)
    return decode2str(res)


def is_phone(value):
    """
    检查是否是手机号码: 11位数字
    """
    return re.match(r'1[3-9]\d{9}', value)


def is_email(value):
    """
    检查是否是邮箱地址
    """
    return re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", value)
