# -*- coding: utf-8 -*-
import re
import json
from datetime import datetime, timedelta

from flask import request, abort
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import BadRequestKeyError
from werkzeug.datastructures import MultiDict, CombinedMultiDict
from mongoengine.fields import DateTimeField

from .config_util import config


_operators = [
    'not__exists' 'exists', 'gte', 'lte', 'ne', 'gt', 'in', 'nin', 'icontains', 'contains',
    'startswith', 'istartswith', 'endswith', 'iendswith'
]


class RegexConverter(BaseConverter):
    """ Extend werkzeug routing by supporting regex for urls/API endpoints """

    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


def underscore(word):
    """
    Make an underscored, lowercase form from the expression in the string.

    Example::

        >>> underscore("DeviceType")
        "device_type"

    As a rule of thumb you can think of :func:`underscore` as the inverse of
    :func:`camelize`, though there are cases where that does not hold::

        >>> camelize(underscore("IOError"))
        "IoError"

    """
    word = re.sub(r"([A-Z]+)([A-Z][a-z])", r'\1_\2', word)
    word = re.sub(r"([a-z\d])([A-Z])", r'\1_\2', word)
    word = word.replace("-", "_")
    return word.lower()


def get_param():
    """获取参数"""
    try:
        post_data = request.data
        if post_data and isinstance(post_data, (bytes, bytearray)):
            post_data = post_data.decode()
        return post_data
    except:
        return None


class ParsedRequest(object):
    """ This class, by means of its attributes, describes a client request.
    """
    # `where` value of the query string (?where). Defaults to None.
    where = None

    # `projection` value of the query string (?projection). Defaults to None.
    projection = None

    # `sort` value of the query string (?sort). Defaults to None.
    sort = None

    # count By
    by = None

    # is debug
    is_debug = False

    # `page` value of the query string (?page). Defaults to 1.
    page = 1

    # `page_size` value of the query string (?page_size). Defaults to
    # `PAGINATION_DEFAULT` unless pagination is disabled.
    page_size = 0

    # `If-Modified-Since` request header value. Defaults to None.
    if_modified_since = None

    # `If-None_match` request header value. Defaults to None.
    if_none_match = None

    # `If-Match` request header value. Default to None.
    if_match = None

    # `embedded` value of the query string (?embedded). Defaults to None.
    embedded = None

    # `inculding` value of the query string (?embedded). Defaults to None.
    included = None

    # `show_deleted` True when the SHOW_DELETED_PARAM is included in query.
    # Only relevant when soft delete is enabled. Defaults to False.
    show_deleted = False

    # `aggregation` value of the query string (?aggregation). Defaults to None.
    aggregation = None

    # `args` value of the original request. Defaults to None.
    args = None

    # `q` text search.  enable index search mode
    q = None


def weak_date(date):
    """ Returns a RFC-1123 string corresponding to a datetime value plus
    a 1 second timedelta. This is needed because when saved, documents
    LAST_UPDATED values have higher resolution than If-Modified-Since's, which
    is limited to seconds.

    :param date: the date to be adjusted.
    """
    return datetime.strptime(date, config.RFC1123_DATE_FORMAT) + timedelta(seconds=1) if date else None


def multidict_to_dict(multidict):
    """ Convert a MultiDict containing form data into a regular dict. If the
    config setting AUTO_COLLAPSE_MULTI_KEYS is True, multiple values with the
    same key get entered as a list. If it is False, the first entry is picked.
    """
    if config.AUTO_COLLAPSE_MULTI_KEYS:
        d = dict(multidict.lists())
        for key, value in d.items():
            if len(value) == 1:
                d[key] = value[0]
        return d
    else:
        return multidict.to_dict()


def _safe_get(args, key):
    if key:
        try:
            return json.loads(args.get(key))
        except:
            return None
    return None


def _etag_parse(challenge, headers):
    if challenge in headers:
        etag = headers[challenge]
        if etag.startswith('W/\"'):
            etag = etag.lstrip('W/')
        # remove double quotes from challenge etag format to allow direct
        # string comparison with stored values
        return etag.replace('\"', '')
    else:
        return None


def parse_request(document):
    """ Parses a client request, returning instance of :class:`ParsedRequest`
    containing relevant request data.

    :param resource: the resource currently being accessed by the client.
    """
    try:
        data = request.get_json()
    except:
        data = {}
    args = request.args
    headers = request.headers
    r = ParsedRequest()
    r.projection = data.get('projection') or _safe_get(args, 'projection')
    r.sort = data.get('sort') or args.get('sort') or '-id'
    if ',' in r.sort:
        r.sort = r.sort.split(',')
    else:
        r.sort = [r.sort]
    r.embedded = data.get('embedded') or _safe_get(args, 'embedded')
    r.included = data.get('included') or _safe_get(args, 'included')
    r.only = data.get('only') or _safe_get(args, 'only')
    r.q = data.get('q') or args.get('q')
    r.by = data.get('by') or args.get('by')
    r.is_debug = headers.get('Debug') == 'on'
    where = data.get('where') or _safe_get(args, 'where') or {}
    if document:
        transformed_where = {}
        fields = document.get_fields()
        for k, v in where.items():
            if isinstance(v, dict):
                if isinstance(fields.get(k), DateTimeField):
                    for kk, vv in v.items():
                        if kk in _operators:
                            fk = k + '__' + kk
                            real_v = datetime.strptime(vv, '%Y-%m-%dT%H:%M:%S')
                            transformed_where[fk] = real_v
                else:
                    for kk, vv in v.items():
                        fk = k + '__' + kk
                        transformed_where[fk] = vv
            else:
                transformed_where[k] = v
        r.where = transformed_where

    try:
        r.page_size = int(float(data.get(config.QUERY_PAGE_SIZE) or args[config.QUERY_PAGE_SIZE]))
        assert r.page_size > 0
    except (ValueError, BadRequestKeyError, AssertionError):
        r.page_size = config.PAGINATION_DEFAULT
    if r.page_size > config.PAGINATION_LIMIT:
        r.page_size = config.PAGINATION_LIMIT

    if config.QUERY_PAGE in data or config.QUERY_PAGE in args:
        try:
            r.page = abs(int(data.get(config.QUERY_PAGE) or args.get(config.QUERY_PAGE))) or 1
        except ValueError:
            r.page = 1

    if headers:
        r.if_modified_since = weak_date(headers.get('If-Modified-Since'))
        r.if_none_match = _etag_parse('If-None-Match', headers)
        r.if_match = _etag_parse('If-Match', headers)

    return r


def payload():
    """ Performs sanity checks or decoding depending on the Content-Type,
    then returns the request payload as a dict. If request Content-Type is
    unsupported, aborts with a 400 (Bad Request).
    """
    content_type = request.headers.get('Content-Type', '').split(';')[0] or 'application/json'

    if content_type in config.JSON_REQUEST_CONTENT_TYPES:
        return request.get_json(force=True)
    elif content_type == 'application/x-www-form-urlencoded':
        return multidict_to_dict(request.form) if len(request.form) else \
            abort(400, description='No form-urlencoded data supplied')
    elif content_type == 'multipart/form-data':
        # as multipart is also used for file uploads, we let an empty
        # request.form go through as long as there are also files in the
        # request.
        if len(request.form) or len(request.files):
            # merge form fields and request files, so we get a single payload
            # to be validated against the resource schema.

            formItems = MultiDict(request.form)

            if config.MULTIPART_FORM_FIELDS_AS_JSON:
                for key, lst in formItems.lists():
                    new_lst = []
                    for value in lst:
                        try:
                            new_lst.append(json.loads(value))
                        except ValueError:
                            new_lst.append(json.loads('"{0}"'.format(value)))
                    formItems.setlist(key, new_lst)

            payload = CombinedMultiDict([formItems, request.files])
            return multidict_to_dict(payload)

        else:
            abort(400, description='No multipart/form-data supplied')
    else:
        abort(400, description='Unknown or no Content-Type header supplied')
