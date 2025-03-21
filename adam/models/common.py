# -*- coding: utf-8 -*-

from adam.models import CacheDocument
from adam.fields import StringField, DictField


class Common(CacheDocument):
    """
    储存全局变量用
    """

    key = StringField(required=True)  # unique=True
    value = DictField(default={})

    @classmethod
    def get_value(cls, key):
        for obj in cls.get_objects():
            if obj.key == key:
                return obj.value
        # 缓存没有，则查询
        obj = cls.objects(key=key).first()
        if obj:
            cls.clear_cache()  # 缓存没有对应的值，则让缓存过期
            return obj.value
        # 查不到
        return None

    @classmethod
    def set_value(cls, key, value):
        obj = cls.objects.filter(key=key).first()
        if obj:
            if obj.value != value:
                obj.value = value
                obj.save()
                cls.clear_cache()
            return obj
        # 没有，则新增
        obj = cls.objects.create(key=key, value=value)
        cls.clear_cache()
        return obj

    @classmethod
    def update_sub_value(cls, key, inner_key, value):
        """设置内嵌的字典值"""
        obj_value = cls.get_value(key) or {}
        obj_value[inner_key] = value
        obj = cls.set_value(key, obj_value)
        return obj

