# -*- coding:utf-8 -*-

import os
import sys
import logging

# 导入环境
CURRENT_DIR, _ = os.path.split(os.path.abspath(__file__))
CURRENT_DIR = CURRENT_DIR or os.getcwd()  # 当前目录
SOURCE_PATH = os.path.abspath(os.path.dirname(CURRENT_DIR))  # 上一层目录，认为是源目录

if SOURCE_PATH not in sys.path:
    sys.path.append(SOURCE_PATH)

# 日志配置
LOGGER_FORMAT = "[%(asctime)s] [%(funcName)s:%(lineno)s] %(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOGGER_FORMAT)

