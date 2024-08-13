# -*- coding:utf-8 -*-
"""
json Utility
"""
import os
import json
import uuid
import time
import datetime
import logging
import decimal
from enum import Enum
from .str_util import decode2str

# base file path, for found files
BASE_PATH = os.getcwd()


def load_json(value):
    """
    change strings to json
    :param value: string
    :return: json dict
    """
    if value is None:
        return None

    if isinstance(value, (bytes, bytearray)):
        value = decode2str(value)
    if not isinstance(value, str):
        return None

    try:
        return json.loads(value)
    except ValueError as e:
        pass

    # Maybe that's a python value
    try:
        # fix json works: true, false, null ...
        true = True
        false = False
        null = None
        return eval(value)
    except Exception as e:
        return None


def load_json_file(file_path):
    """
    read file to json
    :param file_path: file path
    :return: json dict
    """
    if not os.path.isfile(file_path):
        if file_path.startswith('/'):
            return None
        else:
            file_path = os.path.join(BASE_PATH, file_path)
            if not os.path.isfile(file_path):
                return None

    with open(file_path, 'r', encoding='utf-8') as load_f:
        value = load_f.read()
        return load_json(value)
    return None


def json_serializable(value):
    """
    change the stings in (list, tuple, set, dict) to unicode
    :param value: dict,list,tuple,set
    :return {type(value)}:
    """
    if value is None:
        return None
    elif isinstance(value, (bytes, bytearray)):
        return decode2str(value)
    # str/unicode
    elif isinstance(value, str):
        return value
    elif isinstance(value, (bool, int, float, complex)):
        return value
    # time, datetime to str
    elif isinstance(value, time.struct_time):
        return time.strftime('%Y-%m-%dT%H:%M:%S', value)
    elif isinstance(value, datetime.datetime):
        return value.strftime('%Y-%m-%dT%H:%M:%S')
    elif isinstance(value, datetime.date):
        return value.strftime('%Y-%m-%d')
    elif isinstance(value, decimal.Decimal):
        return float(value)
    elif isinstance(value, uuid.UUID):
        return value.hex
    elif isinstance(value, Enum):
        return value.value
    # list,tuple,set recursion
    elif isinstance(value, (list, tuple, set)):
        arr = [json_serializable(item) for item in value]
        return arr
    # dict recursion(the key in dict will change to str too)
    elif isinstance(value, dict):
        this_value = {}  # do not change the type
        for key1, value1 in value.items():
            key1 = json_serializable(key1)
            this_value[key1] = json_serializable(value1)
        return this_value
    else:
        return str(value)


class CustomJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time and decimal types.
    """
    def default(self, o):
        return json_serializable(o)


def dump_json_file(json_value, file_path):
    """
    write json content to a file
    :param json_value: json content
    :param file_path: str
    :return: True if write success, else False
    """
    try:
        json_value = json_serializable(json_value)
        # 没有文件的目录，则先创建目录，避免因此报错
        file_dir = os.path.dirname(file_path)
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir)
        with open(file_path, 'w', encoding='utf-8') as dump_file:
            json.dump(json_value, dump_file, indent=1, ensure_ascii=False)
    except Exception as e:
        logging.error('write a json file error:%s', e, exc_info=True)
    return True

