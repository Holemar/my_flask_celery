# -*- coding:utf-8 -*-
import os
import logging
import datetime

from bson import ObjectId
from flask import request, g
from mongoengine.fields import IntField, FloatField, StringField, DictField

from adam.documents import ResourceDocument
from adam.str_util import decode2str
from adam.json_util import load_json
from .log import Log, repr_value

# log的保存天数，超过则自动删除
SAVE_LOG_DAYS = int(os.environ.get('SAVE_LOG_DAYS') or 10)


def delete_log():
    """删除旧log(删除配置天数之前的)"""
    dt = datetime.datetime.utcnow() - datetime.timedelta(days=SAVE_LOG_DAYS)
    _oid = ObjectId.from_datetime(dt)
    # Log.objects(created_at__lte=dt).delete()
    Log.objects(id__lte=_oid).delete()
    # LogApi.objects(created_at__lte=dt).delete()
    LogApi.objects(id__lte=_oid).delete()


def get_client_ip():
    """获取请求方IP"""
    ips = request.headers.getlist("X-Forwarded-For")
    if ips:
        return str(ips)
    return request.remote_addr


class LogApi(ResourceDocument):
    """请求记录 Model."""
    meta = {}

    method = StringField()  # 请求方式
    url = StringField()  # 接口地址
    headers = DictField()  # 对方的头部信息
    # user_agent = StringField()  # 请求方的UserAgent, headers 里面已经有
    ip = StringField()  # 请求方的真实IP地址
    body = StringField()  # 请求参数
    json_body = DictField()  # JSON格式的请求参数

    status_code = IntField()  # 响应的编码
    response = StringField()  # 响应值
    json_response = DictField()  # JSON格式的响应值
    duration = FloatField()  # 请求耗时(单位：秒)

    others = DictField()  # 其它记录信息

    @classmethod
    def add(cls, response, **kwargs):
        """加请求记录日志
        """
        try:
            obj = cls(
                method=request.method,
                url=request.full_path,  # request.full_path 连带上参数， request.path 不带参数
                headers=dict(request.headers),
                ip=get_client_ip(),
                # user_agent=str(request.user_agent),
                body=decode2str(request.data),
                json_body=request.get_json(),
                # files=request.files,

                status_code=response.status_code,
            )

            try:
                obj.response = decode2str(response.get_data())
                obj.json_response = load_json(obj.response)
            except:
                pass

            obj.duration = getattr(g, 'duration', 0)
            # 储存在 g 里面的其它参数
            g_fields = ('get', 'pop', 'setdefault', 'start_time', 'duration')
            kwargs.update({k: v for k, v in vars(g).items() if not k.startswith('__') and k not in g_fields})
            obj.others = repr_value(kwargs)
            obj.save(force_insert=True)
            return obj
        # 避免写日志的错误影响其它代码
        except Exception as e:
            logging.exception(e)
