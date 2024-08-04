# -*- coding: utf-8 -*-

import json


class CommonException(Exception):
    def __init__(self, code, message):
        self._code = code
        self._message = message

    @property
    def message(self):
        return self._message

    @property
    def code(self):
        return self._code


class BussinessCommonException(Exception):
    def __init__(self, code, message, status_code=400, data=None):
        self._code = code
        self._message = message
        self._status_code = status_code
        self._data = data or dict()

    @property
    def message(self):
        return self._message

    @property
    def code(self):
        return self._code

    @property
    def status_code(self):
        return self.status_code

    @property
    def data(self):
        return self._data

    def __str__(self):
        result = {
            'code': self._code,
            'message': self._message,
            'data': self.data
        }
        return json.dumps(result)
