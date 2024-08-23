#!python
# -*- coding:utf-8 -*-
"""
公用函数(字符串处理) html_util.py 的测试
Created on 2015/1/19
Updated on 2024/8/21
@author: Holemar
"""
import logging
import unittest

from adam.utils import html_util


class TestXhtml(unittest.TestCase):
    # html 测试
    def test_html(self):
        logging.info(u'测试 html_util')
        self.assertEqual(html_util.to_html("  &%<>\n\r\n"), '&nbsp;&nbsp;&amp;&#37;&lt;&gt;\n<br/>\r\n<br/>')
        self.assertEqual(html_util.to_html("""'"+"""), '&#x27;&quot;&#43;')
        self.assertEqual(html_util.to_text('&nbsp;xx&nbsp;&#37;&LT;a&#60;&gt;&#39;&#43;&#160;'), " xx %<a<>'+ ")
        self.assertEqual(html_util.to_text('&AMP;1&#38;&#601;&hellip;&rsquo;&lsquo;<br/><br>'), "&1&ə…’‘\r\n\r\n")
        self.assertEqual(html_util.remove_html("x<div>haha</div>x"), "xhahax")
        self.assertEqual(html_util.remove_html("""x<div>haha</div>x<!--点点滴滴-->啊啊
        <style>body {margin: 0;}</style>
        <script type="text/javascript" src="/manifest.2be1e4cb32664bc84cf0.js"></script>
        <script type="text/javascript"> function ...</script>"""),
                         "xhahax啊啊")

    def test_change_utf8_meta(self):
        logging.info(u'测试 编码转换')
        html = "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=gb2312\">你好：<br>阳江招聘网【YJRC.NET】求职用户发给贵公司的求职简历<br><b>应聘职位：行政专员/助理</b><br><b>姓名：黄永清</b><br><b>联系电话：13168189036/13168189036</b><br><b>以下是本人工作经历：</b><br>2010年7月--2012年3月中山欧普照明，从事订单管理和客服！\r\n2012年4月--2014年1月广州聚晶能源科技有限公司，先后从事销售助理兼总经理助理，华南区域销售代表！\r\n2016年7月--2019年1月金维纳硅藻泥担任店长工作。\r\n2019年9月--2020年4月爱婴岛儿童百货担任店长。<br><br>如果邮件不支持Html方式查看，请点击<a href=\"http://www.yjrc.net/person/person_html.aspx?pid=101539\">查看个人简历</a> http://www.yjrc.net/person/person_html.aspx?pid=101539<br> 阳江招聘网http://www.yjrc.net<br>（注：这是由系统自动发出的邮件，请不要直接回复！）<br><a href=\"http://yjrc.net/info/contact.aspx\">邮件退订</a>\r\n\r\n"
        html2 = "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"/>你好：<br>阳江招聘网【YJRC.NET】求职用户发给贵公司的求职简历<br><b>应聘职位：行政专员/助理</b><br><b>姓名：黄永清</b><br><b>联系电话：13168189036/13168189036</b><br><b>以下是本人工作经历：</b><br>2010年7月--2012年3月中山欧普照明，从事订单管理和客服！\r\n2012年4月--2014年1月广州聚晶能源科技有限公司，先后从事销售助理兼总经理助理，华南区域销售代表！\r\n2016年7月--2019年1月金维纳硅藻泥担任店长工作。\r\n2019年9月--2020年4月爱婴岛儿童百货担任店长。<br><br>如果邮件不支持Html方式查看，请点击<a href=\"http://www.yjrc.net/person/person_html.aspx?pid=101539\">查看个人简历</a> http://www.yjrc.net/person/person_html.aspx?pid=101539<br> 阳江招聘网http://www.yjrc.net<br>（注：这是由系统自动发出的邮件，请不要直接回复！）<br><a href=\"http://yjrc.net/info/contact.aspx\">邮件退订</a>\r\n\r\n"
        self.assertEqual(html_util.change_utf8_meta(html), html2)

        html = "<html>\r\n<head>\r\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=gb2312\">\r\n<meta name=\"viewport\" content=\"width=device-width, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no\">\r\n</head>\r\n<body>\r\n\r\n</body>\r\n</html>\r\n"
        html2 = "<html>\r\n<head>\r\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"/>\r\n<meta name=\"viewport\" content=\"width=device-width, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no\">\r\n</head>\r\n<body>\r\n\r\n</body>\r\n</html>\r\n"
        self.assertEqual(html_util.change_utf8_meta(html), html2)

        html = "<html>\r\n<head>\r\n<meta content=\"text/html; charset=gbk\">\r\n<meta name=\"viewport\" content=\"width=device-width, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no\">\r\n</head>\r\n<body>\r\n\r\n</body>\r\n</html>\r\n"
        html2 = "<html>\r\n<head>\r\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"/>\r\n<meta name=\"viewport\" content=\"width=device-width, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no\">\r\n</head>\r\n<body>\r\n\r\n</body>\r\n</html>\r\n"
        self.assertEqual(html_util.change_utf8_meta(html), html2)

        html = """<html>\r\n<head>
            <meta content='text/html; charset=gbk'/>
        <meta name=\"viewport\" content=\"width=device-width, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no\">
        </head>\r\n<body>\r\n\r\n</body>\r\n</html>\r\n"""
        html2 = """<html>\r\n<head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
        <meta name=\"viewport\" content=\"width=device-width, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no\">
        </head>\r\n<body>\r\n\r\n</body>\r\n</html>\r\n"""
        self.assertEqual(html_util.change_utf8_meta(html), html2)

        html = "<html>\r\n<head>\r\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\r\n<meta content=\"text/html; charset=gb2312\">\r\n</head>\r\n<body>\r\n</body>\r\n</html>\r\n"
        html2 = "<html>\r\n<head>\r\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\r\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"/>\r\n</head>\r\n<body>\r\n</body>\r\n</html>\r\n"
        self.assertEqual(html_util.change_utf8_meta(html), html2)

        html = "<!DOCTYPE html>\r\n<html xmlns=\"http://www.w3.org/1999/xhtml\">\r\n<head>\r\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=gb2312\">\r\n<meta name=\"viewport\" content=\"width=device-width, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no\">\r\n<title>尊敬的猎聘用户冯光，您收到了新的应聘简历。</title>\r\n</head>\r\n<body>\r\n\r\n</body>\r\n</html>\r\n"
        html2 = "<!DOCTYPE html>\r\n<html xmlns=\"http://www.w3.org/1999/xhtml\">\r\n<head>\r\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"/>\r\n<meta name=\"viewport\" content=\"width=device-width, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no\">\r\n<title>尊敬的猎聘用户冯光，您收到了新的应聘简历。</title>\r\n</head>\r\n<body>\r\n\r\n</body>\r\n</html>\r\n"
        self.assertEqual(html_util.change_utf8_meta(html), html2)

    def test_get_urls(self):
        logging.info(u'测试 get_urls')
        self.assertEqual(html_util.get_urls("  &%<>\n\r\n"), {})
        self.assertEqual(html_util.get_urls("""
            <a href="http://www.baidu.com">百度</a>
            <a href="/static/css/style.css">首页样式</a>
            <A HREF='https://www.google.com/sdfsd?rwer=34&er=2ff'>谷歌</A>"""
        ), {
            'http://www.baidu.com': '百度',
            '/static/css/style.css': '首页样式',
            'https://www.google.com/sdfsd?rwer=34&er=2ff': '谷歌'
        })
        self.assertEqual(html_util.get_urls("""
            <a data-destinationLink="https://techcrunch.com/2024/08/13/made-by-google-2024-all-of-googles-reveals-from-the-pixel-9-iineup-to-gemini-ais-addition-to-everything/" data-event="recirculation" data-module="Query" href='https://techcrunch.com/2024/08/13/made-by-google-2024-all-of-googles-reveals-from-the-pixel-9-iineup-to-gemini-ais-addition-to-everything/' target="_self">Made by Google 2024: All of Google&#8217;s reveals, from the Pixel 9 lineup to Gemini AI&#8217;s addition to everything</a>
            """), {
            'https://techcrunch.com/2024/08/13/made-by-google-2024-all-of-googles-reveals-from-the-pixel-9-iineup-to-gemini-ais-addition-to-everything/': 'Made by Google 2024: All of Google’s reveals, from the Pixel 9 lineup to Gemini AI’s addition to everything',
        })


if __name__ == "__main__":
    unittest.main()

