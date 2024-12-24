# -*- coding:utf-8 -*-
"""
Elasticsearch Utility
"""
import logging
from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import ApiError, NotFoundError

logger = logging.getLogger(__name__)


class ElasticsearchHelper:
    def __init__(self, hosts="http://localhost:9200/", http_auth=None, timeout=10):
        """
        初始化Elasticsearch连接

        :param hosts: Elasticsearch主机地址，格式如 "http://localhost:9200/"
        :param http_auth: 认证信息，格式如('username', 'password')
        :param timeout: 连接超时时间，默认10秒
        """
        self.es = Elasticsearch(hosts=hosts, http_auth=http_auth, timeout=timeout)
        logger.debug(f"创建Elasticsearch连接成功: {self.es.info()}")

    def create_index(self, index_name, body=None, **kwargs):
        """
        创建索引

        :param index_name: 索引名称
        :param body: 映射配置
        :return: 创建结果
        """
        try:
            if not self.es.indices.exists(index=index_name):
                self.es.indices.create(index=index_name, body=body, **kwargs)
                logger.debug(f"索引 {index_name} 创建成功")
            else:
                logger.debug(f"索引 {index_name} 已经存在")
        except ApiError as e:
            logger.exception(f"创建索引 {index_name} 时出错: {e}")
            return False
        return True

    def delete_index(self, index_name, **kwargs):
        """
        删除索引

        :param index_name: 索引名称
        :return: 删除结果
        """
        try:
            if self.es.indices.exists(index=index_name):
                self.es.indices.delete(index=index_name, **kwargs)
                logger.debug(f"索引 {index_name} 删除成功")
            else:
                logger.debug(f"索引 {index_name} 不存在")
        except ApiError as e:
            logger.exception(f"删除索引 {index_name} 时出错: {e}")
            return False
        return True

    def clean_index(self, index_name, **kwargs):
        """
        清空索引中的所有文档

        :param index_name: 索引名称
        :return: 清空结果
        """
        if not self.es.indices.exists(index=index_name):
            logger.warning(f"索引 {index_name} 不存在，无法清空")
            return False
        try:
            self.es.delete_by_query(index=index_name, body={"query": {"match_all": {}}}, **kwargs)
            logger.debug(f"索引 {index_name} 中的所有文档已清空")
        except ApiError as e:
            logger.error(f"清空索引 {index_name} 时出错: {e}")
            return False
        return True

    def insert_document(self, index_name, document, document_id=None, **kwargs):
        """
        插入文档(插入单条数据)

        :param index_name: 索引名称
        :param document: 文档内容
        :param document_id: 文档ID，如果不指定则自动生成
        :return: 插入结果id
        """
        try:
            if document_id is not None:
                document_id = str(document_id)
            res = self.es.index(index=index_name, body=document, id=document_id, **kwargs)
            logger.debug(f"文档插入成功，_id: {res['_id']}, 结果: {res}")
            return res['_id']
        except ApiError as e:
            logger.exception(f"插入文档时出错: {e}, id: {document_id}, body: {document}")
            return False

    # todo: 批量插入，未能成功
    def bulk_insert(self, index_name, docs):
        """
        批量插入文档
        """
        actions = [
            {
                "_index": index_name,
                "_source": doc
            }
            for doc in docs
        ]
        try:
            info_list = []
            for doc in docs:
                info_list.append({"index": {}})
                info_list.append(doc)
            res = self.es.bulk(body=actions)
            logger.info(f"批量插入成功，总共插入 {res} 个文档")
        except Exception as e:
            logger.exception(f"批量插入时出错: {e}")
            return False
        return True

    def get_document(self, index_name, document_id, **kwargs):
        """
        获取文档

        :param index_name: 索引名称
        :param document_id: 文档ID
        :return: 文档内容
        """
        try:
            res = self.es.get(index=index_name, id=str(document_id), **kwargs)
            logger.debug(f"文档插入成功，_id: {res['_id']}, 结果: {res}")
            return res['_source']
        except NotFoundError as e:
            logger.debug(f"文档 {document_id} 不存在")
            return {}
        except ApiError as e:
            logger.exception(f"获取文档时出错: {e}, document_id: {document_id}")
            return {}

    def search_documents(self, index_name, query_body, **kwargs):
        """
        搜索文档

        :param index_name: 索引名称
        :param query_body: 查询体
        :return: 搜索结果
        """
        try:
            res = self.es.search(index=index_name, body=query_body, **kwargs)
            return res
        except ApiError as e:
            logger.exception(f"搜索文档时出错: {e}, query_body: {query_body}")
            return {}

    def delete_documents(self, index_name, document_id, **kwargs):
        """
        根据查询条件删除文档

        :param index_name: 索引名称
        :param document_id: 文档ID
        :return: 删除结果
        """
        try:
            res = self.es.delete(index=index_name, id=str(document_id), **kwargs)
            logger.debug(f"删除了文档 {document_id}")
        except ApiError as e:
            logger.exception(f"删除文档时出错: {e}, document_id: {document_id}")
            return False
        return True

    def delete_documents_by_query(self, index_name, query_body):
        """
        根据查询条件删除文档

        :param index_name: 索引名称
        :param query_body: 查询体
        :return: 删除结果
        """
        try:
            res = self.es.delete_by_query(index=index_name, body=query_body)
            logger.debug(f"删除了 {res['deleted']} 个文档")
        except ApiError as e:
            logger.exception(f"删除文档时出错: {e}, query_body: {query_body}")
            return False
        return True

    def update_document(self, index_name, document_id, update_body, **kwargs):
        """
        更新文档

        :param index_name: 索引名称
        :param document_id: 文档ID
        :param update_body: 更新体，使用script进行更新
        :return: 更新结果
        """
        try:
            res = self.es.update(index=index_name, id=str(document_id), body=update_body, **kwargs)
            logger.debug(f"文档更新成功，_version: {res['_version']}")
        except ApiError as e:
            logger.exception(f"更新文档时出错: {e}, document_id: {document_id}, update_body: {update_body}")
            return False
        return True

    def __del__(self):
        self.close()

    def close(self):
        if self.es is not None:
            try:
                self.es.close()
            except Exception as e:
                pass
            finally:
                self.es = None

