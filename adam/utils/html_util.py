#!python
# -*- coding:utf-8 -*-
"""
公用函数(html字符串处理)
Created on 2015/1/19
Updated on 2024/8/21
@author: Holemar
"""
import re
import html
import string
from urllib.parse import quote

__all__ = ('to_html', 'to_text', 'remove_html', 'is_html_file', 'change_utf8_meta', 'to_url', 'get_urls')


def to_html(sour):
    """
    转换字符串成 Html 页面上显示的编码
    :param {string} sour: 需要转换的字符串
    :return {string}: 转换后的字符串
    @example to_html(" ") 返回: &nbsp;
    """
    sour = html.escape(sour)  # & 符号
    sour = sour.replace("\n", "\n<br/>")
    # 强转下面不会 escape 的符号
    sour = sour.replace(" ", "&nbsp;")
    sour = sour.replace("%", "&#37;")
    sour = sour.replace("+", "&#43;")
    return sour


def to_text(sour):
    """
    转换字符串由 Html 页面上显示的编码变回正常编码(与上面的方法对应)
    :param sour: 需要转换的字符串
    :return {string}:转换后的字符串
    @example to_text("&nbsp;") 返回: " "
    """
    sour = html.unescape(sour)  # & 符号
    sour = re.sub(r'\n?<[Bb][Rr]\s*/?>\n?', '\r\n', sour)  # 转换换行符号
    return sour


def remove_html(text):
    """
    清除HTML标签
    :return {string}:清除标签后的内容
    @example remove_html("<div>haha</div>") 返回: "haha"
    """
    # 清除注释
    text = text.strip().replace("<!--.*?-->", "")
    # 样式 内容删除
    text = re.sub(re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>', re.I), '', text)
    # java script 内容删除
    text = re.sub(re.compile('<\s*script[^>]*>[^<]*<\s*/\s*script\s*>', re.I), '', text)
    # 标题换行: </title> ==> 换行符
    text = re.sub(r'</[Tt][Ii][Tt][Ll][Ee]>', '\n', text)
    # tr换行: </tr> ==> 换行符
    text = re.sub(r'</[Tt][Rr]>', '\n', text)
    # html標籤清除
    text = re.sub(r'<[^>]+>', '', text)
    # 转换字符串由 Html 页面上显示的编码变回正常编码
    text = to_text(text)
    return text.strip()


def is_html_file(file_io):
    """判断文件是否html内容"""
    content = str(file_io).lower()
    value = '<html ' in content or '</html>' in content \
            or '<div ' in content or '</div>' in content \
            or '<meta ' in content or '<a ' in content
    return value


def change_utf8_meta(content):
    """将HTML页面里的 <meta>标签指定编码改成 utf-8 编码"""
    if not content:
        return content
    if not is_html_file(content):
        return content
    after_meta = '<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>'
    for code in ('gb2312', 'gbk', 'big5', 'gb18030'):
        s = '<meta +(http-equiv=[\'"]?Content-Type[\'"]?)? *content=[\'"]text/html; *charset=' + code + '[\'"] */?>'
        if re.search(s, content):
            content = re.sub(s, after_meta, content, flags=re.M + re.I)
            break
    # else:
    #     content = content + after_meta
    return content


def to_url(url):
    # url转换
    url = html.unescape(url)  # & 符号
    safe = r"""!"#$%&'+,-./:;=?@[\]^_`~"""
    url = quote(url, safe=safe+string.ascii_letters+string.digits)  # safe表示可以忽略的字符
    return url


def get_urls(html_content):
    """
    获取HTML页面里的链接
    :param {string} html_content: HTML页面内容
    :return {dict}: 链接集(key:链接, value:标题)
    """
    urls = {}  # 根据 url 去重
    pattern = re.compile(r'''<a\b[^>]*?href=['"]([^"']*?)["'][^>]*?>([^<]+?)</a>''', re.I)
    for url, title in pattern.findall(html_content):
        url = to_url(url)  # 链接，需转换
        title = to_text(title).replace(' ', '')  # 标题，可能包含特殊符号，需转码
        urls[url] = title
    return urls

