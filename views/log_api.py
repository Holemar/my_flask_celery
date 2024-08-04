# -*- coding: utf-8 -*-

import logging
from utils.views import ResourceView, Blueprint

bp = Blueprint(__name__)
logger = logging.getLogger(__name__)


class LogApi(ResourceView):
    """LogApi view."""

    def test(self):
        pass
