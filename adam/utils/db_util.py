# -*- coding: utf-8 -*-
import logging

from pymongo import MongoClient, uri_parser


logger = logging.getLogger(__name__)


def get_mongo_db(uri):
    """获取对应字符串的mongodb连接"""
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        parsed = uri_parser.parse_uri(uri)
        db_name = parsed.get('database')
        db = client[db_name]
        db.test.find_one()  # test connection
        return db
    except:
        return None


def get_redis_client(redis_url):
    import redis
    pool = redis.ConnectionPool.from_url(
        redis_url,
        # decode_components=True,
        # decode_responses=True,
    )
    redis_client = redis.Redis(connection_pool=pool)
    return redis_client

