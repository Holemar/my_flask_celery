# -*- coding: utf-8 -*-
import inspect
import pkgutil
import importlib


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

