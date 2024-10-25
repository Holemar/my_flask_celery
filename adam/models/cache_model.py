# -*- coding: utf-8 -*-
import os
import time
from ..documents.resource_document import ResourceDocument

# 缓存配置的时间(超时则重新读取数据库)
TIMEOUT = int(os.environ.get('MODEL_CACHE_TIMEOUT') or 300)


class CacheDocument(ResourceDocument):
    """有缓存的Model."""

    # 描述
    meta = {
        'abstract': True,  # 抽象类，设为True，表示不生成具体document
        'strict': False,  # 严格模式。当 strict 为 True 时, save 的时候传入多余字段会报错
    }

    # 缓存配置值
    _objects = []
    _last_read = None

    @classmethod
    def clear_cache(cls):
        """删除缓存的配置,让下次读取时获取数据库最新的配置"""
        cls._objects = None
        cls._last_read = None

    @classmethod
    def get_objects(cls, clear_cache=None, **kwargs):
        """
        :param clear_cache: 是否强行清除缓存配置
        :param kwargs: 查询参数
        :return: 数据库本表的所有值
        """
        # 如果没有传参过来，则每隔 5 分钟清除缓存，因为没有定时清空缓存机制。
        if clear_cache is None:
            if cls._last_read is None or time.time() - cls._last_read > TIMEOUT:
                cls._last_read = time.time()
                clear_cache = True

        if clear_cache:
            cls._objects = None

        if cls._objects:
            return cls._objects

        # 读取全部的配置
        cls._objects = list(cls.objects.filter(**kwargs).all())
        return cls._objects
