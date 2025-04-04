# -*- coding: utf-8 -*-

import os
import time
import socket

# debug=true 时，log 会变成 debug 级别(默认 info 级别)
DEBUG = os.environ.get('DEBUG', '').lower() in ('true', '1')
ENV = os.environ.get('ENV') or 'development'  # production, development, test
APP_NAME = os.environ.get('APP_NAME', 'my_app')  # 项目名称

# 默认时区设置
TIME_ZONE = os.environ.get('TZ') or os.environ.get('TIME_ZONE') or 'Etc/GMT'  # 'Asia/Shanghai'
os.environ['TZ'] = TIME_ZONE
if hasattr(time, 'tzset'):
    time.tzset()  # Python time tzset() 根据环境变量TZ重新初始化时间相关设置。

# ISO 8601
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'
# RFC 1123 (ex RFC 822)
RFC1123_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'

STATUS_OK = "OK"
STATUS_ERR = "ERR"
LAST_UPDATED = '_updated'
DATE_CREATED = '_created'
ISSUES = '_issues'
STATUS = '_status'
ERROR = '_error'
ITEMS = '_items'
LINKS = '_links'
ETAG = '_etag'
VERSION = '_version'            # field that stores the version number
DELETED = '_deleted'            # field to store soft delete status
META = '_meta'
INFO = None
VALIDATION_ERROR_STATUS = 422

# return a single field validation error as a list (by default a single error
# is retuned as string, while multiple errors are returned as a list).
VALIDATION_ERROR_AS_LIST = False

# codes for which we want to return a standard response which includes
# a JSON body with the status, code, and description.
STANDARD_ERRORS = [400, 401, 404, 405, 406, 409, 410, 412, 422, 428]

# field returned on GET requests so we know if we have the latest copy even if
# we access a specific version
LATEST_VERSION = '_latest_version'

# appended to ID_FIELD, holds the original document id in parallel collection
VERSION_ID_SUFFIX = '_document'
VERSION_DIFF_INCLUDE = []       # always include these fields when diffing

API_VERSION = ''
URL_PREFIX = 'api'   # 所有后端 API 的前缀
ID_FIELD = '_id'
CACHE_CONTROL = ''
CACHE_EXPIRES = 0
ITEM_CACHE_CONTROL = ''
X_DOMAINS = '*'                 # CORS 允许访问的域名，星号表示允许所有
X_DOMAINS_RE = None             # CORS disabled by default.
X_HEADERS = [                   # CORS disabled by default.
    'Authorization',
    'Content-Language',
    'Content-Type',
    'Expires',
    'Last-Modified',
    'Accept',
    'Cache-Control',
    'Accept-Encoding',
    'Accept-Language',
    'Debug'
]
X_EXPOSE_HEADERS = None         # CORS disabled by default.
X_ALLOW_CREDENTIALS = True      # CORS disabled by default.
X_MAX_AGE = 21600               # Access-Control-Max-Age when CORS is enabled
HATEOAS = False                 # HATEOAS enabled by default.
IF_MATCH = False                 # IF_MATCH (ETag match) enabled by default.
ENFORCE_IF_MATCH = True         # ENFORCE_IF_MATCH enabled by default.
EXTRA_HEADERS = {}

ALLOWED_FILTERS = ['*']         # filtering enabled by default
VALIDATE_FILTERS = False
SORTING = True                  # sorting enabled by default.
JSON_SORT_KEYS = False          # json key sorting
EMBEDDING = True                # embedding enabled by default
INCLUDING = True                # including enabled by default
PROJECTION = True               # projection enabled by default
PAGINATION = True               # pagination enabled by default.
PAGINATION_LIMIT = 150          # 每页显示条目的最大值
PAGINATION_DEFAULT = 25
VERSIONING = False              # turn document versioning on or off.
VERSIONS = '_versions'          # suffix for parallel collection w/old versions
VERSION_PARAM = 'version'       # URL param for specific version of a document.
INTERNAL_RESOURCE = False       # resources are public by default.
JSONP_ARGUMENT = None           # JSONP disabled by default.
SOFT_DELETE = False             # soft delete disabled by default.
SHOW_DELETED_PARAM = 'show_deleted'
BULK_ENABLED = True

OPLOG = False                   # oplog is disabled by default.
OPLOG_NAME = 'oplog'            # default oplog resource name.
OPLOG_ENDPOINT = None           # oplog endpoint is disabled by default.
OPLOG_AUDIT = True              # oplog audit enabled by default.
OPLOG_METHODS = ['DELETE', 'POST', 'PATCH', 'PUT']         # oplog logs all operations by default.
OPLOG_CHANGE_METHODS = ['DELETE', 'PATCH', 'PUT']  # methods which write changes to the oplog
OPLOG_RETURN_EXTRA_FIELD = False    # oplog does not return the 'extra' field.

RESOURCE_METHODS = ['GET', 'POST', 'DELETE']
ITEM_METHODS = ['GET', 'PATCH', 'PUT', 'DELETE']
PUBLIC_METHODS = []
ALLOWED_ROLES = []
ALLOWED_READ_ROLES = []
ALLOWED_WRITE_ROLES = []
PUBLIC_ITEM_METHODS = []
ALLOWED_ITEM_ROLES = []
ALLOWED_ITEM_READ_ROLES = []
ALLOWED_ITEM_WRITE_ROLES = []
# globally enables / disables HTTP method overriding
ALLOW_OVERRIDE_HTTP_METHOD = True
ITEM_LOOKUP = True
ITEM_LOOKUP_FIELD = ID_FIELD
ITEM_URL = 'regex("[a-f0-9]{24}")'
UPSERT_ON_PUT = True            # insert unexisting documents on PUT.

# use a simple file response format by default
EXTENDED_MEDIA_INFO = ['content_type', 'name', 'length']
RETURN_MEDIA_AS_BASE64_STRING = False
RETURN_MEDIA_AS_URL = True
MEDIA_ENDPOINT = 'media'
MEDIA_URL = 'regex("[a-f0-9]{24}")'
MEDIA_BASE_URL = None

MULTIPART_FORM_FIELDS_AS_JSON = False
AUTO_COLLAPSE_MULTI_KEYS = False
AUTO_CREATE_LISTS = False
JSON_REQUEST_CONTENT_TYPES = ['application/json']

SCHEMA_ENDPOINT = None

# list of extra fields to be included with every POST response. This list
# should not include the 'standard' fields (ID_FIELD, LAST_UPDATED,
# DATE_CREATED, and ETAG). Only relevant when bandwidth saving mode is on.
EXTRA_RESPONSE_FIELDS = []
BANDWIDTH_SAVER = True

# default query parameters
QUERY_WHERE = 'where'
QUERY_PROJECTION = 'projection'
QUERY_SORT = 'sort'
QUERY_PAGE = 'page'
QUERY_PAGE_SIZE = 'page_size'
QUERY_EMBEDDED = 'embedded'
QUERY_INCLUDED = 'included'
QUERY_AGGREGATION = 'aggregate'
QUERY_TEXT = 'q'

HEADER_TOTAL_COUNT = 'X-Total-Count'
OPTIMIZE_PAGINATION_FOR_SPEED = False

# user-restricted resource access is disabled by default.
AUTH_FIELD = None

# don't allow unknown key/value pairs for POST/PATCH payloads.
ALLOW_UNKNOWN = False

# GeoJSON specs allows any number of key/value pairs
# http://geojson.org/geojson-spec.html#geojson-objects
ALLOW_CUSTOM_FIELDS_IN_GEOJSON = False

# Rate limits are disabled by default. Needs a running redis-server.
RATE_LIMIT_GET = None
RATE_LIMIT_POST = None
RATE_LIMIT_PATCH = None
RATE_LIMIT_DELETE = None

LICENSE_LIMIT = []

# 接口返回值长度限制(1MB)
MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 1024 * 1024)

# disallow Mongo's javascript queries as they might be vulnerable to injection
# attacks ('ReDoS' especially), are probably too complex for the average API
# end-user and finally can  seriously impact overall performance.
MONGO_QUERY_BLACKLIST = ['$where']
# Explicitly set default write_concern to 'safe' (do regular
# aknowledged writes). This is also the current PyMongo/Mongo default setting.
MONGO_WRITE_CONCERN = {'w': 1}
MONGO_OPTIONS = {
    'connect': True,
    'tz_aware': True,
}

MONGO_COLLECTIONS = {}

# 中间件定义
MIDDLEWARE = []

# 授权后端
AUTHENTICATION_BACKENDS = [
    'adam.auth.token_backend'
]


BROKER_MODE = os.environ.get('BROKER_MODE') or 'mongodb'
# MASTER_NAME = 'mymaster'
MASTER_NAME = os.environ.get('MASTER_NAME') or 'mymaster'
REDIS_URLS = os.environ.get('REDIS_URLS') or 'sentinel://localhost:26379;sentinel://localhost:26380;sentinel://localhost:26381'

MONGO_BROKER_URI = os.environ.get('MONGO_BROKER_URI') or "mongodb://localhost:27017/jobs"


class CELERY_CONFIG(object):
    """celery的默认配置"""
    broker_url = os.environ.get('BROKER_URL') or MONGO_BROKER_URI  # 代理人的地址
    result_backend = os.environ.get('CELERY_RESULT_BACKEND') or ''  # 运行结果存储地址

    '''常见的数据序列化方式
    binary: 二进制序列化方式；python的pickle默认的序列化方法；
    json:json 支持多种语言, 可用于跨语言方案，但好像不支持自定义的类对象；
    XML:类似标签语言；
    msgpack:二进制的类 json 序列化方案, 但比 json 的数据结构更小, 更快；
    yaml:yaml 表达能力更强, 支持的数据类型较 json 多, 但是 python 客户端的性能不如 json
    '''
    task_serializer = os.environ.get('CELERY_TASK_SERIALIZER', 'json')  # 任务序列化
    result_serializer = os.environ.get('CELERY_RESULT_SERIALIZER', 'json')  # 任务执行结果序列化
    accept_content = [os.environ.get('CELERY_ACCEPT_CONTENT', 'json')]  # 指定任务接受的内容序列化类型

    task_default_queue = os.environ.get('CELERY_DEFAULT_QUEUE', 'default')  # 默认队列
    result_expires = int(os.environ.get('CELERY_TASK_RESULT_EXPIRES', 3600))  # 任务结果过期时间，单位秒
    task_time_limit = int(os.environ.get('CELERYD_TASK_TIME_LIMIT', 0)) or None  # 规定完成任务的时间，单位秒。在指定时间内完成任务，否则执行该任务的worker将被杀死，任务移交给父进程
    worker_max_tasks_per_child = int(os.environ.get('CELERYD_MAX_TASKS_PER_CHILD', 30)) or None  # 每个worker执行了多少任务就会死掉，默认是无限的。可防止内存泄露
    task_acks_late = os.environ.get('CELERY_ACKS_LATE', 'false').lower() in ('true', '1')  # 任务发送完成是否需要确认，这一项对性能有一点影响

    timezone = TIME_ZONE  # 设置时区
    enable_utc = True  # UTC时区换算
    broker_connection_retry_on_startup = True  # 连接失败重试
    # 设置log格式
    worker_log_format = '[%(asctime)s] [%(module)s.%(funcName)s:%(lineno)s] %(levelname)s: %(message)s'
    worker_task_log_format = '[%(asctime)s] [%(levelname)s/%(task_name)s %(task_id)s]: %(message)s'


# celery 监控账号密码
MONITOR_USERNAME = os.environ.get('MONITOR_USERNAME', 'admin')
MONITOR_PASSWORD = os.environ.get('MONITOR_PASSWORD', '123456')

# celery 限制
RETRY_TASK_DAYS = int(os.environ.get('RETRY_TASK_DAYS') or 10)  # 允许重试的任务天数(超过的不再重试)
LIMIT_TASK = int(os.environ.get('LIMIT_TASK') or 1000)  # 任务数量限制,超过则认为任务堆积过多
TASK_TLE = int(os.environ.get('TASK_TLE') or 60)  # 任务超时时间(分钟)，超过则认为任务需要重试
TASK_ERROR_TIMES = int(os.environ.get('TASK_ERROR_TIMES') or 15)  # 任务出错重试次数限制


# Database
MONGO_CONNECTIONS = {
    'default': os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/my_db',
    # 'broker': CELERY_CONFIG.broker_url,  # 如果使用 mongodb 作为中间件，则需要配置这里
    # 'result_backend': CELERY_CONFIG.result_backend
}


# HTTP 的超时时间
SOCKET_TIMEOUT = int(os.environ.get('SOCKET_TIMEOUT') or 30)
socket.setdefaulttimeout(SOCKET_TIMEOUT)

# pulsar 相关配置
PULSAR_URL = os.environ.get('PULSAR_URL', 'pulsar://localhost:6650')
PULSAR_TOPIC = os.environ.get('PULSAR_TOPIC', f'persistent://public/default/{APP_NAME}')
