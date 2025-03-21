# -*- coding: utf-8 -*-
import os
from .import_util import import_string


class Config(object):
    """配置类，将 dict 转成 Object"""
    def __init__(self, values=None, default=None):
        self._values = {}
        self._default = default
        if values:
            self.add_values(values)

    def __getattr__(self, name, default=None):
        # 默认取环境变量
        name = name.upper()
        value = self._values.get(name) or os.environ.get(name) or default or self._default
        setattr(self, name, value)
        return value

    def set_key_value(self, key, value):
        if key.startswith('__'):
            return
        if not key.isupper():  # 注意： "__AD32__".isupper() 为 True
            return
        if isinstance(value, (int, float, str, bool, list, tuple)):
            self._values[key] = value
            setattr(self, key, value)
        # dict 合并，但不递归
        elif key in self._values and isinstance(value, dict) and isinstance(self._values[key], dict):
            self._values[key].update(value)
            setattr(self, key, self._values[key])
        # 是一个类，逐个属性填充
        elif type(value).__name__ == 'type' and type(self._values.get(key)).__name__ == 'type':
            origin_object = self._values.get(key)
            for k in dir(value):
                if k.startswith('__'):
                    continue
                setattr(origin_object, k, getattr(value, k))
        else:
            self._values[key] = value
            setattr(self, key, value)

    def add_values(self, values):
        if isinstance(values, dict):
            for key, value in values.items():
                self.set_key_value(key, value)
        elif isinstance(values, str):
            objs = import_string(values)
            for key in dir(objs):
                value = getattr(objs, key)
                self.set_key_value(key, value)
        # 是一个 类/模块
        elif type(values).__name__ in ('type', 'module'):
            for key in dir(values):
                value = getattr(values, key)
                self.set_key_value(key, value)

    def to_dict(self):
        return self._values


# makes an instance of the Config helper class available to all the modules
config = Config()

