# -*- coding: utf-8 -*-

import json


class CommonException(Exception):
    def __init__(self, code, message):
        self._code = code
        self._message = message
        super().__init__(message)

    @property
    def message(self):
        return self._message

    @property
    def code(self):
        return self._code


class BussinessCommonException(Exception):
    errors = {}  # 子项目需要对这个字典赋值

    def __init__(self, code, message, status_code=400, data=None):
        self._code = code
        self._message = message
        self._status_code = status_code
        self._data = data
        super().__init__(message)

    @property
    def message(self):
        return self._message

    @property
    def code(self):
        return self._code

    @property
    def status_code(self):
        return self._status_code

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    def __call__(self, message=None, status_code=400, data=None):
        if message:
            self._message = message
        if status_code:
            self._status_code = status_code
        if data:
            self._data = data
        raise self


class CodeType(type):
    def __new__(cls, name, bases, attrs):
        attrs_value = {}
        ERROR = {}
        for k, v in attrs.items():
            if k.startswith('__'):
                continue
            if isinstance(v, (tuple, list)) and len(v) >= 2:
                code, error_msg = v[:2]
                attrs_value[k] = BussinessCommonException(*v)
                ERROR[code] = error_msg
            else:
                attrs_value[k] = v

        obj = type.__new__(cls, name, bases, attrs_value)
        BussinessCommonException.errors.update(ERROR)
        return obj

