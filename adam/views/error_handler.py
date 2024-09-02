# -*- coding:utf-8 -*-
import logging
from flask import current_app
from .blueprint import return_data

logger = logging.getLogger(__name__)


@current_app.errorhandler(404)
def page_not_found(e):
    return return_data(code=404, message=str(e))


@current_app.errorhandler(500)
def internal_server_error(e):
    return return_data(code=500, message=str(e))
