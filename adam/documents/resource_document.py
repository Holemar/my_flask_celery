# -*- coding: utf-8 -*-
"""
继承mongoengine的Document，实现一些基础功能：
    * 时间戳
"""

import json
import logging
from datetime import datetime

from mongoengine import Document, queryset_manager
from mongoengine.queryset.visitor import Q
from mongoengine.fields import DateTimeField
from mongoengine.queryset import QuerySetNoCache
from bson import ObjectId
from flask import request
from ..utils.serializer import mongo_to_dict

logger = logging.getLogger(__name__)

from .base import IDocument


class MyQuerySet(QuerySetNoCache):
    """
    MyQuerySet
    """

    def __init__(self, document, collection):
        super(QuerySetNoCache, self).__init__(document, collection)

        # 禁用始终包含_cls的查询过滤.
        # _loaded_fields: mongoengine 0.15.0版本
        # _cls_query: mongoengine > 0.19.0版本
        if hasattr(self, '_cls_query'):
            self._cls_query = {}
        elif hasattr(self, '_loaded_fields'):
            self._loaded_fields.always_include = set([])

    def by_own(self, user):
        return self.filter(user=user.id)

    def by_users(self, users, share_filter=None):
        q = Q(user__in=users)
        if share_filter is not None:
            return self.filter(Q(**share_filter) | q)
        else:
            return self.filter(q)

    def by_company(self, company):
        return self.filter(owned_company=company.id)

    def by_companies(self, companies, share_filter=None):
        q = Q(owned_company__in=companies)
        if share_filter is not None:
            return self.filter(Q(**share_filter) | q)
        else:
            return self.filter(q)

    def __call__(self, q_obj=None, **query):
        if not hasattr(self, '_cls_query'):
            # remove class check mongoengine <0.19.0
            query.pop('class_check', False)
            return super(QuerySetNoCache, self).__call__(q_obj, class_check=False, read_preference=query.pop('read_preference', None), **query)
        else:
            return super(QuerySetNoCache, self).__call__(q_obj, **query)


class ResourceDocument(Document, IDocument):
    """
    ResourceDocument
    """

    # 描述
    meta = {
        'abstract': True,
        'strict': False,
        'audit': False,
        'audit_actions': [
            'item_read',
            'item_delete',
            'item_update'
        ],
        'item_id_field': None,
        'queryset_class': MyQuerySet,
        'hidden': [],
        'dynamic_fields': [],
        'protected': [],
        'search_fields': [],
        'import_options': {
            'form': [],
            'fields': []
        }
    }

    # 创建时间戳
    created_at = DateTimeField(db_field='created_at', default=datetime.utcnow)

    # 更新时间戳
    updated_at = DateTimeField(db_field='updated_at', default=datetime.utcnow)

    @queryset_manager
    def objects(doc_cls, queryset):
        queryset._class_check = False
        return queryset

    @classmethod
    def _get_changer(cls):
        return request.user

    def before_save(self, *args, **kwargs):
        """
        model 事件 before_save
        """
        pass

    def after_create(self, instance):
        """
        model 事件 after_create
        """
        pass

    def after_delete(self):
        pass

    def after_update(self, payload):
        """
            model 事件 after_update
        """
        pass

    def delete(self, enable_hook=True, *args, **kwargs):
        """
        重载delete
        """
        result = super().delete(*args, **kwargs)
        return result

    def save(self, enable_hook=True, *args, **kwargs):
        """
        重载save，自动更新时间戳
            param: args
            param: kwargs
        """
        if enable_hook:
            self.before_save(*args, **kwargs)

        logger.debug('saving document for %s', str(self.id))
        self.updated_at = datetime.utcnow()
        mode = 'create' if not self.id else 'update'
        result = super().save(*args, **kwargs)
        if enable_hook and mode == 'create':
            self.after_create(result)
        if enable_hook and mode == 'update':
            self.after_update(kwargs)
        return result

    def update(self, enable_hook=True, **kwargs):
        """
        更新，自动更新时间戳
        """
        if enable_hook:
            self.before_save(None, **kwargs)
        self.updated_at = datetime.utcnow()

        # Ugly, TBD
        queryset_obj = self.__class__.objects(id=self.id)
        if hasattr(queryset_obj, 'clear_cls_query'):
            # remove class check mongoengine >0.19.0
            result = queryset_obj.clear_cls_query().update_one(upsert=False, write_concern=None, **kwargs)
        else:
            # remove class check mongoengine 0.15.0
            result = self.__class__.objects(id=self.id, class_check=False).update_one(upsert=False, write_concern=None, **kwargs)
        if enable_hook:
            self.after_update(kwargs)
        return result

    @classmethod
    def is_valid_id(cls, _id):
      return ObjectId.is_valid(_id)

    @classmethod
    def batch_insert(cls, items):
        docs = []
        for item in items:
            docs.append(cls(**item))
        return cls.objects.insert(docs)

    @classmethod
    def build_object(cls, data):
      return cls(**data)

    @classmethod
    def find_one(cls, condition):
        return cls.objects.get(**condition)

    @classmethod
    def find_one_by_id(cls, id):
        item_condition = {'id': id}
        return cls.objects.get(**item_condition)
    
    @classmethod
    def find_by_ids(cls, ids):
        return list(cls.objects(id__in=ids).all())

    @classmethod
    def get_fields(cls):
        return cls._fields

    @classmethod
    def copy(cls, target_object, exclude=None):
        """
        拷贝，shalow copy
            * 去除id
            * 去除exclude
            * 检查字段属性，一致的才会拷贝.
        """
        if not target_object:
            raise SystemError('Invalid Parameter')

        exclude_fields = ['_id']
        if exclude and isinstance(exclude, list):
            exclude_fields = exclude_fields + exclude

        target_json = target_object.to_json()
        res = json.loads(target_json)
        for exclude in exclude_fields:
            if res.get(exclude):
                del res[exclude]
        res = json.dumps(res)
        obj = cls.from_json(res)
        obj._created = True
        return obj

    def to_dict(self, exclude_fields=[], date_format=None, without_none=False):
        return mongo_to_dict(self, exclude_fields=exclude_fields, date_format=date_format, without_none=without_none)

    def from_dict(self):
        return mongo_to_dict(self)
