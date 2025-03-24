# -*- coding: utf-8 -*-
"""
继承mongoengine的 QuerySet，实现一些基础功能
"""
import logging

from mongoengine.queryset.visitor import Q
from mongoengine.queryset import QuerySetNoCache
from ..utils.serializer import mongo_to_dict
from .async_document import get_motor_collection, build_document, find_one_async, find_one_and_update_async, find, \
    find_async, save_async, count_async, update_many_async, delete_many_async, aggregate_async


logger = logging.getLogger(__name__)


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
        return self.filter(company=company.id)

    def by_companies(self, companies, share_filter=None):
        q = Q(company__in=companies)
        if share_filter is not None:
            return self.filter(Q(**share_filter) | q)
        else:
            return self.filter(q)

    def __call__(self, q_obj=None, **query):
        if not hasattr(self, '_cls_query'):
            # remove class check mongoengine <0.19.0
            query.pop('class_check', False)
            return super(QuerySetNoCache, self).__call__(q_obj, class_check=False,
                                                         read_preference=query.pop('read_preference', None), **query)
        else:
            return super(QuerySetNoCache, self).__call__(q_obj, **query)

    async def all_async(self):
        """Return all documents."""
        collection = self._document.get_motor_collection()
        cursor = collection.find(self._query, **self._cursor_args)
        if self._ordering:
            cursor = cursor.sort(self._ordering)
        if self._limit:
            cursor = cursor.limit(self._limit)
        if self._skip:
            cursor = cursor.skip(self._skip)
        async for doc in cursor:
            yield self._document.build_document(doc)

    async def in_async(self, object_ids):
        """Retrieve a set of documents by their ids.

        :param object_ids: a list or tuple of ObjectId's
        :rtype: dict of ObjectId's as keys and collection-specific
                Document subclasses as values.
        """
        async for doc in self._document.find_async({"_id": {"$in": object_ids}}, **self._cursor_args):
            yield doc

    async def first_async(self, *q_objs, **query):
        queryset = self.clone()
        queryset = queryset.order_by().limit(1)
        queryset = queryset.filter(*q_objs, **query)
        return await self._document.find_one_async(queryset._query)

    get_async = first_async  # alias for first_async(丢失了判断多个结果的功能)

    async def create_async(self, **kwargs):
        """Create new object. Returns the saved object instance."""
        return await self._document(**kwargs).save_async()

    async def insert_async(self, doc_or_docs):
        collection = self._document.get_motor_collection()
        if isinstance(doc_or_docs, self._document):
            doc_or_docs = [doc_or_docs]
        docs = [mongo_to_dict(doc) for doc in doc_or_docs]
        result = await collection.insert_many(docs)
        return result.inserted_ids

    async def count_async(self):
        return await self._document.count_async(self._query)

    async def delete_async(self):
        return await self._document.delete_many_async(self._query)

    async def update_async(self, **update):
        return await self._document.update_many_async(filter=self._query, update=update)

