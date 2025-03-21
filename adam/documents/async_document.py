# -*- coding: utf-8 -*-
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple, Union

from pymongo import uri_parser
from motor.motor_asyncio import AsyncIOMotorClient
from mongoengine.base import get_document
from mongoengine.document import Document
from pymongo.client_session import ClientSession

clients = {}
dbs = {}


def register_connection(alias, uri):
    global clients
    client = clients[alias] = AsyncIOMotorClient(uri)
    parsed = uri_parser.parse_uri(uri)
    db_name = parsed.get('database')
    dbs[alias] = client[db_name]


def get_motor_collection(cls):
    global clients, dbs
    db_alias = cls._meta.get('db_alias', 'default')
    db = dbs.get(db_alias)
    return db[cls._get_collection_name()]


async def drop_database(alias):
    global clients, dbs
    client = clients.get(alias)
    if client:
        await client.drop_database(dbs[alias].name)


def build_document(cls, doc):
    if "_cls" in doc:
        return get_document(doc["_cls"])._from_son(doc)
    else:
        return cls._from_son(doc)


async def save_async(self):
    collection = type(self).get_motor_collection()
    doc = self.to_mongo()
    _id = doc.pop("_id", None)
    if not _id:
        result = await collection.insert_one(doc)
        inserted_id = result.inserted_id
        return await type(self).find_one_async({"_id": inserted_id})
    else:
        await collection.replace_one({"_id": _id}, doc)
        return await type(self).find_one_async({"_id": _id})


async def find_one_async(cls, filter: Optional[Any] = None, *args: Any, **kwargs: Any):
    collection = cls.get_motor_collection()
    document = await collection.find_one(filter, *args, **kwargs)
    if not document:
        return None
    return cls.build_document(document)


def find(cls, *args, **kwargs):
    collection = cls.get_motor_collection()
    return collection.find(*args, **kwargs)


async def find_async(cls, *args, **kwargs):
    collection = cls.get_motor_collection()
    cursor = collection.find(*args, **kwargs)
    async for doc in cursor:
        yield cls.build_document(doc)


async def find_one_and_update_async(
        cls, filter: Mapping[str, Any],
        update: Union[Mapping[str, Any], Sequence[Mapping[str, Any]]],
        projection: Optional[Union[Mapping[str, Any], Iterable[str]]] = None,
        sort: Optional[Sequence[Tuple[str,
        Union[int, str, Mapping[str, Any]]]]] = None,
        upsert: bool = False,
        return_document: bool = False,
        array_filters: Optional[Sequence[Mapping[str, Any]]] = None,
        hint: Optional[Union[str, Sequence[Tuple[str,
        Union[int, str, Mapping[str, Any]]]]]] = None,
        session: Optional[ClientSession] = None,
        let: Optional[Mapping[str, Any]] = None,
        comment: Optional[Any] = None,
        **kwargs: Any
):
    collection = cls.get_motor_collection()
    doc = await collection.find_one_and_update(
        filter, update, projection, sort, upsert, return_document, array_filters, hint, session, let, comment, **kwargs)
    if not doc:
        return None
    return cls.build_document(doc)


async def count_async(cls, filter: Mapping[str, Any], session: Optional[ClientSession] = None,
                      comment: Optional[Any] = None, **kwargs: Any):
    collection = cls.get_motor_collection()
    return await collection.count_documents(filter, session, comment, **kwargs)


async def update_many_async(
        cls, filter: Mapping[str, Any],
        update: Union[Mapping[str, Any],
        Sequence[Mapping[str, Any]]],
        upsert: bool = False,
        array_filters: Optional[Sequence[Mapping[str, Any]]] = None,
        bypass_document_validation: Optional[bool] = None, collation=None,
        hint: Optional[Union[str, Sequence[Tuple[str, Union[int, str, Mapping[str, Any]]]]]] = None,
        session: Optional[ClientSession] = None,
        let: Optional[Mapping[str, Any]] = None,
        comment: Optional[Any] = None):
    collection = cls.get_motor_collection()
    res = await collection.update_many(filter, update, upsert, array_filters, bypass_document_validation, collation,
                                       hint, session, let, comment)
    return res


async def delete_many_async(
        cls, filter: Mapping[str, Any], collation=None,
        hint: Optional[Union[str, Sequence[Tuple[str, Union[int, str, Mapping[str, Any]]]]]] = None,
        session: Optional[ClientSession] = None,
        let: Optional[Mapping[str, Any]] = None,
        comment: Optional[Any] = None):
    collection = cls.get_motor_collection()
    res = await collection.delete_many(filter, collation, hint, session, let, comment)
    return res


async def aggregate_async(cls, pipeline, *args, **kwargs):
    collection = cls.get_motor_collection()
    cursor = collection.aggregate(pipeline, *args, **kwargs)
    async for doc in cursor:
        yield doc


def apply_patch():
    """打上补丁，使得 mongoengine 支持异步操作"""
    setattr(Document, "get_motor_collection", classmethod(get_motor_collection))
    setattr(Document, "find_one_async", classmethod(find_one_async))
    setattr(Document, "build_document", classmethod(build_document))
    setattr(Document, "find_one_and_update_async", classmethod(find_one_and_update_async))
    setattr(Document, "find", classmethod(find))
    setattr(Document, "find_async", classmethod(find_async))
    setattr(Document, "save_async", save_async)
    setattr(Document, "count_async", classmethod(count_async))
    setattr(Document, "update_many_async", classmethod(update_many_async))
    setattr(Document, "delete_many_async", classmethod(delete_many_async))
    setattr(Document, "aggregate_async", classmethod(aggregate_async))
