# -*- coding: utf-8 -*-
import os
import re
import logging
import inspect
import pkgutil
import importlib

logger = logging.getLogger(__name__)


class VirtualObject(object):
    """虚拟类，将 dict 转成 Object"""
    def __init__(self, values: dict = None, default=None):
        self._values = values
        self._default = default
        if values:
            for k, v in values.items():
                setattr(self, k, v)

    def __getattr__(self, name):
        return self._default

    def add_values(self, values: dict):
        for k, v in values.items():
            if not hasattr(self, k):
                setattr(self, k, v)
                self._values[k] = v
            elif isinstance(v, dict):  # dict 合并，但不递归，也不转换内嵌层级为 Object
                if k in self._values and isinstance(self._values[k], dict):
                    self._values[k].update(v)
            # 是一个类，逐个属性填充
            elif type(v).__name__ == 'type':
                origin_object = self._values.get(k)
                for key in dir(v):
                    if key.startswith('__'):
                        continue
                    if hasattr(origin_object, key):
                        continue
                    setattr(origin_object, key, getattr(v, key))

    def to_dict(self):
        return self._values


def import_submodules(package, recursive=True):
    """ Import all submodules of a module, recursively, including subpackages

    :param package: package (name or actual module)
    :type package: str | module
    :rtype: dict[str, types.ModuleType]
    """
    if isinstance(package, str):
        package = package.replace('/', '.').replace(os.sep, '.')
        package = importlib.import_module(package)
    results = {}
    for _, name, is_pkg in pkgutil.walk_packages(package.__path__):
        if name.startswith('_'):
            continue
        full_name = package.__name__ + '.' + name
        try:
            results[full_name] = importlib.import_module(full_name)
        except Exception as e:
            logger.exception('Failed to import %s: %s', full_name, e)
        if recursive and is_pkg:
            results.update(import_submodules(full_name))
    return results


def discovery_items_in_package(package, func_lookup=inspect.isfunction):
    """
        discovery all function at most depth(2) in specified package
    """
    functions = []
    _modules = import_submodules(package)
    for _k, _m in _modules.items():
        functions.extend(inspect.getmembers(_m, func_lookup))

    return functions


def load_modules(path, func_lookup=None):
    """
        加载指定目录下的所有类(不包含同名的类)
    """
    models = {}

    path = path.replace('/', '.').replace(os.sep, '.')
    package = importlib.import_module(path)
    all_modules = discovery_items_in_package(package, func_lookup)

    for _k, _m in all_modules:
        models[_k] = _m
    return models


def parse_csv_content(content, schema):
    if not content:
        return []
    items = content.split('\n')
    result = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        _keys = re.split(r'[,，\t]', item.strip())
        if _keys:
            cur_value = {}
            for (index, field) in enumerate(schema):
                if index < len(_keys):
                    _name = field['name']
                    _type = field['type']
                    if _type == 'bool':
                        cur_value[_name] = bool(_keys[index])
                    elif _type == 'string':
                        cur_value[_name] = _keys[index]
                    elif _type == 'array':
                        sub_val = re.split(r'[;；]', _keys[index])
                        cur_value[_name] = sub_val
                    else:
                        logger.warning('Missing type config %s', _type)
            result.append(cur_value)
    return result
