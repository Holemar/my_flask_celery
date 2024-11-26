# -*- coding: utf-8 -*-
import json
import time
import uuid
import logging
import decimal
import datetime
from enum import Enum

from bson import ObjectId
from mongoengine.fields import DateTimeField, LazyReference, ReferenceField, DictField, LazyReferenceField, \
    GenericLazyReferenceField, ListField, EmbeddedDocumentField
from mongoengine.base.fields import ObjectIdField
from mongoengine import Document, EmbeddedDocument
from flask import current_app as app

from ..fields import LazyRelation, EnumField, RelationField

_build_in_field_names = ['_cls', '_type']

logger = logging.getLogger(__name__)


def serialize(_root, obj, field_obj, depth=1, included=None, excluded=None):
    """
    递归序列化
    """
    result = None
    if obj is None:
        return None

    if isinstance(obj, (list, tuple, set)):
        result = []
        for item in obj:
            result.append(serialize(_root, item, None, depth, included=included, excluded=excluded))
        return result
    elif isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if excluded and k in excluded:
                continue
            result[k] = serialize(k, v, None, depth, included=included, excluded=excluded)
        return result
    elif isinstance(obj, (str, int, float, bool, complex)):
        result = obj
    elif isinstance(obj, decimal.Decimal):
        result = float(obj)
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, time.struct_time):
        return time.strftime('%Y-%m-%dT%H:%M:%S', obj)
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, datetime.date):
        return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, uuid.UUID):
        return obj.hex
    elif isinstance(obj, Enum):
        return obj.value

    elif isinstance(field_obj, GenericLazyReferenceField):
        if depth <= 2 or _root in included:
            model = app.models.get(field_obj.name.capitalize())
            if model:
                new_obj = None
                if isinstance(obj, LazyReference):
                    new_obj = obj.fetch()
                elif isinstance(obj, ObjectId):
                    new_obj = model.objects(id=obj).first()
                else:
                    logger.error('wrong lazy generic reference field')
                return serialize(_root, new_obj, None, depth, included=included)
        else:
            return {'id': str(obj)}
    elif isinstance(obj, LazyReference) or isinstance(field_obj, GenericLazyReferenceField):
        if depth <= 2 and included and _root in included:
            return serialize(_root, obj.fetch(), None, depth, included=included)
        else:
            return {'id': str(obj.id)}
    elif isinstance(obj, LazyRelation):
        if depth <= 2 and included and _root in included:
            return serialize(_root, obj.fetch(), None, depth, included=included)
    elif isinstance(obj, EmbeddedDocument):
        result = {}
        for field_name, field_obj in obj._fields.items():
            if field_name in _build_in_field_names or obj[field_name] is None or (excluded and field_name in excluded):
                continue
            value = serialize(field_name, obj[field_name], field_obj, depth, included=included)
            if value is not None:
                result[field_name] = value
        return result
    elif isinstance(obj, Document):
        if depth <= 2:
            result = {}
            doc_excluded = obj._meta['hidden']
            if depth == 2:
                doc_excluded = doc_excluded + obj._meta['protected']

            norm_doc_excluded = list(filter(lambda x: '.' not in x, doc_excluded))
            nest_doc_excluded = list(filter(lambda x: '.' in x, doc_excluded))
            nest_doc_excluded_dict = {}
            for n_e_i in nest_doc_excluded:
                p, c = n_e_i.split('.')
                if p in nest_doc_excluded_dict:
                    nest_doc_excluded_dict[p].append(c)
                else:
                    nest_doc_excluded_dict[p] = [c]
            for field_name, field_obj in obj._fields.items():
                value = None
                if field_name in _build_in_field_names or obj[field_name] is None or field_name in doc_excluded:
                    continue
                value = serialize(
                    field_name, obj[field_name], field_obj, depth + 1, included=included,
                    excluded=nest_doc_excluded_dict.get(field_name))
                if value is not None:
                    result[field_name] = value
            if obj._meta['dynamic_fields']:
                for df_name in obj._meta['dynamic_fields']:
                    if df_name in included:
                        val = getattr(obj, df_name, None)
                        if val is not None:
                            if isinstance(val, dict):
                                for dfn, dfv in val.items():
                                    result[dfn] = dfv
                            elif val:
                                result[df_name] = val
                        else:
                            logger.error('Missing dynamic field %s', df_name)
            return result
    else:
        logger.warning('unknow type to serialize, %s', obj.__class__)
        result = obj
    return result


def _array_to_list_field(list_field, data):
    result = []
    field = list_field.field
    for item in data:
        if isinstance(field, EmbeddedDocumentField):
            document_type = field.document_type
            tmp = {}
            for e_n, e_f in document_type._fields.items():
                tmp[e_n] = item.get(e_n)
            result.append(document_type(**tmp))
        elif isinstance(field, ReferenceField):
            result.append(field.document_type.objects(id=item).first())
        else:
            result.append(item)
    return result


def dict_to_mongo(model, data):
    if not isinstance(data, dict):
        return None

    result = {}

    # filter
    for name, value in data.items():
        if name in model._fields:
            field = model._fields[name]
            if isinstance(field, ListField):
                result[name] = _array_to_list_field(field, value)
            elif isinstance(field, ReferenceField) \
                    or isinstance(field, LazyReferenceField):
                if value is None:
                    result[name] = None
                elif isinstance(value, dict) and value.get('id'):
                    result[name] = ObjectId(value.get('id'))
                else:
                    result[name] = ObjectId(value)
            elif isinstance(field, DictField):
                try:
                    if isinstance(value, str):
                        result[name] = json.loads(value)
                    elif isinstance(value, dict):
                        result[name] = value
                    else:
                        logger.warning('Unknown dict type for dict_to_mongo %s', name)
                except:
                    logger.warning('Invalid dict type for dict_to_mongo %s', name)
                    raise SyntaxError('Invalid Data')
            elif isinstance(field, EmbeddedDocumentField):
                if isinstance(value, dict):
                    tmp = {}
                    for field_name, field_val in field.document_type._fields.items():
                        tmp[field_name] = value.get(field_name)
                    result[name] = field.document_type(**tmp)
                else:
                    logger.warning('Invalid Type for dict_to_mongo %s', name)
            else:
                result[name] = value

    return result


def mongo_to_dict(obj, index_only=False, exclude_fields=[], only_fields=[], date_format=None, without_none=False):
    """
    转换成dict，depth默认是1，只关心本model的数据
    """
    return_data = []
    if obj is None:
        return None
    if isinstance(obj, Document):
        return_data.append(("id", str(obj.id)))

    if index_only and not isinstance(obj, EmbeddedDocument) and not obj._meta.get('index'):
        return None

    for field_name, field in obj._fields.items():
        if only_fields:
            if field_name not in only_fields:
                continue
        elif exclude_fields and field_name in exclude_fields:
            continue

        if field_name in ("id",):
            continue

        if index_only and not (hasattr(field, 'index') and field.index):
            continue

        data = obj._data.get(field_name)
        if data is not None:
            _field_val = obj._fields[field_name]
            if isinstance(_field_val, ListField):
                _result = (field_name, _list_field_to_dict(data, index_only, date_format))
                if _result:
                    return_data.append(_result)
            elif isinstance(_field_val, EmbeddedDocumentField):
                return_data.append(
                    (field_name, mongo_to_dict(data, index_only, exclude_fields, only_fields, date_format)))
            elif isinstance(_field_val, DictField):
                return_data.append((field_name, data))
            elif isinstance(_field_val, EnumField):
                if isinstance(data, Enum):
                    return_data.append((field_name, data.value))
                else:
                    return_data.append((field_name, data))
            elif isinstance(_field_val, DateTimeField):
                if isinstance(data, datetime.datetime):
                    # return_data.append((field_name, data.strftime('%Y-%m-%d')))
                    if date_format == 'keep':
                        return_data.append((field_name, data))
                    elif date_format:
                        return_data.append((field_name, data.strftime(date_format)))
                    else:
                        return_data.append((field_name, data.isoformat()))
                else:
                    return_data.append((field_name, data))
            elif isinstance(_field_val, ObjectIdField):
                return_data.append((field_name, str(data)))
            elif isinstance(_field_val, ReferenceField):
                return_data.append((field_name, str(data.id)))
            elif isinstance(_field_val, LazyReferenceField):
                # ugly fix
                if isinstance(data, ObjectId):
                    return_data.append((field_name, str(data)))
                elif isinstance(data, str):
                    return_data.append((field_name, data))
                else:
                    return_data.append((field_name, str(data.id)))
            elif not isinstance(_field_val, RelationField):
                return_data.append((field_name, obj._data[field_name]))
        else:
            if not without_none:
                return_data.append((field_name, data))

    return dict(return_data)


def _list_field_to_dict(list_field, index_only=False, date_format=None):
    return_data = []
    for item in list_field:
        if isinstance(item, EmbeddedDocument):
            return_data.append(mongo_to_dict(item, index_only, [], [], date_format))
        else:
            return_data.append(item)
    return return_data
