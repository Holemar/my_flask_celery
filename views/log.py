# -*- coding: utf-8 -*-

import logging
from adam.views import ResourceView, Blueprint

bp = Blueprint(__name__)
logger = logging.getLogger(__name__)


class Log(ResourceView):
    """Log view.

    默认已经加上的请求地址：
 <Rule '/api/log' (GET, OPTIONS, HEAD) -> |collection_read|log|>,
 <Rule '/api/log' (OPTIONS, POST) -> |collection_create|log|>,
 <Rule '/api/log/count' (GET, OPTIONS, HEAD) -> |collection_count|log|>,
 <Rule '/api/log/import' (OPTIONS, POST) -> |collection_import|log|>,
 <Rule '/api/log/<id>' (GET, OPTIONS, HEAD) -> |item_read|log|>,
 <Rule '/api/log/<id>' (PUT, OPTIONS) -> |item_update|log|>,
 <Rule '/api/log/<id>' (OPTIONS, DELETE) -> |item_delete|log|>,
 <Rule '/api/log/batch' (PUT, OPTIONS) -> |batch_update|log|>,
 <Rule '/api/log/batch' (OPTIONS, DELETE) -> |batch_delete|log|>,
    """
