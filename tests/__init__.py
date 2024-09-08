# -*- coding:utf-8 -*-
"""
单元测试模块
"""

import os
import sys
import logging
import unittest

# 导入环境
CURRENT_DIR, _ = os.path.split(os.path.abspath(__file__))
CURRENT_DIR = CURRENT_DIR or os.getcwd()  # 当前目录
SOURCE_PATH = os.path.abspath(os.path.dirname(CURRENT_DIR))  # 上上一层目录，认为是源目录

if SOURCE_PATH not in sys.path:
    sys.path.append(SOURCE_PATH)

# 日志配置
LOGGER_FORMAT = "[%(asctime)s] [%(module)s.%(funcName)s:%(lineno)s] %(levelname)s: %(message)s"
logging.basicConfig(level=logging.DEBUG, format=LOGGER_FORMAT)


def setUpClass(cls):
    """测试这个类前的初始化动作"""
    logging.info('--------------------- %s 类的测试开始 -----------------', cls.__name__)


def tearDownClass(cls):
    """测试这个类所有函数后的结束动作"""
    logging.info('--------------------- %s 类的测试结束 -----------------\r\n', cls.__name__)


def setUp(self):
    """初始化"""
    self.class_name = self.__class__.__name__
    logging.info('%s 类的 %s 函数测试开始...', self.class_name, self._testMethodName)


def tearDown(self):
    """销毁"""
    self.class_name = self.__class__.__name__
    logging.info('%s 类的 %s 函数测试完毕。。。\r\n', self.class_name, self._testMethodName)


# 修改 unittest.TestCase 的 setUp / tearDown 函数, 以便添加默认的 初始化及销毁函数
setattr(unittest.TestCase, 'setUpClass', classmethod(setUpClass))
setattr(unittest.TestCase, 'tearDownClass', classmethod(tearDownClass))
setattr(unittest.TestCase, 'setUp', setUp)
setattr(unittest.TestCase, 'tearDown', tearDown)
