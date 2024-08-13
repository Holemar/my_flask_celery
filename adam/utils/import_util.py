# -*- coding: utf-8 -*-
import re
import logging
import inspect
import pkgutil
import importlib

logger = logging.getLogger(__name__)


def import_submodules(package, recursive=True):
    """ Import all submodules of a module, recursively, including subpackages

    :param package: package (name or actual module)
    :type package: str | module
    :rtype: dict[str, types.ModuleType]
    """
    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for _, name, is_pkg in pkgutil.walk_packages(package.__path__):
        if name.startswith('_'):
            continue
        full_name = package.__name__ + '.' + name
        results[full_name] = importlib.import_module(full_name)
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