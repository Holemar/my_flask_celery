# -*- coding: utf-8 -*-

"""
View Class
"""
import re
import os
import json
import copy
import logging
import traceback
import requests
from operator import attrgetter
from itertools import groupby
from io import StringIO
from io import BytesIO
import zipfile
from datetime import datetime
from urllib.parse import quote

import mongoengine
from flask import request, abort, Response
from flask import current_app as app
from bson import ObjectId
from mongoengine.queryset.visitor import Q
from mongoengine.fields import LazyReferenceField, ReferenceField
from werkzeug.exceptions import NotFound, Unauthorized, HTTPException, Forbidden, BadRequest

from bello_adam.exceptions import CommonException, BussinessCommonException
from bello_adam.serializer import serialize, dict_to_mongo, mongo_to_dict
# from bello_adam.distributed_tracing import trace
from bello_adam.io.fields import RelationField
from .utils import parse_request, payload
from elasticsearch_dsl import Q as ESQ
from .documents.base import IDocument
from opentracing_instrumentation.request_context import get_current_span
import bello_jmespath
from bello_adam.helper.format import SuperFormatter
from bello_adam.utils import get_access_from_request
from bello_adam.helper.decorator_util import condition_span_trace

logger = logging.getLogger(__name__)
_enable_profile = os.environ.get('PROFILE') != None
_env = os.environ.get('ENV') or 'development'
JAEGER_AGENT_HOST = os.environ.get('JAEGER_AGENT_HOST')


class ResourceView(object):
    """
    ResourceView, 实现资源类的控制器逻辑（CRUD）
        acl = [
            {
                'property': 'find',
                'principal': '$owner',
                'permission': 'allow'
            }
        ]
    """
    model = None
    app = None
    acl = []

    meta = {
        'datasource': 'mongodb',
        'target_resource': None
    }

    methods = {
        'collection_create': {'methods': ['POST']},
        'collection_count': {'methods': ['GET'], 'url': 'count'},
        'collection_read': {'methods': ['GET']},
        'collection_read_random': {'methods': ['GET'], 'url': 'random'},
        'collection_import': {'methods': ['POST'], 'url': 'import'},
        'item_read': {'methods': ['GET']},
        'item_update': {'methods': ['PUT']},
        'item_delete': {'methods': ['DELETE']},
        'batch_update': {'methods': ['PUT']},
        'batch_delete': {'methods': ['DELETE']}
    }

    reference_methods = {
        'item_reference_create': {'methods': ['POST']},
        'item_reference_read': {'methods': ['GET']},
        'item_reference_delete': {'methods': ['DELETE']}
    }

    embedded_methods = {
        'item_embedded_list_create': {'methods': ['POST']},
        'item_embedded_list_update': {'methods': ['PUT'], 'params': {'index': 'regex(r"\d+")'}},
        'item_embedded_list_delete': {'methods': ['DELETE'], 'params': {'index': 'regex(r"\d+")'}}
    }

    relation_methods = {
        'item_relation_create': {'methods': ['POST']},
        'item_relation_count': {'methods': ['GET'], 'url': 'count'},
        'item_relation_read': {'methods': ['GET']}
    }

    query_methods = {
        'item_sync': {
            'methods': ['POST'],
            'url': 'sync'
        },
        'collection_sync': {
            'methods': ['POST'],
            'url': 'sync'
        },
        'collection_query': {
            'methods': ['GET'],
            'url': 'query'
        }
    }

    graph_methods = {
        'collection_import': {'methods': ['POST'], 'url': 'import'},
        'collection_graph_node_read': {'methods': ['GET']},
        'collection_graph_node_read_all_between': {'methods': ['GET'], 'url': 'between'},
        'collection_graph_node_create': {'methods': ['POST']},
        'item_graph_node_connect': {'methods': ['POST'], 'url': 'connect'},
        'item_graph_node_update': {'methods': ['PUT']},
        'item_graph_node_delete': {'methods': ['DELETE']},
        'item_graph_node_import': {'methods': ['POST'], 'url': 'import'},
        'item_graph_node_expand': {'methods': ['POST'], 'url': 'expand'}
    }

    def __init__(self, app, model, routes):
        self.model = model
        self.name = ''
        if model:
            self.name = model.__name__.lower()
        self.app = app
        self.routes = routes
        if _enable_profile:
            import cProfile
            self.pr = cProfile.Profile()

    def __call__(self, *args, **kwargs):
        """
        Flask view function entrypoint
            * middleware, 倒置的顺序开始跑

            middleware1
            middleware2
            middleware3

            执行的顺序:

            middleware1 before
            middleware2 before
            middleware3 before
            rest
            middleware3 after
            middleware2 after
            middleware1 after
        """

        if _enable_profile:
            self.pr.enable()

        reserved_middlewares = list(reversed(self.app.available_middlewares))

        # pre process request
        _, action, resource, _ = request.endpoint.split('|')
        request.resource = resource
        request.action = action
        request.view = self

        result = None
        try:
            def current(): return self.dispatch_request(*args, **kwargs)
            for mw in reserved_middlewares:
                current = mw(current)
            result = current()
        except Exception as ex:
            result = self.render_error(400, str(ex), ex)

        if _enable_profile:
            self.pr.disable()
            self.pr.print_stats()

        return result

    def _patch_where(self):
        if self.model._meta.get('where'):
            where = copy.deepcopy(self.model._meta['where'])
            where.update(request.req.where or {})
            request.req.where = where

    def _patch_included(self, items, included_fields):
        if not included_fields:
            return items
        if items and isinstance(items[0], IDocument):
            for item in items:
                for field in included_fields:
                    if field in self.model._fields and item[field] and \
                            isinstance(self.model._fields[field], LazyReferenceField):
                        try:
                            item[field] = item[field].fetch()
                        except item[field].document_type.DoesNotExist:
                            logger.warning(
                                f'reference doesnot exist: {field}:{item[field].pk} in model {self.model.__name__}')
                            item[field] = None
        elif items and isinstance(items[0], dict):
            id_map_index = {ObjectId(item['id']): index for index, item in enumerate(items)}
            ids = list(id_map_index.keys())
            for field in included_fields:
                orm_field = self.model._fields.get(field)
                if not orm_field:
                    continue
                if isinstance(orm_field, RelationField):
                    # TODO: 即使是 has one 也是返回 [] 结构
                    for item in items:
                        item[field] = []
                    target_field = orm_field.target_field
                    query = {f'{target_field}__in': ids}
                    only_fields = orm_field.document_type._meta.get('included_fields', [])
                    objects = orm_field.document_type.objects(**query).only(*only_fields)
                    for object in objects:
                        id = getattr(object, target_field).id
                        items[id_map_index[id]][field].append(mongo_to_dict(object, only_fields=only_fields))
                elif isinstance(orm_field, LazyReferenceField):
                    query = {'id__in': [item[orm_field.name] for item in items]}
                    only_fields = orm_field.document_type._meta.get('included_fields', [])
                    objects = orm_field.document_type.objects(**query).only(*only_fields)
                    ref_map_data = {str(object.id): mongo_to_dict(object, only_fields=only_fields)
                                    for object in objects}
                    for item in items:
                        item[orm_field.name] = ref_map_data.get(item[orm_field.name]) or {}

    # @trace()
    def dispatch_request(self, *args, **kwargs):
        """
        分发请求主逻辑：
            * 解析请求信息（request.req）
            * item类型的，获取对应的object
            * 结果返回包装 （json）
        """
        try:
            response = None
            handler = None
            # logger.debug(request.method + ' - ' + request.endpoint)
            if request.method == 'OPTIONS':
                response = self.options()
            elif '|' in request.endpoint:
                # 解析请求，并放入request ctx
                req = parse_request(self.model)
                request.req = req
                endpoint = request.endpoint
                source, action, _, _ = endpoint.split('|')
                is_collection = action.startswith('collection')
                is_item = action.startswith('item')
                is_batch = action.startswith('batch')
                is_proxy = action.startswith('proxy')
                is_remote_item = action.startswith('remote_item')
                is_customize = '@' in action
                instance = None
                if is_customize:
                    real_action = action.split('@')[-1]
                    if is_item:
                        handler = self.routes['item'][real_action]['function_name']
                    elif is_collection:
                        handler = self.routes['collection'][real_action]['function_name']
                    elif is_remote_item:
                        handler = self.routes['remote_item'][real_action]['function_name']
                    else:
                        logger.error('Unknow handler %s', action)
                        abort(400, 'Bad Request')
                else:
                    handler = action
                if handler:
                    if is_batch:
                        if self.model:
                            data = request.json
                            ids = data.get('ids', [])
                            instances = self.model.find_by_ids(ids)
                            kwargs['instances'] = instances
                    if is_item:
                        # 支持item, item_customize
                        if not is_proxy and self.model:
                            item_condition = {}
                            id_field = self.model._meta.get('item_id_field') or 'id'
                            if self.model.is_valid_id(kwargs['id']):
                                item_condition['id'] = kwargs['id']
                            elif id_field != 'id':
                                item_condition[id_field] = kwargs['id']
                            else:
                                raise NotFound
                            if not self.model:
                                abort(400, 'Bad Request')
                            instance = self.model.find_one(item_condition)
                            if not instance:
                                raise NotFound
                            kwargs['instance'] = instance
                            del kwargs['id']
                    # if not self.has_permission(action, endpoint, instance):
                    if not self.has_access(endpoint, instance) and not app.config.get('DEBUG'):
                        raise Forbidden
                    function = getattr(self, handler)
                    # if JAEGER_AGENT_HOST:
                    #     op_name = op_name = re.sub('(<|bound |method |of |function |object |at 0x\w+|>)',
                    #                                '', str(function)).strip()
                    #     get_current_span().set_operation_name(op_name)
                    response = function(**kwargs)
                else:
                    raise NotFound
            if isinstance(response, Response):
                return response
            elif isinstance(response, requests.models.Response):
                headers = dict(response.headers)
                return Response(response.content, response.status_code, headers=headers)
            else:
                return self.render_obj(response)
        except mongoengine.queryset.DoesNotExist as ex:
            return self.render_error(400, '不存在', ex)
        except Unauthorized as ex:
            return self.render_error(401, '未授权', ex)
        except NotFound as ex:
            return self.render_error(400, '不存在', ex)
        except BadRequest as ex:
            return self.render_error(ex.code, ex.description)
        except BussinessCommonException as ex:
            return self.render_bussiness_error(ex)
        except CommonException as ex:
            return self.render_error(ex.code, ex.message)
        except Exception as ex:
            logger.error(ex) # render_error 里会单独打印call stack,这里就不用exception了,
            return self.render_error(400, '未知错误', ex)

    def render_obj(self, obj):
        included = None
        if hasattr(request, 'req'):
            included = request.req.included or []
        response = serialize('_root', obj, None, included=included)
        ua = request.headers.get('User-Agent')
        # ugly fix for IE
        mimetype = 'text/html' if (ua and re.search(r'MSIE\s[6-9]', ua)) else 'application/json'
        return Response(json.dumps(response), status=200, mimetype=mimetype)
    
    def render_bussiness_error(self, exception):
        ua = request.headers.get('User-Agent')
        # ugly fix for IE
        mimetype = 'text/html' if re.search(r'MSIE\s[6-9]', ua) else 'application/json'
        return Response(str(exception), status=exception.status_code, mimetype=mimetype)

    def render_error(self, code, message, ex=None):
        detail = None
        callstack = None
        if ex:
            if hasattr(ex, 'code') and ex.code:
                code = ex.code
            detail = str(ex)
            traceback.print_exc()
            if _env != 'production':
                callstack = traceback.format_exc().splitlines()
            # Notification
            app.error_service.notify(request, ex)

        error = {
            'error': {
                'code': code,
                'message': message,
                'detail': detail,
                'callstack': callstack
            }
        }

        logger.error(error)

        ua = request.headers.get('User-Agent')
        # ugly fix for IE
        mimetype = 'text/html' if re.search(r'MSIE\s[6-9]', ua) else 'application/json'
        return Response(json.dumps(error), status=code, mimetype=mimetype)

    @condition_span_trace(os.environ.get('ELASTIC_APM_SERVER_URL'))
    def has_access(self, endpoint, instance=None):
        """
        endpoint: $create, $read, $updaet, $delete, other_action
        allow: True/False
            {
                'endpoint': 'find',
                'allow': True
            }
        """
        user = getattr(request, 'user', None)
        _, action, _, _ = request.endpoint.split('|')
        rows = get_access_from_request()
        results = []
        for row in rows:
            scope = row.get('scope')
            allow = row['allow']
            if action.startswith('item_'):
                if scope == 'company':
                    if user and instance:
                        resource_company = None
                        if instance._class_name == 'Company' or instance.__class__.__bases__[0].__name__ == 'Company':
                            resource_company = instance
                        elif hasattr(instance, 'owned_company'):
                            resource_company = instance.owned_company
                        elif hasattr(instance, 'user'):
                            resource_company = app.models['User'].objects(id=instance.user.id).first().owned_company
                        if request.user.owned_company == resource_company:
                            results.append(allow)
                elif scope == 'owner' or scope == 'company':
                    if user and instance:
                        resource_user_id = None
                        if instance._class_name == 'User' or instance.__class__.__bases__[0].__name__ == 'User':
                            resource_user_id = instance.id
                        elif instance.user:
                            resource_user_id = instance.user.id
                        if request.user.id == resource_user_id:
                            results.append(allow)
                else:
                    results.append(allow)
            else:
                results.append(allow)

        if True in results and False not in results:
            return True
        else:
            return False

    def options(self):
        """
        HTTP OPTIONS handler
        """
        return {}

    def fetch_remote_response(self, target_resource, method, data=None, args=None):
        source = self.meta.get('name')
        return self.fetch_other_remote_response(source, target_resource, method, data, args=args)

    def fetch_other_remote_response(self, source, target_resource, method, data=None, args=None):
        config = app.config['REST_CONNECTIONS'].get(source)
        env = request.args.get('_env') or request.headers.get('Rest-Env') or 'default'
        detail_config = config.get(env, config.get('default', {}))
        api_key = detail_config.get('api-key')
        token = detail_config.get('token')
        url = detail_config['url'] + target_resource
        headers = {}

        try:
            data = data or request.json
        except:
            pass

        if token:
            headers['Authorization'] = 'Bearer ' + token
        elif api_key:
            headers['X-API-Key'] = api_key

        # Fetch the URL, and stream it back
        logger.info("Fetching with headers: %s", url)
        logger.debug(headers)

        params = args or request.args
        return requests.request(method, url, files=request.files, params=params, json=data, headers=headers)

    def collection_download_to_csv(self, data, prefix, header=None):
        file_name = prefix + '_' + datetime.now().strftime('%Y-%m-%d') + '.csv'
        content_disposition = 'attachment; filename*=UTF-8\'\'%s' % quote(file_name)
        headers = {
            'Content-Type': 'plain/text',
            'Content-Disposition': content_disposition
        }
        text = ''
        if header:
            text = ','.join(header) + '\n'
        for item in data:
            text = text + ','.join(item) + '\n'
        response = Response(text, headers=headers, mimetype='plain/text',
                            direct_passthrough=True)
        return response

    def collection_download_to_json_zip(self, items, prefix=''):
        file_name = self.name + '_' + prefix + '_' + datetime.now().strftime('%Y-%m-%d') + '.zip'
        content_disposition = 'attachment; filename*=UTF-8\'\'%s' % quote(file_name)
        headers = {
            'Content-Type': 'application/zip',
            'Content-Disposition': content_disposition
        }
        # This is my zip file
        buff = BytesIO()
        zip_archive = zipfile.ZipFile(buff, mode='w')

        for item in items:
            fb = StringIO()
            fb.write(json.dumps(item.to_dict()))
            zip_archive.writestr(str(item.id) + '.json', fb.getvalue())

        zip_archive.close()
        response = Response(buff.getvalue(), headers=headers, mimetype='application/zip',
                            direct_passthrough=True)
        return response

    def collection_import(self):
        """
        collection import endpoint POST
            - csv data import
        """
        data = request.get_json() or {}
        items = self.model.import_csv(data)
        return {
            'items': items
        }

    def collection_query(self):
        """
        collection query endpoint GET
        """
        self._patch_where()
        response = {}
        # meta-hidden
        hidden = self.model._meta.get('hidden', [])
        protected = self.model._meta.get('protected', [])
        exclude_fields = hidden + protected

        exclude_fields = list(filter(lambda x: x in self.model._fields, exclude_fields))

        if not self.model._meta.get('index'):
            abort(400, 'Resource not allowed to query')
        indexer = None

        # Launch query
        response = app.indexer.find(self.model, request.req, [])

        # build items
        return {
            'items': response['items'],
            'meta': {
                'page': request.req.page,
                'max_results': request.req.max_results,
                'total': response['total']
            }
        }

    def collection_count(self):
        """
        collection count endpoint GET
        """
        self._patch_where()
        response = {}
        by = request.req.by

        # meta-hidden
        hidden = self.model._meta.get('hidden', [])
        protected = self.model._meta.get('protected', [])
        exclude_fields = hidden + protected
        exclude_fields = list(filter(lambda x: x in self.model._fields, exclude_fields))

        user = request.user if hasattr(request, 'user') else None
        owned_company = request.owned_company if hasattr(request, 'owned_company') else None
        rows = get_access_from_request()
        scope = [row.get('scope', None) for row in rows]
        queryset = None
        if None in scope:
            queryset = self.model.objects()
        elif 'company' in scope and self.model._fields.get('owned_company') and owned_company:
            queryset = self.model.objects().by_company(owned_company)
        elif 'company' in scope and app.models['Company']._meta['collection'] == 'company':
            queryset = self.model.objects(id=owned_company.id)
        elif 'company' in scope and not self.model._fields.get('owned_company') and self.model._fields.get('user') and user:
            queryset = self.model.objects().by_own(user)
        elif 'owner' in scope and self.model._fields.get('user') and user:
            queryset = self.model.objects().by_own(user)
        else:
            queryset = self.model.objects()

        items = []
        count = queryset.filter(**request.req.where).count()
        _query = queryset.filter(**request.req.where)._query
        sort = request.req.sort
        transformed_sort = {}
        for s in sort:
            if s.startswith('-'):
                transformed_sort[s[1:]] = -1
            elif s.startswith('+'):
                transformed_sort[s[1:]] = 1
            else:
                transformed_sort[s] = -1

        if by:
            pipeline = [
                {"$match": _query},
                {"$group": {"_id": '$' + by, "count": {"$sum": 1}}},
                {"$sort": transformed_sort},
            ]
            items = list(queryset.aggregate(*pipeline))

        # build items
        return {
            'items': items,
            'meta': {
                'total': count
            }
        }

    def collection_read_random(self):
        # meta-hidden
        hidden = self.model._meta.get('hidden', [])
        protected = self.model._meta.get('protected', [])

        if not self.model._meta.get('index'):
            abort(400, 'Resource not allowed to random')
        indexer = None

        # Launch query
        response = app.indexer.findByRandom(self.model, request.req)

        # build items
        return {
            'items': response['items'],
            'meta': {
                'page': request.req.page,
                'max_results': request.req.max_results,
                'total': response['total']
            }
        }

    def collection_read(self):
        """
        collection endpoint GET
        """
        response = {}
        all_conditions = []
        limit = int(request.req.max_results or 25)  # 每页显示多少行
        page = int(request.req.page or 1)  # 第几页
        sort = request.req.sort
        only_fields = request.req.only
        included_fields = request.req.included or []
        q = request.req.q

        # meta-hidden
        self._patch_where()
        hidden = self.model._meta.get('hidden', [])
        protected = list(set(self.model._meta.get('protected', [])) - set(included_fields))
        exclude_fields = hidden + protected
        search_fields = self.model._meta.get('search_fields', [])

        if only_fields:
            exclude_fields = list(set(self.model._fields.keys() - set(only_fields + ['id'])))

        # exclude_fields = list(filter(lambda x: x in self.model._fields, exclude_fields))
        search_fields = list(filter(lambda x: x in self.model._fields, search_fields))

        user = request.user if hasattr(request, 'user') else None
        owned_company = request.owned_company if hasattr(request, 'owned_company') else None
        rows = get_access_from_request()
        if rows:
            scope = [row.get('scope', None) for row in rows]
        else:
            scope = []
        queryset = None
        if None in scope:
            queryset = self.model.objects()
        elif 'company' in scope and self.model._fields.get('owned_company') and owned_company:
            companies = [str(owned_company.id)]
            queryset = self.model.objects().by_companies(companies, self.model._meta.get('share_filter'))
            all_conditions.append(ESQ('bool', should=list(map(lambda x: ESQ('match', owned_company=x), companies))))
        elif 'company' in scope and app.models['Company']._meta['collection'] == 'company':
            companies = []
            queryset = self.model.objects(id=owned_company.id)
            all_conditions.append(ESQ('bool', should=list(map(lambda x: ESQ('match', owned_company=x), companies))))
        elif 'company' in scope and not self.model._fields.get('owned_company') and self.model._fields.get('user') and user:
            users = [str(user.id)]
            all_conditions.append(ESQ('bool', should=list(map(lambda x: ESQ('match', user=x), users))))
            queryset = self.model.objects().by_users(users, self.model._meta.get('share_filter'))
        elif 'owner' in scope and self.model._fields.get('user') and user:
            users = [str(user.id)]
            all_conditions.append(ESQ('bool', should=list(map(lambda x: ESQ('match', user=x), users))))
            queryset = self.model.objects().by_users(users, self.model._meta.get('share_filter'))
        else:
            queryset = self.model.objects()

        if q:
            _filter = None
            if ObjectId.is_valid(q):
                _filter = Q(id=q)
            elif search_fields:
                _first_filter = search_fields[0]
                _filter = Q(**{_first_filter + '__icontains': q})
                for sf in search_fields[1:]:
                    _filter = _filter | Q(**{sf + '__icontains': q})
            else:
                logger.warn('Invalid query %s', q)
            queryset = queryset.filter(_filter)

        if self.model._meta.get('collection_read_src') == 'es':
            resp = self.app.indexer.find(self.model, request.req, all_conditions, included_fields)
            count = resp["total"]
            items = resp["items"]
        else:
            req_where = request.req.where
            req_query = Q(**req_where)
            external_query_info = getattr(request, "external_query_info") \
                if hasattr(request, "external_query_info") else None
            if external_query_info:
                and_list = external_query_info.get("and")
                or_list = external_query_info.get("or")
                if and_list:
                    for and_q in and_list:
                        req_query = req_query & and_q
                if or_list:
                    for or_q in or_list:
                        req_query = req_query | or_q

            count = queryset.filter(req_query).count()  # 总数
            # 页码防呆
            max_page = int((count + limit - 1) // limit)  # 最大页码
            page = max_page if page > max_page else page
            page = 1 if page < 1 else page
            skip = (page - 1) * limit
            # 取数据
            items = queryset.filter(req_query).exclude(*exclude_fields).order_by(*sort).limit(limit).skip(skip)

        # items = list(items)
        items = items if isinstance(items, list) else list(items)
        self._patch_included(items, included_fields)

        # build items
        response = {
            'items': items,
            'meta': {
                'page': page,
                'max_results': limit,
                'total': count
            }
        }
        return response

    def _before_collection_create(self):
        pass

    def collection_create(self):
        """
        collection endpoint POST
        """
        self._before_collection_create()
        data = payload()
        create_data = dict_to_mongo(self.model, data)
        instance = self.model()
        if create_data:
            for k, v in create_data.items():
                o = v
                field = self.model._fields.get(k)
                if field:
                    if isinstance(field, mongoengine.GenericLazyReferenceField):
                        o = self.app.models[field.name.capitalize()].objects(id=v).first()
                    elif isinstance(field, mongoengine.LazyReferenceField):
                        field_cls_name = field.document_type._class_name
                        if field_cls_name == self.model._class_name:
                            o = self.model.objects(id=v).first()
                        else:
                            o = self.app.models[field_cls_name].objects(id=v).first()
                        if not o:
                            abort(400, "%s资源不存在" % field_cls_name)
                    instance[k] = o

        user = request.user if hasattr(request, 'user') else None
        owned_company = request.owned_company if hasattr(request, 'owned_company') else None
        if user and self.model._fields.get('user') and not create_data.get('user'):
            instance.user = request.user
        if owned_company and self.model._fields.get('owned_company') and not create_data.get('owned_company'):
            instance.owned_company = request.owned_company
        instance.save()
        return instance

    def collection_graph_node_create(self):
        """
        collection graph endpoint POST
        """
        data = payload()
        instance = self.model(**data)
        instance.save()
        return instance

    def item_graph_node_delete(self, instance):
        return instance.delete()

    def item_graph_node_update(self, instance):
        data = payload()
        for k, v in data.items():
            setattr(instance, k, v)
        instance.save()
        return instance

    def item_graph_node_import(self, instance):
        data = payload()
        relation = data.get('relation')
        target = data.get('target')

        if not target or not relation:
            abort(400, 'Invalid Parameter')

        target_class = target.capitalize()
        rel_map = self.model.get_relations_map()
        if target_class not in rel_map or relation not in rel_map[target_class]:
            abort(400, 'Invalid Parameter (relation not exist)')

        rel_field = rel_map[target_class][relation]['field']
        target_model = self.app.models.get(target_class)
        if not getattr(self.model, rel_field) or not target_model:
            abort(400, 'Invalid Parameter')

        items = target_model.import_csv(data)
        for item in items:
            status = getattr(instance, rel_field).connect(item)
        return {
            'items': items
        }


    def item_graph_node_connect(self, instance):
        data = payload()
        targets = data.get('targets') or []
        relation = data.get('relation')

        if not targets or not relation or not hasattr(instance, relation):
            abort(400, 'Invalid Parameter')

        node_relation = getattr(self.model, relation)
        target_model = node_relation.definition['node_class']

        result = []
        for target in targets:
            target_node = target_model.find_one_by_id(target)
            if not target_node:
                result.append({'id': target, 'status': False, 'reason': 'not exist'})
            else:
                status = getattr(instance, relation).connect(target_node)
                result.append({'id': target, 'status': status, 'reason': ''})
        return result

    def item_graph_node_expand(self, instance):
        included = request.req.included
        ref_nodes, ref_rels = self.model.find_references_by_ids([instance.id], included)
        rel_nodes, rel_rels = self.model.find_relations_by_ids([instance.id], included)
        return {
            'nodes': ref_nodes + rel_nodes,
            'edges': ref_rels + rel_rels
        }

    def collection_graph_node_read_all_between(self):
        args = request.args
        left = args.get('left')
        right = args.get('right')
        nodes = []
        edges = []

        if left and right:
            nodes, edges = self.model.find_all_between_two(left, right)

        return {
            'nodes': nodes,
            'edges': edges
        }

    def collection_graph_node_read(self):
        """
        graph endpoint GET
        """
        response = {}
        limit = request.req.max_results
        sort = request.req.sort
        included = request.req.included
        q = request.req.q

        count = len(self.model.nodes._get(**request.req.where))
        items = self.model.nodes._get(limit=limit, **request.req.where)
        items = list(items)

        ids = list(map(lambda x: x.id, items))

        # find_relations_by_ids
        target_nodes = []
        all_nodes = items
        rels = []
        target_nodes, rels = self.model.find_relations_by_ids(ids, included)
        all_nodes = all_nodes + target_nodes

        unique_items = []
        for _, g in groupby(all_nodes, key=attrgetter('id')):
            g = list(g)
            unique_items.append(g[0])

        # unique.
        all_nodes
        # build items
        response = {
            'items': items,
            'related': {
                'nodes': unique_items,
                'edges': rels
            },
            'meta': {
                'page': request.req.page,
                'max_results': request.req.max_results,
                'total': count
            }
        }
        return response

    def batch_update(self, instances):
        """
        batch endpoint PUT
        """
        form = payload()
        data = form.get('data', {})
        update = dict_to_mongo(self.model, data)
        if update:
            for instance in instances:
                for k, v in update.items():
                    instance[k] = v
                instance.save()
        return instances

    def batch_delete(self, instances):
        """
        batch endpoint PUT
        """
        for instance in instances:
            instance.delete()
        return {'deleted': True}

    def item_read(self, instance):
        """
        item endpoint GET
        """
        return instance

    def item_embedded_list_create(self, instance):
        """
        item embedded endpoint POST
        """
        data = payload()
        embedded = request.endpoint.split('|')[-1]
        embedded_field = instance._fields.get(embedded).field
        embedded_instance = embedded_field.document_type(**data)
        instance[embedded].append(embedded_instance)
        instance.save()
        return instance

    def item_embedded_list_delete(self, instance, index):
        """
        item embedded count GET
        """
        index = int(index)
        embedded = request.endpoint.split('|')[-1]
        embedded_field = instance._fields.get(embedded).field
        if len(instance[embedded]) < index:
            abort(400, 'Out of Range')
        instance.save()
        del instance[embedded][index]
        instance.save()
        return instance

    def item_embedded_list_update(self, instance, index):
        """
        item embedded count GET
        """
        data = payload()
        index = int(index)
        embedded = request.endpoint.split('|')[-1]
        embedded_field = instance._fields.get(embedded).field
        if len(instance[embedded]) < index:
            abort(400, 'Out of Range')
        update = embedded_field.document_type(**data)
        instance[embedded][index] = update
        instance.save()
        return instance

    def item_reference_create(self, instance):
        """
        item reference endpoint POST
        """
        data = payload()
        reference = request.endpoint.split('|')[-1]
        reference_field = instance._fields.get(reference)
        current_reference = instance[reference]
        if current_reference:
            abort(400, 'Reference Exist')
        reference_instance = reference_field.document_type(**data)
        if hasattr(request, 'user') and self.model._fields.get('user'):
            reference_instance.user = request.user
        if hasattr(request, 'owned_company') and self.model._fields.get('owned_company'):
            reference_instance.owned_company = request.owned_company
        reference_instance.save()
        instance[reference] = reference_instance
        instance.save()
        return instance

    def item_reference_delete(self, instance):
        """
        item reference DELETE
        """
        reference = request.endpoint.split('|')[-1]
        reference_field = instance._fields.get(reference)
        if reference_field:
            reference_ref = instance[reference]
            if reference_ref:
                reference_instance = reference_ref.fetch()
                if reference_instance:
                    reference_instance.delete()
                instance[reference] = None
        instance.save()
        return instance

    def item_reference_read(self, instance):
        """
        item reference GET
        """
        reference = request.endpoint.split('|')[-1]
        reference_field = instance._fields.get(reference)
        if reference_field:
            obj = getattr(instance, reference)
            if isinstance(reference_field, ReferenceField):
                return obj
            elif isinstance(reference_field, LazyReferenceField):
                obj.fetch()
        return None

    def item_reference_file(self, instance, field, sub_field):
        """
        item reference GET
        """
        file_proxy = getattr(instance, field)
        # file_proxy = getattr(reference_obj, sub_field)
        method = request.args.get('method') or 'inline'
        response = file_proxy.read()
        if not response:
            abort(400, 'Not Exist')

        content_disposition = method
        if file_proxy.name:
            content_disposition = '%s; filename*=UTF-8\'\'%s' % (
                method, quote(file_proxy.name))

        headers = {
            'Content-Type': file_proxy.content_type,
            'Content-Disposition': content_disposition
        }
        if isinstance(response, bytes):
            data = response
            headers['Last-Modified'] = file_proxy.grid_id.generation_time
        else:
            headers['ETag'] = response['meta']['ETag']
            headers['Last-Modified'] = response['meta']['Last-Modified']
            data = response['data']
        response = Response(data, headers=headers, mimetype=file_proxy.content_type,
                            direct_passthrough=True)
        return response

    def item_relation_create(self, instance):
        """
        item relations endpoint POST
        """
        data = payload()
        relation = request.endpoint.split('|')[-1]
        relation_ref = getattr(instance, relation)
        relation_instance = relation_ref.document_type(**data)
        if hasattr(request, 'user') and self.model._fields.get('user'):
            relation_instance.user = request.user
        if hasattr(request, 'owned_company') and self.model._fields.get('owned_company'):
            relation_instance.owned_company = request.owned_company
        relation_instance[relation_ref.target_field] = instance
        relation_instance.save()
        return relation_instance

    def item_relation_count(self, instance):
        """
        item relations count GET
        """
        by = request.req.by
        relation = request.endpoint.split('|')[-1]
        relation_ref = getattr(instance, relation)
        if relation_ref:
            queryset = relation_ref.objects(**request.req.where)
            items = []
            count = queryset.count()
            if by:
                pipeline = [
                    {"$group": {"_id": '$' + by, "count": {"$sum": 1}}}
                ]
                items = list(queryset.aggregate(*pipeline))
            return {
                'items': items,
                'meta': {
                    'total': count
                }
            }
        return None

    def item_relation_read(self, instance):
        """
        item relations GET
        """
        limit = int(request.req.max_results or 25)  # 每页显示多少行
        page = int(request.req.page or 1)  # 第几页
        sort = request.req.sort

        relation = request.endpoint.split('|')[-1]

        relation_ref = getattr(instance, relation)
        if relation_ref:
            # relation limit...
            queryset = relation_ref.objects(**request.req.where)
            count = queryset.count()  # 总数
            # 页码防呆
            max_page = int((count + limit - 1) // limit)  # 最大页码
            page = max_page if page > max_page else page
            page = 1 if page < 1 else page
            skip = (page - 1) * limit
            # 取数据
            items = queryset.order_by(*sort).limit(limit).skip(skip)
            return {
                'items': list(items),
                'meta': {
                    'page': page,
                    'max_results': limit,
                    'total': count
                }
            }
        return None

    def item_file_preview(self, instance):
        """
        item file preview GET
        """
        cos_id = instance.attachment.cos_id
        _file = request.endpoint.split('|')[-1]
        file_proxy = getattr(instance, _file)
        return file_proxy.getPreview()

    def item_file(self, instance):
        """
        item file GET
        """
        cos_id = instance.attachment.cos_id
        _file = request.endpoint.split('|')[-1]
        file_proxy = getattr(instance, _file)
        method = request.args.get('method') or 'inline'
        response = file_proxy.read(cos_id)
        if not response:
            abort(400, 'Not Exist')

        content_disposition = response['meta']['Content-Disposition']
        if file_proxy.name:
            content_disposition = '%s; filename*=UTF-8\'\'%s' % (
                method, quote(file_proxy.name))

        headers = {
            'Content-Type': response['meta']['Content-Type'],
            'Content-Disposition': content_disposition,
            'ETag': response['meta']['ETag'],
            'Last-Modified': response['meta']['Last-Modified']
        }
        response = Response(response['data'], headers=headers, mimetype=headers['Content-Type'],
                            direct_passthrough=True, content_type=response['meta']['Content-Type'])
        return response

    def _before_item_update(self):
        pass

    def item_update(self, instance):
        """
        item endpoint PUT
        """
        self._before_item_update()
        data = payload()
        update = dict_to_mongo(self.model, data)
        if update:
            for k, v in update.items():
                instance[k] = v
            instance.save()
            # instance.update(**update)
        return instance

    def collection_sync(self):
        """
        collection endpoint sync
        """
        instances = self.model.objects.all()
        for instance in instances:
            logger.debug('Syncing instance %s', str(instance.id))
            instance.apply_index('replace')
        return {}

    def item_sync(self, instance):
        """
        item endpoint sync
        """
        instance.apply_index('replace')
        return {}

    def item_delete(self, instance):
        """
        item endpoint PUT
        """
        instance.delete()
        return {'deleted': True}

    def proxy_collection_count(self):
        """
        proxy method
        """
        pass

    def proxy_collection_import(self):
        """
        proxy method
        """
        return self.fetch_remote_response(self.meta['target_resource'] + '/import', 'POST').json()

    def proxy_collection_create(self):
        """
        proxy method
        """
        return self.fetch_remote_response(self.meta['target_resource'], 'POST').json()

    def proxy_collection_query(self):
        """
        proxy method
        """
        return self.fetch_remote_response(self.meta['target_resource'] + '/query', 'GET').json()

    def proxy_collection_read(self):
        """
        proxy method
        """
        return self.fetch_remote_response(self.meta['target_resource'], 'GET').json()

    def proxy_item_read(self, id):
        """
        """
        return self.fetch_remote_response(self.meta['target_resource'] + '/' + id, 'GET').json()

    def proxy_item_update(self, id):
        """
        """
        return self.fetch_remote_response(self.meta['target_resource'] + '/' + id, 'PUT').json()

    def proxy_item_delete(self, id):
        """
        """
        return self.fetch_remote_response(self.meta['target_resource'] + '/' + id, 'DELETE').json()
