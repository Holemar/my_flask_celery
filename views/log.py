# -*- coding: utf-8 -*-

import logging
from utils.views import ResourceView, Blueprint

bp = Blueprint(__name__)
logger = logging.getLogger(__name__)


class Log(ResourceView):
    """Log view."""

    def test(self):
        pass
