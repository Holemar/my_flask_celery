# -*- coding:utf-8 -*-
"""
Elasticsearch MongoDB Model Utility
"""
import logging
import datetime

import elasticsearch
from mongoengine import Document
from mongoengine.fields import *
from elasticsearch_dsl import Search, connections, Q, query, function
from elasticsearch.helpers import bulk, reindex

from .config_util import config
from .es_util import ElasticsearchHelper
from .serializer import mongo_to_dict

logger = logging.getLogger(__name__)


class EsModelUtil:
    es_helper = None
    es = None
    model_class = None
    index_name = None

    def __init__(self, model_class):
        """
        初始化Elasticsearch连接
        :param model_class: mongoengine Document
        """
        self.es_helper = self.init_app()
        self.es = self.es_helper.es
        self.model_class = model_class
        self.index_name = self.get_index_name(model_class)

    @staticmethod
    def init_app():
        """
        初始化 Elasticsearch 连接
        """
        if not config.ELASTIC_CONNECTIONS:
            return
        hosts = config.ELASTIC_CONNECTIONS['hosts']
        http_auth = config.ELASTIC_CONNECTIONS['http_auth']
        client = ElasticsearchHelper(hosts=hosts, http_auth=http_auth)
        return client

    def check(self):
        """
        输出当前系统的ES信息
        """
        return self.es.info()

    @staticmethod
    def get_index_name(model_class):
        """
        获取 Elasticsearch 连接
        """
        index = None
        if hasattr(model_class, '_class_name'):
            index = model_class._class_name.lower()
        elif isinstance(model_class, Document):
            index = model_class._get_collection_name().lower()
        elif isinstance(model_class, type(Document)):
            index = model_class()._get_collection_name().lower()
        if not index:
            index = model_class.__class__.__name__.lower()
        return index

    def get_query_set(self, **kwargs):
        """获取 Elasticsearch 查询集(类似于 mongoengine 的 QuerySet)"""
        return Search(using=self.es, index=self.index_name, **kwargs)

    def filter(self, params: dict, query_set: Search = None, **kwargs):
        """按条件搜索，返回 query_set
        :param params: 查询条件(按 mongoengine 的查询语法)
        :param query_set: Elasticsearch 查询集
        """
        all_conditions = []
        _fields = self.model_class._fields
        for k, v in params.items():
            kk = ''
            rk = k
            if v is None or v == '':
                continue
            if '__' in k:
                rk, kk = k.split('__')
            if rk in _fields:
                field = _fields[rk]
                # if rk == 'id' or (hasattr(field, 'index') and field.index):
                if isinstance(field, StringField) and not kk:
                    all_conditions.append(Q('match', **{rk: {'query': v, 'operator': 'and'}}))
                elif isinstance(field, StringField) and kk == 'in':
                    query_set = query_set.filter('terms', **{rk: v})
                elif isinstance(field, ObjectIdField) and not kk:
                    all_conditions.append(Q('match', **{rk: v}))
                elif isinstance(field, LazyReferenceField) and not kk:
                    all_conditions.append(Q('match', **{rk: v}))
                elif isinstance(field, ObjectIdField) and kk == 'in':
                    all_conditions.append(Q('terms', **{rk: v}))
                elif isinstance(field, IntField) and kk == 'ne':
                    all_conditions.append(~Q('match', **{rk: v}))
                elif isinstance(field, IntField):
                    all_conditions.append(Q('match', **{rk: v}))
                elif isinstance(field, FloatField):
                    all_conditions.append(Q('match', **{rk: v}))
                elif isinstance(field, ListField) and isinstance(field.field, StringField):
                    all_conditions.append(Q('match', **{rk: v}))
                elif isinstance(field, ListField) and isinstance(field.field, EmbeddedDocumentField):
                    all_conditions.append(Q('nested', path=rk, query=Q('match', **{k: v})))
                elif isinstance(field, DateTimeField) and kk:
                    all_conditions.append(Q('range', **{rk: {kk: v.isoformat()}}))
                elif isinstance(field, DateTimeField) and not kk:
                    all_conditions.append(Q('match', **{rk: v.isoformat()}))
                elif isinstance(field, BooleanField):
                    all_conditions.append(Q('term', **{rk: v}))
                elif isinstance(field, DictField) and kk:
                    all_conditions.append(Q('match', **{'%s.%s' % (rk, kk): v}))
                else:
                    logger.warning('Ignore query filter %s', k)
        if query_set is None:
            query_set = self.get_query_set(**kwargs)
        query_set = query_set.query('bool', must=all_conditions)
        return query_set

    def find(self, req, included: list):
        """按条件搜索
        :param req: 公用的前端参数请求类的实例
        :param included: 需要查询的字段列表
        """
        # term, match, range, exactly
        page_size = req.page_size  # 每页显示多少行
        skip = (req.page - 1) * page_size
        sort = req.sort
        search = self.get_query_set()
        hidden = self.model_class._meta.get('hidden', [])
        protected = list(set(self.model_class._meta.get('protected', [])) - set(included))
        exclude_fields = list(set(hidden + protected) - set(req.included or []))
        if exclude_fields:
            search = search.source(exclude=exclude_fields)
        if sort:
            search = search.sort(*sort)
        if req.q:
            search = search.query("query_string", query=req.q)
        elif req.where:
            search = self.filter(req.where, search)
        search = search[skip:skip + page_size]
        response = search.execute()
        total = response.hits.total
        items = []
        for item in response:
            current = item.to_dict()
            current['id'] = item.meta.id
            current['_score'] = item.meta.score
            items.append(current)
        return {
            'total': total,
            'items': items
        }

    def search(self, params: dict = None, query_string=None, random=False, page_size=20):
        """按条件搜索
        :param params: 查询条件(按 mongoengine 的查询语法)
        :param query_string: 查询条件
        :param random: 是否随机取数据
        :param page_size: 取多少条数据
        """
        search = self.get_query_set()
        if query_string:
            search = search.query("query_string", query=query_string)
        if params:
            search = self.filter(params, search)
        if random:
            seed = str(int(datetime.datetime.now().timestamp()))
            search = search.query('function_score', functions=[query.SF('random_score', seed=seed)])
        if not query_string and not params and not random:
            search = search.query('match_all')
        search = search[0:page_size]
        response = search.execute()
        total = response.hits.total
        items = []
        for item in response:
            current = item.to_dict()
            current['id'] = item.meta.id
            current['_score'] = item.meta.score
            items.append(current)
        return {
            'total': total,
            'items': items
        }

    def search_keywords(self, keywords, fields, query_params=None, page_size=20, include_fields=None, exclude_fields=None):
        """
        多个值和字段的模糊匹配查询
        :param keywords: 关键字列表， 参数如: ['搜索关键字1', '搜索关键字2']
        :param fields: 字段列表， 参数如: ['title^2', 'content']   其中 ^2 表示权重加倍
        :param query_params: 其它查询条件， 参数如: {"range": {"age": {"gte": 18, "lte": 30}}}
        :param page_size: 取多少条数据
        :param include_fields: 需要查询的字段列表， 参数如: ['title', 'content']
        :param exclude_fields: 排除的字段列表， 参数如: ['id', 'create_time']
        """
        '''
        params = {
            "query": {
                "multi_match": {  # 多字段模糊匹配，但 multi_match 会对输入的每个词进行分词，导致结果不准确
                    "query": " ".join(keywords),
                    "fields": fields
                }
            }
        }
        '''
        params = {
            "query": {
                "bool": {  # match_phrase 短语精确匹配，是全文搜索，且不分词
                    "should": [
                        {"match_phrase": {field: keyword}} for keyword in keywords for field in fields
                    ]
                }
            },
            "size": page_size
        }
        if query_params:
            params = {
                "query": {
                    "bool": {
                        "must": [
                            query_params,  # 必须过滤的条件
                            {
                                "bool": {
                                    "should": [
                                        {"match_phrase": {field: keyword}} for keyword in keywords for field in fields
                                    ]
                                }
                            }
                        ]
                    }
                },
                "size": page_size
            }
        if include_fields:
            params['_source'] = include_fields
            # params['_source_include'] = include_fields
        if exclude_fields:
            params['_source_exclude'] = exclude_fields
        search_result = self.es_helper.search_documents(self.index_name, params) or {}
        items = search_result.get('hits', {}).get('hits', [])
        items = [item['_source'] for item in items]
        total = search_result.get('hits', {}).get('total', 0)
        return {
            'total': total,
            'items': items
        }

    def analyze(self, text, analyzer, **kwargs):
        return self.es.indices.analyze(index=self.index_name, body={'text': text, 'analyzer': analyzer}, **kwargs)

    def create_index(self, version='', fields=None, body=None, **kwargs):
        """创建索引"""
        index_version_name = self.index_name + '_' + version if version else self.index_name
        if fields and body is None:
            pass  # TODO: 自定义字段映射
            body = {
                "mappings": {
                    "properties": {
                        field: {"type": "text"} for field in fields
                        #"name": {"type": "text"}, "age": {"type": "integer"}
                    }
                }
            }
        return self.es_helper.create_index(index_version_name, body=body, **kwargs)

    def reindex_index(self, source_version, source_type, target_version, target_type, **kwargs):
        """更新索引"""
        if source_version:
            source_index_version_name = self.index_name + '_' + source_version
        else:
            source_index_version_name = self.index_name
        if target_version:
            target_index_version_name = self.index_name + '_' + target_version
        else:
            target_index_version_name = self.index_name
        if self.es.indices.exists(index=source_index_version_name) and \
            self.es.indices.exists(index=target_index_version_name):
            body = {
                "source": {
                    "index": source_index_version_name,
                    "type": source_type
                },
                "dest": {
                    "index": target_index_version_name,
                    "type": target_type
                }
            }
            return self.es.reindex(body=body, wait_for_completion=False, **kwargs)

        return {}


    def delete_index(self, version='', **kwargs):
        """删除索引"""
        index_version_name = self.index_name + '_' + version if version else self.index_name
        return self.es_helper.delete_index(index_version_name, **kwargs)

    def clean_index(self, version='', **kwargs):
        """清空索引"""
        index_version_name = self.index_name + '_' + version if version else self.index_name
        return self.es_helper.clean_index(index_version_name, **kwargs)

    def set_index_master(self, version='', is_master=True, **kwargs):
        index_version_name = self.index_name + '_' + version if version else self.index_name
        master_name = self.index_name
        if self.es.indices.exists(index=index_version_name):
            if is_master:
                return self.es.indices.put_alias(index=index_version_name, name=master_name, **kwargs)
            else:
                return self.es.indices.delete_alias(index=index_version_name, name=master_name, **kwargs)
        return

    def put_index_mapping(self, version='', body: dict = None, **kwargs):
        index_version_name = self.index_name + '_' + version if version else self.index_name
        if self.es.indices.exists(index=index_version_name):
            return self.es.indices.put_mapping(index=index_version_name, body=body, master_timeout='300s', timeout='300s', **kwargs)
        return

    def put_index_settings(self, analysis, version='', **kwargs):
        index_version_name = self.index_name + '_' + version if version else self.index_name
        if self.es.indices.exists(index=index_version_name):
            settings = {
                'analysis': analysis
            }
            self.es.indices.close(index=index_version_name)
            result = None
            try:
                result = self.es.indices.put_settings(index=index_version_name, body=settings, master_timeout='300s', **kwargs)
                self.es.indices.open(index=index_version_name)
            except Exception as ex:
                logger.exception(ex)
            return result
        return

    def list_index(self):
        items = []
        for k, v in self.es.indices.get(index='*%s*' % self.index_name).items():
            _props = k.split('_')
            key = None
            resource = None
            version = None
            if len(_props) == 3:
                key, resource, version = _props
            elif len(_props) == 2:
                key, resource = _props
            alias = v['aliases']
            if alias:
                alias = list(alias.keys())[0]
            items.append({
                'name': k,
                'key': key,
                'resource': resource,
                'version': version,
                'count': self.es.count(index=k)['count'],
                'alias': alias or '',
                'mappings': v['mappings'],
                'types': list(v['mappings'].keys()) or ['_doc'],
                'settings': v['settings']
            })
        return items

    def build_document(self, docs, only_fields=None, exclude_fields=None):
        """Build document, filter unindexed field."""
        documents = []
        only_fields = only_fields or self.model_class._meta.get('es_only_fields')
        exclude_fields = exclude_fields or self.model_class._meta.get('es_exclude_fields')
        for doc in docs:
            _doc = mongo_to_dict(doc, index_only=False, only_fields=only_fields, exclude_fields=exclude_fields)
            documents.append(_doc)
        return documents

    def insert(self, document, document_id=None, **kwargs):
        """Insert document, it must be new if there is ``_id`` in it."""
        if isinstance(document, Document):
            document_id = document_id or document.id
            document = self.build_document([document])[0]
        return self.es_helper.insert_document(self.index_name, document, document_id=document_id, **kwargs)

    def get(self, document_id, **kwargs):
        """get one document with ``_id``."""
        return self.es_helper.get_document(self.index_name, document_id, **kwargs)

    # todo: 批量插入，未能成功
    def bulk_insert(self, docs, suffix=''):
        """Bulk insert documents."""
        models = []
        res = None
        # 如果数量大于 20，则分批插入
        for doc in docs:
            models.append(doc)
            length = len(models)
            if length >= 20:
                indexed_docs = self.build_document(models)
                actions = list(map(lambda x: {'index': self.index_name, '_id': x['id'], '_source': x}, indexed_docs))
                res = bulk(self.es, actions, index=self.index_name + suffix, stats_only=False)
                models.clear()
        if models:
            indexed_docs = self.build_document(models)
            actions = list(map(lambda x: {'index': self.index_name, '_id': x['id'], '_source': x}, indexed_docs))
            res = bulk(self.es, actions, index=self.index_name + suffix, stats_only=False)
        return res

    def update(self, document_id, doc, changed_fields=None, **kwargs):
        """Update document in index."""
        if isinstance(changed_fields, dict):
            doc.reload()
            changed_fields = list(map(lambda x: x[5:] if x.startswith('set__') else x, changed_fields.keys()))
        updated_doc = self.build_document([doc], only_fields=changed_fields)[0]
        return self.es_helper.update_document(self.index_name, document_id, {'doc': updated_doc, 'doc_as_upsert': True}, **kwargs)

    def replace(self, document_id, document, **kwargs):
        """Replace document in index."""
        doc = self.build_document([document])[0]
        return self.es.index(index=self.index_name, body=doc, id=document_id, **kwargs)

    def remove(self, document_id, **kwargs):
        """Remove docs for resource."""
        return self.es_helper.delete_documents(self.index_name, document_id, **kwargs)

    def update_by_query(self, query_body, **kwargs):
        """Update document in index."""
        return self.es.update_by_query(index=self.index_name, body=query_body, **kwargs)
