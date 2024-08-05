# -*- coding: utf-8 -*-

import logging
from utils.views import ResourceView, Blueprint

bp = Blueprint(__name__)
logger = logging.getLogger(__name__)


class LogApi(ResourceView):
    """LogApi view.

    默认已经加上的请求地址：
 <Rule '/api/log_api' (GET, OPTIONS, HEAD) -> |collection_read|log_api|>,
 <Rule '/api/log_api' (OPTIONS, POST) -> |collection_create|log_api|>,
 <Rule '/api/log_api/count' (GET, OPTIONS, HEAD) -> |collection_count|log_api|>,
 <Rule '/api/log_api/import' (OPTIONS, POST) -> |collection_import|log_api|>,
 <Rule '/api/log_api/<id>' (GET, OPTIONS, HEAD) -> |item_read|log_api|>,
 <Rule '/api/log_api/<id>' (PUT, OPTIONS) -> |item_update|log_api|>,
 <Rule '/api/log_api/<id>' (OPTIONS, DELETE) -> |item_delete|log_api|>,
 <Rule '/api/log_api/batch' (PUT, OPTIONS) -> |batch_update|log_api|>,
 <Rule '/api/log_api/batch' (OPTIONS, DELETE) -> |batch_delete|log_api|>,
    """
