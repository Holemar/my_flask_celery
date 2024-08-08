#!python
# -*- coding:utf-8 -*-
"""
公用函数(rc4加密)，兼容py2及py3
Created on 2014/5/26
Updated on 2024/08/03
@author: Holemar
"""
import sys

__all__ = ("decode", 'encode', 'encode_symmetrical', 'decode_symmetrical')


def RC4(data, key):
    """rc4加密的核心算法"""
    x = 0
    box = list(range(256))
    for i in list(range(256)):
        x = (x + box[i] + ord(key[i % len(key)])) % 256
        box[i], box[x] = box[x], box[i]
    x = 0
    y = 0
    out = []
    for char in data:
        x = (x + 1) % 256
        y = (y + box[x]) % 256
        box[x], box[y] = box[y], box[x]
        out.append(chr(ord(char) ^ box[(box[x] + box[y]) % 256]))
    return ''.join(out)


def hex2str(s):
    """16进制转字符串"""
    if s[:2] in ('0x', '0X'):
        s = s[2:]
    res = []
    for i in list(range(0, len(s), 2)):
        hex_dig = s[i:i + 2]
        res.append(chr(int(hex_dig, base=16)))
    return ''.join(res)


def str2hex(input_str):
    """字符串转16进制"""
    res = []
    for s in input_str:
        hex_dig = hex(ord(s))[2:]
        if len(hex_dig) == 1:
            hex_dig = "0" + hex_dig
        res.append(hex_dig)
    return ''.join(res)


def decode(rc4_txt, key):
    """
    将rc4加密后的密文，解密出来
    :param {string} rc4_txt: RC4加密后的密文
    :param {string} key: 加密/解密的key值
    :return {string}: 返回解密后的明文
    """
    if not rc4_txt:
        return rc4_txt
    if not key:
        raise RuntimeError(u'缺少解密的key!')
    rc4_txt = to_str(rc4_txt)
    key = to_str(key)
    real_text = RC4(hex2str(rc4_txt), key)
    try:
        unicode # py2
        return real_text
    except NameError: # py3
        b = bytes((ord(s) for s in real_text))
        return b.decode()


def encode(real_text, key):
    """
    将明文字符串，用RC4加密成密文
    :param {string} real_text: 明文的字符串
    :param {string} key: 加密/解密的key值
    :return {string}: 返回加密后的密文
    """
    if not real_text:
        return real_text
    if not key:
        raise RuntimeError(u'缺少加密的key!')
    real_text = to_str(real_text)
    key = to_str(key)
    rc4_txt = str2hex(RC4(real_text, key))
    return rc4_txt


system_encoding = "utf-8"
defaultencoding = sys.getdefaultencoding()


def to_str(text):
    """
    中文转换，将 unicode、gbk、big5 编码转成 str 编码(utf-8)
    :param {string} text: 原字符串
    :return {string}: 返回转换后的字符串
    """
    try:
        if isinstance(text, unicode):
            return text.encode(system_encoding)
        elif isinstance(text, str):
            # 没有中文，不必处理编码
            if text.isalnum():
                return text
            text = to_unicode(text)
            return text.encode(system_encoding)
        else:
            return str(text)
    except NameError:
        # py3 的处理
        text = to_unicode(text)
        return text.encode().decode("unicode-escape")


def to_unicode(text):
    """
    中文转换，将 unicode、gbk、big5 编码转成 unicode 编码
    :param {string} text: 原字符串
    :return {string}: 返回转换后的字符串
    """
    try:
        if isinstance(text, unicode):
            return text
    except NameError:
        # py3 的处理
        return text

    try:
        return text.decode(system_encoding)  # 如果这句执行没报异常，说明是 utf-8 编码，不用再转换
    except:
        # py2 的处理
        encoding_tuple = ("gbk", "big5", defaultencoding) if defaultencoding and isinstance(defaultencoding, basestring) else ("gbk", "big5")
        for encoding in encoding_tuple:
            try:
                return text.decode(encoding) # 如果这句执行没报异常，说明是这种编码
            except:
                pass

    return unicode(text)


def encode_symmetrical(data, key):
    """
    将明文字符串，加密成密文(按字符逐个对应加密)
    :param {string} data: 明文的字符串
    :param {string} key: 加密/解密的key值
    :return {string}: 返回加密后的密文
    """
    if not data:
        return data
    if not key:
        raise RuntimeError(u'缺少加密的key!')
    # 有中文，需要处理编码
    if not data.isalnum():
        data = to_unicode(data)
    result = []
    for d in data:
        value = encode(d, key)
        if len(value) > 2:
            value = '/%s/' % value
        result.append(value)
    return ''.join(result)


def decode_symmetrical(data, key):
    """
    将加密后的密文，解密出来(按字符逐个对应解密)
    :param {string} data: RC4加密后的密文
    :param {string} key: 加密/解密的key值
    :return {string}: 返回解密后的明文
    """
    if not data:
        return data
    if not key:
        raise RuntimeError(u'缺少解密的key!')
    result = []
    index = 0
    length = len(data)
    while index < length:
        if '/' == data[index]:
            end = data.index('/', index+1) + 1
            value = data[index+1:end-1]
        else:
            end = index+2
            value = data[index:end]
        value = decode(value, key)
        result.append(value)
        index = end
    return ''.join(result)


if __name__ == "__main__":
    key = "1bb762f7ce24ceee"

    # 英文加密测试
    txt = 'abc321cc55+-*/,.,.dfdehryz908&^%$#@!~*()_+-='
    secret_txt = encode(txt, key)
    assert decode(secret_txt, key) == txt

    # 中文加密测试
    txt2 = '哈哈5+-*/,.,.dfd08&^%$#@!~*()_+-='
    secret_txt = encode(txt2, key)
    assert decode(secret_txt, key) == txt2

    # 英文逐个字符加密测试
    txt3 = 'abc321cc55+-*/,.,.dfdehryz908&^%$#@!~*()_+-='
    secret_txt = encode_symmetrical(txt3, key)
    assert decode_symmetrical(secret_txt, key) == txt3

    # 中文逐个字符加密测试
    txt4 = '哈哈5+-*/,.,.dfd08&^%$#@!~*()_+-='
    secret_txt = encode_symmetrical(txt4, key)
    assert decode_symmetrical(secret_txt, key) == txt4
