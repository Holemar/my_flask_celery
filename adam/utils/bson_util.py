# -*- coding: utf-8 -*-
"""
提供 json 序列化和反序列化的 bson 编码器和解码器。
主要用于 celery 任务参数的序列化和反序列化。
"""
import uuid
import json
import time
import decimal
import datetime

from bson.objectid import ObjectId


class BsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return {
                '__type__': '__ObjectId__',
                'value': str(obj)
            }
        if isinstance(obj, uuid.UUID):
            return {
                '__type__': '__uuid__',
                'value': obj.hex
            }
        if isinstance(obj, datetime.datetime):
            return {
                '__type__': '__datetime__',
                'value': obj.timestamp()
            }
        if isinstance(obj, datetime.date):
            return {
                '__type__': '__date__',
                'value': time.mktime(obj.timetuple())
            }
        if isinstance(obj, time.struct_time):
            return {
                '__type__': '__time__',
                'value': time.mktime(obj)
            }
        if isinstance(obj, decimal.Decimal):
            return {
                '__type__': '__decimal__',
                'value': float(obj)
            }
        return json.JSONEncoder.default(self, obj)


def bson_decoder(obj):
    if '__type__' in obj:
        _type = obj['__type__']
        value = obj['value']
        if _type == '__ObjectId__':
            return ObjectId(value)
        if _type == '__uuid__':
            return uuid.UUID(value)
        if _type == '__datetime__':
            return datetime.datetime.fromtimestamp(value)
        if _type == '__date__':
            return datetime.date.fromtimestamp(value)
        if _type == '__time__':
            return time.localtime(value)
        if _type == '__decimal__':
            return decimal.Decimal(value)
    return obj


# Encoder function
def bson_dumps(obj):
    return json.dumps(obj, cls=BsonEncoder)


# Decoder function
def bson_loads(obj):
    return json.loads(obj, object_hook=bson_decoder)
