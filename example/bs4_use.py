# -*- coding: utf-8 -*-
"""
BeautifulSoup 是用于解析HTML和XML的库。
它提取标签文本、属性，使用CSS选择器和处理特殊标签等内容。

安装： pip install beautifulsoup4
使用教程: https://beautifulsoup.readthedocs.io/zh-cn/v4.4.0/
https://blog.csdn.net/love666666shen/article/details/77512353
"""
import re
from bs4 import BeautifulSoup

# 待解析的HTML内容
html_content = """
<html>
<head>
    <title>The Dormouse's story</title>
</head>
<body>
<p class="title aq">
    <b>
        The Dormouse's story
    </b>
</p>
<p class="story">Once upon a time there were three little sisters; and their names were
    <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
    <a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> 
    and
    <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
    and they lived at the bottom of a well.
</p>
<p class="story">...</p>
"""

soup = BeautifulSoup(html_content, 'html.parser')
# soup = BeautifulSoup(html_content, 'html.parser', from_encoding='GB2312')  # 需要指定编码时

"""
解析器比较"
解析器 | 使用方法 | 优势 | 劣势
--- | --- | --- | ---
Python标准库 | BeautifulSoup(markup, "html.parser") | Python的内置标准库,执行速度适中,文档容错能力强 | Python 2.7.3 or 3.2.2 以前的版本，文档容错能力差
lxml HTML 解析器 | BeautifulSoup(markup, "lxml") | 速度快,文档容错能力强 | 需要安装C语言库
lxml XML 解析器 | BeautifulSoup(markup, ["lxml", "xml"]) BeautifulSoup(markup, "xml") | 速度快, 唯一支持XML的解析器 | 需要安装C语言库
html5lib | BeautifulSoup(markup, "html5lib") | 最好的容错性,以浏览器的方式解析文档,生成HTML5格式的文档 | 速度慢
"""

# """
print(type(soup))  # <class 'bs4.BeautifulSoup'>
# BeautifulSoup 实例，可以直接点出来标签， 但只是第一个标签


'''
搜索文档树
'''
print(soup.find("div", class_="articleExcerpt"))  # 按 class 属性查找，需要写 "class_"
print(soup.select('article ul li a'))  # 按 CSS 选择器查找，返回 A 标签的列表
print(soup.select_one('article ul li a'))  # 返回搜索到的第一个 A 标签对象

# find_all 输出所有的 a 标签，以列表形式显示
print(soup.find_all('a'))  # [<a href="http://www.baidu.com/" id="link1" name="百度">Elsie</a>, <a class="sister" href="http://example.com/lacie" id="link2">Lacie</a>, <a class="sister" href="http://example.com/tillie" id="link3">Tillie</a>]

# find 输出第一个 按标签及属性到找的  标签
print(soup.find(id="link3"))  # <a class="sister" href="http://example.com/tillie" id="link3">Tillie</a>
print(soup.find("a", id="link2"))  # <a class="sister" href="http://example.com/lacie" id="link2">Lacie</a>
print(soup.find("a"))  # <a href="http://www.baidu.com/" id="link1" name="百度">Elsie</a>

for link in soup.find_all('a'):
    # 获取 link 的  href 属性内容
    print(link.get('href'))

# 正则匹配，名字中带有b的标签
for tag in soup.find_all(re.compile("b")):
    print(tag.name)

# CSS选择器
print(list(soup.select('p.story a')))  # []
# 只取一个标签
print(soup.select_one('p.title b'))  # <b>\n\t\tThe Dormouse's story\n\t</b>



# 输出第一个 title 标签
print('title:', soup.title)  # <title>The Dormouse's story</title>
# 输出第一个 head 标签
print('head:', soup.head)  # <head><title>The Dormouse's story</title></head>
# 输出第一个 p 标签
print(soup.p)  # <p class="title aq">\n\t<b>\n\t\tThe Dormouse's story\n\t</b>\n</p>


# 标签的类型 Tag, 它有两个重要的属性，是 name 和 attrs
print(type(soup.p))  # <class 'bs4.element.Tag'>

# 标签的名称
print('title.name:',  soup.title.name)  # title
print('p.name:',  soup.p.name)  # p

# 标签的所有属性信息
print('title.attrs:', soup.title.attrs)  # {}
print('p.attrs:', soup.p.attrs)  # {'class': ['title', 'aq']}

# 标签的 属性内容
print(soup.p['class'])  # ['title', 'aq']
print(soup.a['href'])  # http://example.com/elsie

# 标签的包含内容
print('title.string:',  soup.title.string)  # The Dormouse's story

# 获取所有文字内容
print(soup.get_text())  # \n\n\nThe Dormouse's story\n\n\n\n\n        The Dormouse's story\n    \n\nOnce upon a time there were three little sisters; and their names were\n    Elsie,\n    Lacie \n    and\n    Tillie;\n    and they lived at the bottom of a well.\n\n...\n

print('p.string:',  soup.p.string)  # None
print('p.get_text():',  soup.p.get_text())  # "\n\n        The Dormouse's story\n    \n"

print('b.string:',  soup.b.string)  # "\n        The Dormouse's story\n    "
print('b.get_text():',  soup.b.get_text())  # "\n        The Dormouse's story\n    "

# stripped_strings 可以去除多余空白内容。但它是个迭代器，需要用list()转换成列表
print('p.stripped_strings', list(soup.p.stripped_strings))  # ["The Dormouse's story"]
print('b.stripped_strings', list(soup.b.stripped_strings))  # ["The Dormouse's story"]


'''
soup的属性可以被添加,删除或修改. soup的属性操作方法与字典一样
'''
print('*' * 50)
print(soup.a)  # <a class="sister" href="http://example.com/elsie" id="link1">Elsie</a>
print(soup.a.attrs)  # {'class': ['sister'], 'href': 'http://example.com/elsie', 'id': 'link1'}

# 修改第一个 a 标签的href属性
soup.a['href'] = 'http://www.baidu.com/'

# 给第一个 a 标签添加 name 属性
soup.a['name'] = u'百度'

# 删除第一个 a 标签的 class 属性为
del soup.a['class']

print(soup.a)  # <a href="http://www.baidu.com/" id="link1" name="百度">Elsie</a>
print(soup.a.attrs)  # {'href': 'http://www.baidu.com/', 'id': 'link1', 'name': '百度'}

soup.a.decompose()  # 删除节点

'''
节点查找
'''
# 标签的所有子节点
print(soup.p.contents)  # ['\n', <b>\n        The Dormouse's story\n    </b>, '\n']
# 可以用列表索引来获取它的某一个元素
print(soup.p.contents[1])  # <b>\n        The Dormouse's story\n    </b>

# 标签的父节点
print('title.parent:',  soup.title.parent.name)  # head
print('p.parent:',  soup.p.parent.name)  # body
# 标签的全部父节点 (Tag.parents 是一个生成器)
for parent in soup.p.parents:
    print(parent.name)  # body, html, [document]

# 子节点
print('p.children:',  type(soup.p.children))  # <class 'list_iterator'>
# print('p.children:',  soup.p.children[0])  # 报异常: TypeError: 'list_iterator' object is not subscriptable
print('p.children:',  list(soup.p.children)[1])  # <b>\n        The Dormouse's story\n    </b>

# 兄弟节点
# Tag.next_sibling 下一个兄弟节点
print(soup.a.next_sibling)  # ',\n    ' (文本也算节点，所以第一个兄弟节点是文本)
print(soup.a.next_sibling.next_sibling)  # <a class="sister" href="http://example.com/lacie" id="link2">Lacie</a>
# Tag.next_siblings 下一个兄弟节点的列表，是个生成器
print(list(soup.a.next_siblings))  # [',\n    ', <a class="sister" href="http://example.com/lacie" id="link2">Lacie</a>, ',\n    ', <a class="sister" href="http://example.com/tillie" id="link3">Tillie</a>, '\n']
# Tag.previous_sibling 上一个兄弟节点
print(soup.a.previous_sibling)  # 'Once upon a time there were three little sisters; and their names were\n    '
# Tag.previous_siblings 上一个兄弟节点的列表，是个生成器
print(list(soup.a.previous_siblings))  # ['Once upon a time there were three little sisters; and their names were\n    ']

# .next方法：只能针对单一元素进行.next，或者说是对contents列表元素的挨个清点。
print(soup.a.next)  # Elsie
print(soup.a.next.next)  # ',\n    '
print(soup.a.next.next.next)  # <a class="sister" href="http://example.com/lacie" id="link2">Lacie</a>

# 前后节点
# .next_element .previous_element 属性与 .next_sibling .previous_sibling 不同，它并不是针对于兄弟节点，而是在所有节点，不分层次。
print(soup.a.next_element)  # Elsie
print(soup.a.previous_element)  # Once upon a time there were three little sisters; and their names were

# 所有前后节点(返回生成器)
print(list(soup.a.next_elements))  # ['Elsie', ',\n    ', <a class="sister" href="http://example.com/lacie" id="link2">Lacie</a>, 'Lacie', ' \n    and\n    ', <a class="sister" href="http://example.com/tillie" id="link3">Tillie</a>, 'Tillie', ';\n    and they lived at the bottom of a well.\n', '\n', <p class="story">...</p>, '...', '\n']
print(list(soup.a.previous_elements))  # ...


# """

