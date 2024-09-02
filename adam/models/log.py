# -*- coding:utf-8 -*-
import sys
import uuid
import types
import time
import datetime
import decimal
import logging
import traceback
from enum import Enum

from flask import request
from mongoengine import Document
from mongoengine.fields import IntField, StringField, DictField

from ..documents import ResourceDocument
from ..utils.str_util import decode2str
from ..utils.json_util import json_serializable

# 记录各变量时，排除的类型
NotRecordTypes = (types.FunctionType, types.LambdaType, types.ModuleType, type(Document), type)
# record 原有属性
RecordFields = ('name', 'levelno', 'pathname', 'module', 'funcName', 'lineno', 'threadName', 'processName', 'exc_info',
                'exc_text', 'stack_info', 'created', 'msg', 'args', 'levelname', 'filename', 'msecs', 'relativeCreated',
                'process', "asctime", "getMessage", "message", "thread", "_filter_msg", "old_msg")
# 记录 record 的属性
LogRecordFields = ('name', 'levelno', 'pathname', 'module', 'funcName', 'lineno', 'threadName', 'processName',
                   'exc_info', 'exc_text', 'stack_info', 'levelname', 'filename', 'process', "thread",)
# 内置变量
Built_in = ('<class ', '<built-in ', '<function ', '<bound method ')


def get_locals(pathname):
    """获取报错时的所有变量值
    :param pathname:报错logger所在文件名
    """
    # 获取报错时的变量
    t, v, tb = sys.exc_info()
    if tb is None:
        return {}
    frame = tb.tb_frame
    while frame and hasattr(frame, 'f_back') and pathname != frame.f_code.co_filename:
        frame = frame.f_back
    if not frame:
        return {}

    # 获取打印 logger 行的所有变量
    f_locals = getattr(frame, 'f_globals', {})
    f_locals.update(getattr(frame, 'f_locals', {}))
    result = {}
    for k, v in f_locals.items():
        # 内置变量、类型， 去掉
        if k.startswith('__') or type(v) in NotRecordTypes:
            continue
        if repr(v).startswith(Built_in):
            continue
        # 全大写的，一般是全局变量，去掉
        if isinstance(k, str) and k == k.upper():
            continue
        result[k] = v
    return repr_value(result)


def get_record_extra(record):
    """获取record记录的额外参数
    :param record: 日志record
    """
    result = {}
    for name in dir(record):
        if name in RecordFields or name.startswith('__'):
            continue
        value = getattr(record, name, None)
        if type(value) in NotRecordTypes or repr(value).startswith(Built_in):
            continue
        result[name] = value
    return repr_value(result)


def repr_value(value):
    """
    格式化变量，以便数据库存储
    其中 list,tuple,set,dict 等类型需要递归转变
    :param {任意} value 将要被格式化的值
    :return {type(value)}: 返回原本的参数类型(list,tuple,set,dict等类型会保持不变)
    """
    if value is None:
        return None
    # 一般类型
    if isinstance(value, (str, bytes, bytearray, bool, int, float, complex, list, tuple, set, Enum,
                          time.struct_time, datetime.datetime, datetime.date, decimal.Decimal, uuid.UUID)):
        return json_serializable(value)
    # dict 类型,递归转换(字典里面的 key 也会转成 unicode 编码)
    if isinstance(value, dict):
        this_value = {}  # 不能改变原参数
        for key1, value1 in value.items():
            # 字典里面的 key 也转成 unicode 编码
            key1 = repr_value(key1).replace('.', '。').replace('$', '¥')
            this_value[key1] = repr_value(value1)
        return this_value
    # model 对象，友好显示出来
    elif isinstance(value, Document):
        return 'Document:' + str(value.pk)
    # request 请求，记录详情
    elif value is request:
        try:
            return dict(method=request.method, url=request.full_path, headers=dict(request.headers),
                        ip=request.headers.getlist("X-Forwarded-For") or request.remote_addr,
                        body=decode2str(request.data), endpoint=request.endpoint
                        )
        except:
            return repr(value)
    # LogRecord
    elif isinstance(value, logging.LogRecord):
        _v = {k: getattr(value, k, None) for k in LogRecordFields}
        _v['message'] = getattr(value, 'old_msg', value.getMessage())
        return _v
    # 其它类型
    else:
        return repr(value)


class Log(ResourceDocument):
    """Log Model."""
    meta = {
        'collection': 'log',
    }

    name = StringField()  # logger 名称
    level = IntField()  # 日志级别，跟 logging 的级别一样的数值
    message = StringField()  # 日志内容

    file_path = StringField()  # 写日志的代码所在文件的路径
    module = StringField()  # 写日志的代码所在的 module
    func_name = StringField()  # 写日志的代码所在的 函数名
    line_no = IntField()  # 写日志的代码所在文件的 行数
    thread_name = StringField()  # 写日志的代码所在的 线程名
    process_name = StringField()  # 写日志的代码所在的 进程名

    exc_info = StringField()  # 抛出的Exception
    exc_text = StringField()  # 错误信息的堆栈
    stack_info = StringField()
    f_locals = DictField()  # 出错时的各变量key/value

    @classmethod
    def add(cls, record, msg=None):
        """写日志
        :param record: logging record
        :param msg: 日志内容
        """
        try:
            # 过滤 bad request 请求日志
            if record.name == "werkzeug" and record.module == "_internal" and record.funcName == "_log":
                return
            obj = cls()
            obj.name = record.name
            obj.level = record.levelno
            obj.file_path = record.pathname
            obj.module = record.module
            obj.func_name = record.funcName
            obj.line_no = record.lineno
            obj.thread_name = record.threadName
            obj.process_name = record.processName
            obj.message = msg or record.getMessage()
            for m in ("403: Forbidden", '账户或密码错误', '邮箱服务器配置不正确', '需要pop3配置信息', '需要imap配置信息'):
                if m in obj.message:
                    return
            obj.exc_info = str(record.exc_info) if record.exc_info else None
            obj.exc_text = str(record.exc_text) if record.exc_text else None
            if record.levelno >= 40:
                obj.f_locals = get_locals(record.pathname)
            if record.exc_info or obj.f_locals:
                obj.exc_text = obj.exc_text or traceback.format_exc()
            # 约定额外赋值
            extra = get_record_extra(record)
            if extra:
                f_locals = obj.f_locals or {}
                f_locals.update(extra)
                obj.f_locals = f_locals
            obj.stack_info = str(record.stack_info) if record.stack_info else None
            obj.created_at = datetime.datetime.fromtimestamp(record.created)
            obj.save(force_insert=True)
        # 避免写日志的错误影响其它代码
        except Exception as e:
            print('数据库日志记录异常:', e)
            print(traceback.format_exc())
