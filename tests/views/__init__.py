# -*- coding:utf-8 -*-
"""
本目录探测项目内的view接口，不发真实请求，仅仅是为了测试接口是否正常。
"""

import logging
import unittest
from tests import SOURCE_PATH


def setUp(self):
    """初始化"""
    from main import app  # 数据库连接、模块加载等，依赖这一行
    app.load_route()  # 加载路由
    self.app = app
    # 激活测试标志
    app.config['TESTING'] = True
    # 在这里,使用flask提供的测试客户端进行测试
    self.client = app.test_client()
    self.class_name = self.__class__.__name__
    logging.info('%s 类的 %s 函数测试开始...', self.class_name, self._testMethodName)


# 修改 unittest.TestCase 的 setUp / tearDown 函数, 以便添加默认的 初始化及销毁函数
setattr(unittest.TestCase, 'setUp', setUp)
