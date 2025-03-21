# -*- coding: utf-8 -*-
import os
import re
import sys
import logging
import inspect
import pkgutil
import importlib

logger = logging.getLogger(__name__)


def import_string(import_name: str):
    """Imports an object based on a string.  This is useful if you want to
    use import paths as endpoints or something similar.  An import path can
    be specified either in dotted notation (``xml.sax.saxutils.escape``)
    or with a colon as object delimiter (``xml.sax.saxutils:escape``).

    :param import_name: the dotted name for the object to import.
    :return: imported object
    """
    import_name = import_name.replace(":", ".")
    try:
        try:
            __import__(import_name)
        except ImportError:
            if "." not in import_name:
                raise
        else:
            return sys.modules[import_name]

        module_name, obj_name = import_name.rsplit(".", 1)
        module = __import__(module_name, globals(), locals(), [obj_name])
        try:
            return getattr(module, obj_name)
        except AttributeError as e:
            raise ImportError(e) from None

    except ImportError as e:
        pass

    return None


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
            logger.error('Failed to import %s: %s', full_name, e)
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
    all_modules = {}

    try:
        path = path.replace('/', '.').replace(os.sep, '.')
        package = importlib.import_module(path)
        all_modules = discovery_items_in_package(package, func_lookup)
    except Exception as e:
        logger.error('Failed to load modules from %s: %s', path, e)

    for _k, _m in all_modules:
        models[_k] = _m
        _n = str(_m)[8:-2]
        if _n.startswith(path + '.'):
            _n = _n[len(path) + 1:]
        if _n.endswith('.' + _k):
            _n = _n[:-len(_k) - 1]
        if _n:
            models[_n] = _m
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
